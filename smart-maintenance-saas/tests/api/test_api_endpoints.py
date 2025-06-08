import pytest
import httpx
from fastapi import FastAPI
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID, uuid4
import datetime # Added for datetime.datetime.utcnow

from apps.api.main import app
from core.config.settings import settings
from core.events.event_models import SensorDataReceivedEvent
from data.schemas import ReportRequest, ReportResult # Added
from apps.system_coordinator import SystemCoordinator
from core.events.event_bus import EventBus
from apps.agents.decision.reporting_agent import ReportingAgent

# EventBus import for type hinting mock, if needed, but patch path is string-based
# from core.events.event_bus import EventBus


BASE_URL = "http://test"  # Base URL for the test client

# Setup mock coordinator for tests
@pytest.fixture(autouse=True)
async def setup_test_coordinator():
    """Setup a mock coordinator for all API tests."""
    mock_coordinator = MagicMock(spec=SystemCoordinator)
    mock_event_bus = MagicMock(spec=EventBus)
    mock_event_bus.publish = AsyncMock()
    mock_coordinator.event_bus = mock_event_bus
    
    mock_reporting_agent = MagicMock(spec=ReportingAgent)
    mock_reporting_agent.generate_report = AsyncMock()
    # Set a default return value for the reporting agent
    mock_reporting_agent.generate_report.return_value = ReportResult(
        report_id="test_report_123",
        report_type="test_report", 
        format="json",
        content="test content",
        generated_at=datetime.datetime.utcnow(),
        charts_encoded={},
        metadata={}
    )
    mock_coordinator.reporting_agent = mock_reporting_agent
    
    # Set the coordinator on app.state
    app.state.coordinator = mock_coordinator
    yield
    # Cleanup - remove coordinator after test
    if hasattr(app.state, 'coordinator'):
        delattr(app.state, 'coordinator')


# Unauthorized Access Tests
@pytest.mark.asyncio
async def test_unauthorized_ingest_data():
    """Test unauthorized access to the /api/v1/data/ingest endpoint."""
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post("/api/v1/data/ingest", json={})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


@pytest.mark.asyncio
async def test_unauthorized_generate_report():
    """Test unauthorized access to the /api/v1/reports/generate endpoint (now POST)."""
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        # Changed to POST and added json={}
        response = await client.post("/api/v1/reports/generate", json={})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


@pytest.mark.asyncio
async def test_unauthorized_submit_decision():
    """Test unauthorized access to the /api/v1/decisions/submit endpoint."""
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post("/api/v1/decisions/submit", json={})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


# Authorized Access Tests
@pytest.mark.asyncio
async def test_authorized_ingest_data_basic_check():
    """Test authorized access to /api/v1/data/ingest for basic success (status 200)."""
    headers = {"X-API-Key": settings.API_KEY}
    json_body = {
        "sensor_id": "sensor_auth_check_001",
        "value": 25.0,
        "timestamp": "2023-10-27T10:00:00Z",
        "metadata": {"temperature": 25.0, "humidity": 60.0}
    }
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post("/api/v1/data/ingest", headers=headers, json=json_body)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"


@pytest.mark.asyncio
async def test_authorized_generate_report_basic_check():
    """Test authorized access to /api/v1/reports/generate (now POST) for basic success."""
    headers = {"X-API-Key": settings.API_KEY}
    # Changed to POST and added a minimal valid ReportRequest body
    json_body = ReportRequest(
        report_type="basic_check_report",
        format="json",
        parameters={"detail_level": "summary"}
    ).model_dump()
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post("/api/v1/reports/generate", headers=headers, json=json_body)
    # Assuming the endpoint returns 200 on success if the agent call is not mocked
    # or if the agent itself returns a valid ReportResult.
    # This might need adjustment based on unmocked agent behavior or if it processes an error.
    # For now, let's keep 200. If it fails, it indicates an issue with the endpoint itself or unmocked agent.
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"


@pytest.mark.asyncio
async def test_authorized_submit_decision():
    """Test authorized access to the /api/v1/decisions/submit endpoint."""
    headers = {"X-API-Key": settings.API_KEY}
    json_body = {
        "request_id": "test_request_123", 
        "decision": "approved", 
        "operator_id": "test_operator",
        "justification": "Test decision"
    }
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post("/api/v1/decisions/submit", headers=headers, json=json_body)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.text}"


# Specific Endpoint Tests for /api/v1/data/ingest
@pytest.mark.asyncio
async def test_ingest_data_publishes_event():
    """Test that /api/v1/data/ingest correctly forms and publishes a SensorDataReceivedEvent."""
    headers = {"X-API-Key": settings.API_KEY}
    request_payload = {
        "sensor_id": "sensor_event_test_002", 
        "value": 1012.5,
        "timestamp": "2023-10-27T11:00:00Z",
        "metadata": {"pressure": 1012.5, "vibration": 0.05}
    }
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post("/api/v1/data/ingest", headers=headers, json=request_payload)

    assert response.status_code == 200
    # Check that the coordinator's event bus publish was called
    app.state.coordinator.event_bus.publish.assert_called_once()
    published_event = app.state.coordinator.event_bus.publish.call_args[0][0]
    assert isinstance(published_event, SensorDataReceivedEvent)
    assert published_event.raw_data["sensor_id"] == request_payload["sensor_id"]
    assert published_event.raw_data["value"] == request_payload["value"]
    assert "correlation_id" in published_event.raw_data
    assert published_event.sensor_id == request_payload["sensor_id"]
    try:
        UUID(published_event.correlation_id)
    except ValueError:
        pytest.fail(f"event.correlation_id ('{published_event.correlation_id}') is not a valid UUID string.")

# Specific Endpoint Tests for /api/v1/reports/generate
@pytest.mark.asyncio
async def test_generate_report_calls_agent_and_returns_result():
    """Test that /api/v1/reports/generate calls the reporting agent and returns its result."""
    headers = {"X-API-Key": settings.API_KEY}

    report_request_payload = ReportRequest(
        report_type="sample_report",
        format="json",
        parameters={"param1": "value1", "complex": {"nes": "ted"}}
    )

    sample_report_id = str(uuid4())
    sample_generated_at = datetime.datetime.utcnow()

    expected_report_result = ReportResult(
        report_id=sample_report_id,
        report_type=report_request_payload.report_type,
        format=report_request_payload.format,
        content="{'data': 'sample report content for test'}", # JSON string or actual dict
        generated_at=sample_generated_at,
        charts_encoded={"chart1_id": "base64data...."},
        metadata={"source": "test_mock"}
    )

    # Set the return value for this test
    app.state.coordinator.reporting_agent.generate_report.return_value = expected_report_result

    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(
            "/api/v1/reports/generate",
            headers=headers,
            json=report_request_payload.model_dump() # Send Pydantic model as dict
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"

    app.state.coordinator.reporting_agent.generate_report.assert_called_once()

    # Check the arguments passed to the mocked agent method
    call_args = app.state.coordinator.reporting_agent.generate_report.call_args
    assert call_args is not None
    passed_report_request_arg = call_args[0][0]

    assert isinstance(passed_report_request_arg, ReportRequest), \
        f"Agent was called with type {type(passed_report_request_arg)}, expected ReportRequest"

    assert passed_report_request_arg.report_type == report_request_payload.report_type
    assert passed_report_request_arg.format == report_request_payload.format
    assert passed_report_request_arg.parameters == report_request_payload.parameters

    # Check the response from the endpoint
    # Pydantic models in FastAPI response are automatically converted to JSON
    # expected_report_result.model_dump_json() will include proper ISO format for datetime
    assert response.json() == expected_report_result.model_dump(mode='json')
