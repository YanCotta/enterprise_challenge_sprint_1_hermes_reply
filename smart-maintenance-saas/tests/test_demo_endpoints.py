"""Tests for the Golden Path demo endpoints.

These tests focus on:
1. Starting the demo and validating response shape.
2. Polling status until completion (with timeout) asserting step + metric fields.

They intentionally mock out heavy dependencies (Redis + coordinator) minimally where needed.
"""

import time
import uuid
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

# NOTE: These tests assume app.state.coordinator and redis client are initialized
# in the FastAPI startup events. If that is not the case in the test context,
# we can inject lightweight stubs.


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_start_demo_endpoint(client):
    response = client.post("/api/v1/demo/golden-path", params={"sensor_events": 8})
    assert response.status_code == 200
    data = response.json()
    assert "correlation_id" in data
    assert "status_url" in data
    assert data["status"] == "started"
    uuid.UUID(data["correlation_id"])  # validates format


def test_demo_status_progression(client):
    # Start
    start_resp = client.post("/api/v1/demo/golden-path", params={"sensor_events": 10})
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    cid = start_data["correlation_id"]

    # Poll until complete or timeout
    status_url = f"/api/v1/demo/golden-path/status/{cid}"
    deadline = time.time() + 25  # generous timeout
    last_payload: Dict[str, Any] = {}
    while time.time() < deadline:
        r = client.get(status_url)
        assert r.status_code == 200
        last_payload = r.json()
        assert last_payload.get("correlation_id") == cid
        assert "steps" in last_payload
        assert "metrics" in last_payload
        # basic shape checks
        for step in last_payload["steps"]:
            assert set(step.keys()) >= {"name", "status", "events"}
        if last_payload.get("status") in ("complete", "failed"):
            break
        time.sleep(0.75)

    assert last_payload, "No status payload retrieved."\

    # Final assertions
    assert last_payload.get("status") in ("complete", "failed"), "Pipeline did not finish in time"
    steps_index = {s["name"]: s for s in last_payload["steps"]}
    # Ensure ingestion / prediction at least progressed
    assert steps_index.get("ingestion"), "Ingestion step missing"
    assert steps_index.get("prediction"), "Prediction step missing"
    # Metrics sanity
    metrics = last_payload.get("metrics", {})
    assert "total_events" in metrics
    # If pipeline completed successfully, latency metric should exist
    if last_payload.get("status") == "complete":
        assert metrics.get("latency_ms_ingest_to_prediction") is not None
