from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.config import Settings, get_settings
from app.database import build_engine, build_session_factory, initialise_database, session_dependency
from app.models import Recommendation, SyncRun
from app.services.analytics import (
    category_totals,
    dashboard_summary,
    grouped_spend,
    recommendation_rows,
    trend,
)
from app.services.demo_data import seed_demo_ledger
from app.services.optimizer import regenerate_recommendations
from app.services.sync import run_live_sync

API_REQUESTS = Counter("cloudcost_api_requests_total", "API requests served", ["route", "method"])
OPEN_RECOMMENDATIONS = Gauge("cloudcost_open_recommendations", "Open cost recommendations")
POTENTIAL_SAVINGS = Gauge("cloudcost_potential_monthly_savings_usd", "Potential monthly savings in USD")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialise_database(application.state.engine)
        with application.state.session_factory() as session:
            if settings.demo_mode:
                seed_demo_ledger(session)
            if not session.scalar(select(Recommendation.id).limit(1)):
                regenerate_recommendations(session)
        yield

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = build_engine(settings.database_url)
    app.state.session_factory = build_session_factory(app.state.engine)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health() -> dict:
        API_REQUESTS.labels(route="health", method="GET").inc()
        return {"status": "ok", "service": "cloudcost-api", "demo_mode": settings.demo_mode}

    @app.get("/metrics")
    def metrics(session: Session = Depends(session_dependency)) -> Response:
        summary = dashboard_summary(session)
        OPEN_RECOMMENDATIONS.set(summary["open_recommendations"])
        POTENTIAL_SAVINGS.set(summary["potential_monthly_savings"])
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/v1/dashboard")
    def dashboard(session: Session = Depends(session_dependency)) -> dict:
        API_REQUESTS.labels(route="dashboard", method="GET").inc()
        summary = dashboard_summary(session)
        return {
            "summary": summary,
            "trend": trend(session),
            "by_provider": grouped_spend(session, "provider"),
            "by_service": grouped_spend(session, "service"),
            "savings_by_category": category_totals(session),
            "sync_status": [
                {
                    "provider": run.provider,
                    "status": run.status,
                    "records_imported": run.records_imported,
                    "source": run.source,
                    "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                }
                for run in session.scalars(select(SyncRun).order_by(SyncRun.id.desc()).limit(5))
            ],
        }

    @app.get("/api/v1/recommendations")
    def recommendations(status: str | None = None, session: Session = Depends(session_dependency)) -> dict:
        API_REQUESTS.labels(route="recommendations", method="GET").inc()
        return {"items": recommendation_rows(session, status)}

    @app.patch("/api/v1/recommendations/{recommendation_id}")
    def update_recommendation(
        recommendation_id: int, payload: dict, session: Session = Depends(session_dependency)
    ) -> dict:
        status = payload.get("status")
        if status not in {"open", "in_review", "accepted", "dismissed"}:
            raise HTTPException(status_code=422, detail="status must be open, in_review, accepted, or dismissed")
        recommendation = session.get(Recommendation, recommendation_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        recommendation.status = status
        session.commit()
        return {"id": recommendation.id, "status": recommendation.status}

    @app.post("/api/v1/demo/reset")
    def reset_demo(session: Session = Depends(session_dependency)) -> dict:
        if not settings.demo_mode:
            raise HTTPException(status_code=409, detail="Demo reset is only available when DEMO_MODE=true")
        from sqlalchemy import delete
        from app.models import SpendRecord

        session.execute(delete(Recommendation))
        session.execute(delete(SpendRecord))
        session.commit()
        records = seed_demo_ledger(session)
        recommendations_created = regenerate_recommendations(session)
        return {"records_seeded": records, "recommendations_created": recommendations_created}

    @app.post("/api/v1/sync/{provider}")
    def sync_provider(provider: str, request: Request, session: Session = Depends(session_dependency)) -> dict:
        if provider not in {"aws", "azure"}:
            raise HTTPException(status_code=404, detail="Provider must be aws or azure")
        try:
            return run_live_sync(
                session,
                request.app.state.settings,
                provider,
                date.today() - timedelta(days=30),
                date.today(),
            )
        except Exception as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return app


app = create_app()
