from datetime import datetime

from sqlalchemy.orm import Session

from app.adapters import AwsCostExplorerAdapter, AzureCostManagementAdapter, ProviderNotConfigured
from app.adapters.base import ImportedCost
from app.config import Settings
from app.models import SpendRecord, SyncRun
from app.services.optimizer import regenerate_recommendations


def persist_imported_costs(session: Session, costs: list[ImportedCost], source: str) -> int:
    records = [
        SpendRecord(
            provider=cost.provider,
            account_scope=cost.account_scope,
            service_name=cost.service_name,
            resource_id=cost.resource_id,
            resource_name=cost.resource_name,
            region=cost.region,
            cost_date=cost.cost_date,
            currency=cost.currency,
            amortized_cost=cost.amortized_cost,
            tags=cost.tags or {},
            source=source,
        )
        for cost in costs
    ]
    session.add_all(records)
    session.commit()
    return len(records)


def run_live_sync(session: Session, settings: Settings, provider: str, start, end) -> dict:
    if not settings.allow_live_sync:
        raise ProviderNotConfigured("Live synchronization is disabled. Set ALLOW_LIVE_SYNC=true after configuring read-only credentials.")
    adapter = AwsCostExplorerAdapter(settings) if provider == "aws" else AzureCostManagementAdapter(settings)
    sync_run = SyncRun(provider=provider, status="running", source="live")
    session.add(sync_run)
    session.commit()
    try:
        costs = adapter.fetch_daily_costs(start, end)
        sync_run.records_imported = persist_imported_costs(session, costs, source="live")
        sync_run.status = "succeeded"
        regenerate_recommendations(session)
    except Exception as error:
        sync_run.status = "failed"
        sync_run.error_message = str(error)
        raise
    finally:
        sync_run.finished_at = datetime.utcnow()
        session.add(sync_run)
        session.commit()
    return {"run_id": sync_run.id, "records_imported": sync_run.records_imported, "status": sync_run.status}
