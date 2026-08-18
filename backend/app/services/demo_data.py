from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import SpendRecord


DEMO_SERVICES = [
    {
        "provider": "aws",
        "account_scope": "engineering-prod",
        "service_name": "Amazon EC2",
        "resource_id": "i-demo-cpu-01",
        "resource_name": "api-worker-01",
        "region": "us-east-1",
        "base_cost": 128.5,
        "tags": {"environment": "production", "avg_cpu_percent": 8, "instance_family": "m5.2xlarge"},
    },
    {
        "provider": "aws",
        "account_scope": "engineering-prod",
        "service_name": "Amazon RDS",
        "resource_id": "db-demo-analytics-01",
        "resource_name": "analytics-postgres",
        "region": "us-east-1",
        "base_cost": 49.8,
        "tags": {"environment": "production", "avg_connections": 6, "instance_family": "db.r5.large"},
    },
    {
        "provider": "aws",
        "account_scope": "engineering-prod",
        "service_name": "Amazon EBS",
        "resource_id": "vol-demo-orphan-01",
        "resource_name": "orphaned-analytics-volume",
        "region": "us-east-1",
        "base_cost": 13.2,
        "tags": {"attached": False, "size_gib": 600, "environment": "production"},
    },
    {
        "provider": "aws",
        "account_scope": "engineering-prod",
        "service_name": "AWS Data Transfer",
        "resource_id": "nat-demo-01",
        "resource_name": "public-nat-gateway",
        "region": "us-east-1",
        "base_cost": 25.7,
        "tags": {"environment": "production", "traffic_pattern": "cross-az"},
    },
    {
        "provider": "azure",
        "account_scope": "subscription-demo-finops",
        "service_name": "Virtual Machines",
        "resource_id": "/subscriptions/demo/resourceGroups/platform/providers/Microsoft.Compute/virtualMachines/reporting-vm",
        "resource_name": "reporting-vm",
        "region": "eastus",
        "base_cost": 91.4,
        "tags": {"environment": "production", "avg_cpu_percent": 11, "sku": "Standard_D8s_v5"},
    },
    {
        "provider": "azure",
        "account_scope": "subscription-demo-finops",
        "service_name": "Managed Disks",
        "resource_id": "/subscriptions/demo/resourceGroups/platform/providers/Microsoft.Compute/disks/retired-app-disk",
        "resource_name": "retired-app-disk",
        "region": "eastus",
        "base_cost": 14.6,
        "tags": {"attached": False, "size_gib": 512, "environment": "production"},
    },
    {
        "provider": "azure",
        "account_scope": "subscription-demo-finops",
        "service_name": "Azure SQL Database",
        "resource_id": "/subscriptions/demo/resourceGroups/data/providers/Microsoft.Sql/servers/analytics/databases/warehouse",
        "resource_name": "analytics-warehouse",
        "region": "eastus",
        "base_cost": 45.9,
        "tags": {"environment": "production", "avg_dtu_percent": 13, "sku": "GP_Gen5_8"},
    },
    {
        "provider": "azure",
        "account_scope": "subscription-demo-finops",
        "service_name": "Bandwidth",
        "resource_id": "network-demo-egress-01",
        "resource_name": "inter-region-egress",
        "region": "eastus",
        "base_cost": 17.1,
        "tags": {"environment": "production", "traffic_pattern": "inter-region"},
    },
]


def seed_demo_ledger(session: Session, days: int = 60) -> int:
    existing = session.scalar(select(func.count()).select_from(SpendRecord))
    if existing:
        return 0

    today = date.today()
    records: list[SpendRecord] = []
    for offset in range(days - 1, -1, -1):
        cost_date = today - timedelta(days=offset)
        weekly_factor = [0.97, 1.01, 1.03, 0.99, 1.05, 0.94, 0.91][cost_date.weekday()]
        month_factor = 1 + ((days - offset) / days) * 0.08
        for service in DEMO_SERVICES:
            records.append(
                SpendRecord(
                    **{key: value for key, value in service.items() if key != "base_cost"},
                    cost_date=cost_date,
                    currency="USD",
                    amortized_cost=round(service["base_cost"] * weekly_factor * month_factor, 2),
                    source="demo",
                )
            )
    session.add_all(records)
    session.commit()
    return len(records)
