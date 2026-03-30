from datetime import datetime

from fastapi.testclient import TestClient

from mlops_forecasting.api.main import app


client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "model_loaded" in body


def test_ingest_endpoint_rejects_invalid_payload_shape():
    resp = client.post("/ingest/timeseries", json={"mode": "merge", "rows": [{"x": 1}]})
    assert resp.status_code == 422


def test_ingest_endpoint_accepts_valid_rows():
    payload = {
        "mode": "replace",
        "rows": [
            {"ds": datetime(2025, 1, 1).isoformat(), "y": 10.0},
            {"ds": datetime(2025, 1, 2).isoformat(), "y": 12.5},
        ],
    }
    resp = client.post("/ingest/timeseries", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["rows_received"] == 2
