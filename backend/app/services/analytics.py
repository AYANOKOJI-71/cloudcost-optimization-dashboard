from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Recommendation, SpendRecord


def trend(session: Session, days: int = 30) -> list[dict]:
    start = date.today() - timedelta(days=days - 1)
    rows = session.execute(
        select(SpendRecord.cost_date, func.sum(SpendRecord.amortized_cost))
        .where(SpendRecord.cost_date >= start)
        .group_by(SpendRecord.cost_date)
        .order_by(SpendRecord.cost_date)
    ).all()
    return [{"date": record_date.isoformat(), "cost": round(float(cost), 2)} for record_date, cost in rows]


def grouped_spend(session: Session, dimension: str) -> list[dict]:
    column = SpendRecord.provider if dimension == "provider" else SpendRecord.service_name
    rows = session.execute(
        select(column, func.sum(SpendRecord.amortized_cost))
        .group_by(column)
        .order_by(func.sum(SpendRecord.amortized_cost).desc())
    ).all()
    return [{"name": name, "cost": round(float(cost), 2)} for name, cost in rows]


def dashboard_summary(session: Session) -> dict:
    today = date.today()
    start_current = today.replace(day=1)
    previous_end = start_current - timedelta(days=1)
    previous_start = previous_end.replace(day=1)
    current_spend = session.scalar(
        select(func.coalesce(func.sum(SpendRecord.amortized_cost), 0)).where(
            SpendRecord.cost_date >= start_current
        )
    )
    previous_spend = session.scalar(
        select(func.coalesce(func.sum(SpendRecord.amortized_cost), 0)).where(
            SpendRecord.cost_date.between(previous_start, previous_end)
        )
    )
    days_elapsed = max((today - start_current).days + 1, 1)
    forecast = float(current_spend) / days_elapsed * 30
    open_recommendations = session.scalar(
        select(func.count()).select_from(Recommendation).where(Recommendation.status == "open")
    )
    savings = session.scalar(
        select(func.coalesce(func.sum(Recommendation.monthly_savings), 0)).where(
            Recommendation.status == "open"
        )
    )
    current = float(current_spend)
    previous = float(previous_spend)
    change = ((current - previous) / previous * 100) if previous else 0
    return {
        "month_to_date_cost": round(current, 2),
        "forecast_cost": round(forecast, 2),
        "month_over_month_change": round(change, 1),
        "open_recommendations": int(open_recommendations),
        "potential_monthly_savings": round(float(savings), 2),
        "currency": "USD",
        "data_mode": "demo" if session.scalar(select(func.count()).select_from(SpendRecord).where(SpendRecord.source == "demo")) else "live",
    }


def recommendation_rows(session: Session, status: str | None = None) -> list[dict]:
    statement = select(Recommendation).order_by(Recommendation.monthly_savings.desc())
    if status:
        statement = statement.where(Recommendation.status == status)
    recommendations = session.scalars(statement).all()
    return [
        {
            "id": recommendation.id,
            "provider": recommendation.provider,
            "account_scope": recommendation.account_scope,
            "category": recommendation.category,
            "title": recommendation.title,
            "rationale": recommendation.rationale,
            "resource_name": recommendation.resource_name,
            "monthly_savings": round(recommendation.monthly_savings, 2),
            "confidence": recommendation.confidence,
            "status": recommendation.status,
            "evidence": recommendation.evidence,
        }
        for recommendation in recommendations
    ]


def category_totals(session: Session) -> list[dict]:
    totals: defaultdict[str, float] = defaultdict(float)
    for item in session.scalars(select(Recommendation).where(Recommendation.status == "open")):
        totals[item.category] += item.monthly_savings
    return [
        {"category": category, "monthly_savings": round(savings, 2)}
        for category, savings in sorted(totals.items(), key=lambda row: row[1], reverse=True)
    ]
