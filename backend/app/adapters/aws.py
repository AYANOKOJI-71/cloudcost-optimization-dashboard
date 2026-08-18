from datetime import date

from app.adapters.base import ImportedCost, ProviderNotConfigured
from app.config import Settings


class AwsCostExplorerAdapter:
    provider_name = "aws"

    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch_daily_costs(self, start: date, end: date) -> list[ImportedCost]:
        if not self.settings.aws_cost_explorer_enabled:
            raise ProviderNotConfigured("AWS Cost Explorer is disabled. Set AWS_COST_EXPLORER_ENABLED=true.")

        import boto3

        if self.settings.aws_cost_explorer_role_arn:
            assumed = boto3.client("sts").assume_role(
                RoleArn=self.settings.aws_cost_explorer_role_arn,
                RoleSessionName="cloudcost-readonly",
            )["Credentials"]
            client = boto3.client(
                "ce",
                region_name=self.settings.aws_region,
                aws_access_key_id=assumed["AccessKeyId"],
                aws_secret_access_key=assumed["SecretAccessKey"],
                aws_session_token=assumed["SessionToken"],
            )
        else:
            client = boto3.client("ce", region_name=self.settings.aws_region)
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="DAILY",
            Metrics=["AmortizedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        records: list[ImportedCost] = []
        for bucket in response.get("ResultsByTime", []):
            for group in bucket.get("Groups", []):
                amount = float(group["Metrics"]["AmortizedCost"]["Amount"])
                records.append(
                    ImportedCost(
                        provider="aws",
                        account_scope="linked-account",
                        service_name=group["Keys"][0],
                        cost_date=date.fromisoformat(bucket["TimePeriod"]["Start"]),
                        amortized_cost=amount,
                        currency=group["Metrics"]["AmortizedCost"].get("Unit", "USD"),
                    )
                )
        return records
