from __future__ import annotations

from fastapi.testclient import TestClient

from riskpulse.api.app import create_app
from riskpulse.services.factory import get_repository


def test_health_and_openapi() -> None:
    client = TestClient(create_app())
    assert client.get("/healthz").json()["status"] == "ok"
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "RiskPulse API"


def test_manual_analyze_and_list() -> None:
    repository = get_repository()
    repository.clear_runtime()
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/analyze",
        json={
            "source_record_id": "api-test-1",
            "text": "Nova Bank downgraded after default and missed payment",
        },
    )
    assert response.status_code == 201
    signal = response.json()[0]
    assert signal["event"]["label"] == "credit_event"
    assert signal["impact"]["score"] > 7
    listing = client.get("/api/v1/signals?min_impact=7").json()
    assert listing["total"] == 1
    assert client.get(f"/api/v1/signals/{signal['signal_id']}").status_code == 200


def test_replay_stress_portfolio_and_metrics_endpoints() -> None:
    repository = get_repository()
    repository.clear_runtime()
    client = TestClient(create_app())

    assert client.get("/readyz").json()["status"] == "ready"
    assert client.post("/api/v1/replays", json={"fixture": "../README.md"}).status_code == 400

    replay = client.post("/api/v1/replays", json={"fixture": "data/demo/mixed_source_events.jsonl"})
    assert replay.status_code == 200
    assert replay.json()["stress_runs"] == 4

    runs = client.get("/api/v1/stress-tests?limit=10").json()
    assert len(runs) == 4
    run = runs[0]
    assert client.get(f"/api/v1/stress-tests/{run['stress_run_id']}").status_code == 200
    repeated = client.post("/api/v1/stress-tests", json={"signal_id": run["signal_id"]})
    assert repeated.status_code == 201
    assert repeated.json()["stress_run_id"] == run["stress_run_id"]

    portfolio = client.get("/api/v1/portfolio/summary").json()
    assert portfolio["position_count"] == 72
    assert set(portfolio["by_asset_type"]) == {"bond", "derivative", "loan"}
    metrics = client.get("/api/v1/metrics/summary").json()
    assert metrics["documents"] == 8
    assert metrics["stress_runs"] == 4

    assert client.get("/api/v1/signals/not-found").status_code == 404
    assert client.get("/api/v1/stress-tests/not-found").status_code == 404
    assert client.post("/api/v1/stress-tests", json={"signal_id": "not-found"}).status_code == 404


def test_duplicate_and_ineligible_manual_signal() -> None:
    repository = get_repository()
    repository.clear_runtime()
    client = TestClient(create_app())
    payload = {
        "source_record_id": "api-neutral-1",
        "text": "Orion Pharma schedules its annual community meeting",
    }
    first = client.post("/api/v1/analyze", json=payload)
    assert first.status_code == 201
    assert client.post("/api/v1/analyze", json=payload).status_code == 409
    response = client.post("/api/v1/stress-tests", json={"signal_id": first.json()[0]["signal_id"]})
    assert response.status_code == 422
