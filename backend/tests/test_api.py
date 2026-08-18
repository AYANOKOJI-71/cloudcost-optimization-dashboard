from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def build_client(tmp_path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'test.db'}",
        demo_mode=True,
        allow_live_sync=False,
    )
    return TestClient(create_app(settings))


def test_health_and_dashboard_seed_demo_workspace(tmp_path):
    with build_client(tmp_path) as client:
        health = client.get("/health")
        dashboard = client.get("/api/v1/dashboard")

    assert health.status_code == 200
    assert health.json()["demo_mode"] is True
    assert dashboard.status_code == 200
    assert dashboard.json()["summary"]["data_mode"] == "demo"
    assert len(dashboard.json()["trend"]) == 30


def test_recommendations_and_status_transition(tmp_path):
    with build_client(tmp_path) as client:
        recommendations = client.get("/api/v1/recommendations")
        first = recommendations.json()["items"][0]
        updated = client.patch(f"/api/v1/recommendations/{first['id']}", json={"status": "in_review"})

    assert recommendations.status_code == 200
    assert first["monthly_savings"] > 0
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_review"


def test_live_sync_is_closed_by_default(tmp_path):
    with build_client(tmp_path) as client:
        response = client.post("/api/v1/sync/aws")

    assert response.status_code == 409
    assert "disabled" in response.json()["detail"]


def test_prometheus_metrics_endpoint(tmp_path):
    with build_client(tmp_path) as client:
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "cloudcost_open_recommendations" in response.text
