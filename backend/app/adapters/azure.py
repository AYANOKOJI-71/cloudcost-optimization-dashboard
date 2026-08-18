from datetime import date, datetime

import httpx

from app.adapters.base import ImportedCost, ProviderNotConfigured
from app.config import Settings


class AzureCostManagementAdapter:
    provider_name = "azure"

    def __init__(self, settings: Settings):
        self.settings = settings

    def _access_token(self) -> str:
        if not all(
            [
                self.settings.azure_tenant_id,
                self.settings.azure_client_id,
                self.settings.azure_client_secret,
            ]
        ):
            raise ProviderNotConfigured("Azure service-principal environment variables are incomplete.")
        token_response = httpx.post(
            f"https://login.microsoftonline.com/{self.settings.azure_tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": self.settings.azure_client_id,
                "client_secret": self.settings.azure_client_secret,
                "grant_type": "client_credentials",
                "scope": "https://management.azure.com/.default",
            },
            timeout=20,
        )
        token_response.raise_for_status()
        return token_response.json()["access_token"]

    def fetch_daily_costs(self, start: date, end: date) -> list[ImportedCost]:
        if not self.settings.azure_cost_management_enabled:
            raise ProviderNotConfigured(
                "Azure Cost Management is disabled. Set AZURE_COST_MANAGEMENT_ENABLED=true."
            )
        if not self.settings.azure_subscription_id:
            raise ProviderNotConfigured("AZURE_SUBSCRIPTION_ID is required for Azure cost queries.")

        url = (
            f"https://management.azure.com/subscriptions/{self.settings.azure_subscription_id}"
            "/providers/Microsoft.CostManagement/query?api-version=2023-11-01"
        )
        payload = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": start.isoformat(), "to": end.isoformat()},
            "dataset": {
                "granularity": "Daily",
                "aggregation": {"cost": {"name": "PreTaxCost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": "ServiceName"}],
            },
        }
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {self._access_token()}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json().get("properties", {})
        columns = [column["name"] for column in data.get("columns", [])]
        rows = [dict(zip(columns, row, strict=True)) for row in data.get("rows", [])]
        def parse_cost_date(raw_date: object) -> date:
            value = str(raw_date)
            return datetime.strptime(value, "%Y%m%d").date() if value.isdigit() and len(value) == 8 else date.fromisoformat(value)

        return [
            ImportedCost(
                provider="azure",
                account_scope=self.settings.azure_subscription_id,
                service_name=str(row.get("ServiceName", "Uncategorized")),
                cost_date=parse_cost_date(row.get("UsageDate")),
                amortized_cost=float(row.get("PreTaxCost", 0)),
                currency=str(row.get("Currency", "USD")),
            )
            for row in rows
        ]
