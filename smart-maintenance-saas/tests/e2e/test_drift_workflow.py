"""E2E test for Day 13 drift detection workflow (/check_drift endpoint).

Seeds baseline and recent sensor readings for a sensor, then calls the
`/api/v1/ml/check_drift` endpoint to verify response structure and status.
The goal is to ensure endpoint wiring, dependency overrides, and basic
statistical evaluation path function end-to-end.
"""

from datetime import datetime, timedelta
import random

import pytest
from httpx import AsyncClient

from apps.api.main import app
from core.database.session import get_async_db
from core.database.crud.crud_sensor_reading import crud_sensor_reading
from data.schemas import SensorReadingCreate, SensorType


pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


@pytest.fixture
def drift_test_sensor_id():
    return "drift_sensor_001"


async def seed_drift_data(db_session, sensor_id: str, window_minutes: int = 30):
    """Seed baseline and recent readings for drift testing.

    Baseline window: (now - 2*window) .. (now - window)
    Recent window:   (now - window) .. now
    Baseline distribution centered at 50, recent at 70 to likely induce drift.
    """
    now = datetime.utcnow()
    baseline_start = now - timedelta(minutes=2 * window_minutes)
    recent_start = now - timedelta(minutes=window_minutes)

    # Helper to create readings
    async def create_reading(ts: datetime, value: float):
        reading = SensorReadingCreate(
            sensor_id=sensor_id,
            value=value,
            timestamp=ts,
            sensor_type=SensorType.TEMPERATURE,
            unit="C",
            quality=1.0,
            metadata={}
        )
        await crud_sensor_reading.create_sensor_reading(db_session, obj_in=reading)

    # Baseline readings (50 +/- small noise)
    for i in range(40):
        ts = baseline_start + timedelta(seconds=i * (window_minutes * 60) / 40)
        val = 50 + random.uniform(-1.0, 1.0)
        await create_reading(ts, val)

    # Recent readings (70 +/- small noise)
    for i in range(40):
        ts = recent_start + timedelta(seconds=i * (window_minutes * 60) / 40)
        val = 70 + random.uniform(-1.0, 1.0)
        await create_reading(ts, val)


async def test_drift_check_endpoint(db_session, drift_test_sensor_id):
    """End-to-end test for /check_drift endpoint structure and success response."""

    # Override DB dependency to use test session
    async def override_get_async_db():  # pragma: no cover - override wiring
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_async_db

    # Seed data
    await seed_drift_data(db_session, drift_test_sensor_id, window_minutes=30)

    # Use AsyncClient to call endpoint
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "sensor_id": drift_test_sensor_id,
            "window_minutes": 30,
            "p_value_threshold": 0.05,
            "min_samples": 30,
        }
        response = await client.post("/api/v1/ml/check_drift", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()

    # Basic structure assertions
    for field in [
        "sensor_id", "recent_count", "baseline_count", "window_minutes",
        "p_value_threshold", "drift_detected", "request_id", "evaluated_at"
    ]:
        assert field in data, f"Missing field '{field}' in response: {data}"

    assert data["sensor_id"] == drift_test_sensor_id
    assert data["recent_count"] >= 30
    assert data["baseline_count"] >= 30
    assert data["window_minutes"] == 30
    # If stats were computed, ks_statistic & p_value should not be None
    if not data.get("insufficient_data"):
        assert data["ks_statistic"] is not None
        assert data["p_value"] is not None

    # Cleanup override
    app.dependency_overrides.pop(get_async_db, None)
