from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Recommendation, SpendRecord


def _recommendation(
    record: SpendRecord,
    *,
    category: str,
    title: str,
    rationale: str,
    savings_multiplier: float,
    confidence: str,
    evidence: dict,
) -> Recommendation:
    return Recommendation(
        provider=record.provider,
        account_scope=record.account_scope,
        category=category,
        title=title,
        rationale=rationale,
        resource_id=record.resource_id,
        resource_name=record.resource_name,
        monthly_savings=round(record.amortized_cost * 30 * savings_multiplier, 2),
        confidence=confidence,
        status="open",
        evidence=evidence,
    )


def regenerate_recommendations(session: Session) -> int:
    session.execute(delete(Recommendation))
    latest_records = session.scalars(
        select(SpendRecord).order_by(SpendRecord.resource_id, SpendRecord.cost_date.desc())
    ).all()
    seen_resources: set[str] = set()
    recommendations: list[Recommendation] = []
    for record in latest_records:
        resource_key = record.resource_id or f"{record.provider}:{record.service_name}"
        if resource_key in seen_resources:
            continue
        seen_resources.add(resource_key)
        tags = record.tags or {}
        if tags.get("attached") is False:
            recommendations.append(
                _recommendation(
                    record,
                    category="idle_storage",
                    title=f"Remove unattached storage: {record.resource_name}",
                    rationale="The latest imported cost record is marked unattached. Validate the snapshot policy, then delete the orphaned volume or disk.",
                    savings_multiplier=1.0,
                    confidence="high",
                    evidence={"attached": False, "size_gib": tags.get("size_gib")},
                )
            )
        elif tags.get("avg_cpu_percent") is not None and float(tags["avg_cpu_percent"]) < 15:
            recommendations.append(
                _recommendation(
                    record,
                    category="rightsizing",
                    title=f"Rightsize underutilized compute: {record.resource_name}",
                    rationale="Observed average CPU is below the 15% review threshold. Validate peak load, memory, and commitments before selecting a smaller SKU.",
                    savings_multiplier=0.45,
                    confidence="medium",
                    evidence={"avg_cpu_percent": tags.get("avg_cpu_percent"), "review_threshold_percent": 15},
                )
            )
        elif tags.get("avg_dtu_percent") is not None and float(tags["avg_dtu_percent"]) < 20:
            recommendations.append(
                _recommendation(
                    record,
                    category="database_rightsizing",
                    title=f"Review database tier: {record.resource_name}",
                    rationale="The usage signal is below the 20% review threshold. Validate workload windows and availability requirements before reducing the tier.",
                    savings_multiplier=0.3,
                    confidence="medium",
                    evidence={"avg_dtu_percent": tags.get("avg_dtu_percent"), "review_threshold_percent": 20},
                )
            )
        elif tags.get("traffic_pattern") in {"cross-az", "inter-region"}:
            recommendations.append(
                _recommendation(
                    record,
                    category="network_egress",
                    title=f"Reduce cross-zone transfer: {record.resource_name}",
                    rationale="The record is tagged with a cross-zone or inter-region traffic pattern. Review service placement and private connectivity before changing network paths.",
                    savings_multiplier=0.25,
                    confidence="low",
                    evidence={"traffic_pattern": tags.get("traffic_pattern")},
                )
            )
    session.add_all(recommendations)
    session.commit()
    return len(recommendations)
