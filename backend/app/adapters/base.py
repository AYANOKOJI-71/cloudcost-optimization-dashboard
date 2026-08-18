from dataclasses import dataclass
from datetime import date
from typing import Protocol


class ProviderNotConfigured(RuntimeError):
    """Raised when a live provider adapter is invoked without approved configuration."""


@dataclass(frozen=True)
class ImportedCost:
    provider: str
    account_scope: str
    service_name: str
    cost_date: date
    amortized_cost: float
    currency: str = "USD"
    resource_id: str | None = None
    resource_name: str | None = None
    region: str | None = None
    tags: dict | None = None


class CostProvider(Protocol):
    provider_name: str

    def fetch_daily_costs(self, start: date, end: date) -> list[ImportedCost]: ...
