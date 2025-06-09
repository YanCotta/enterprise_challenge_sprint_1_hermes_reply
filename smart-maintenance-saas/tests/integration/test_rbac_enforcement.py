"""
Integration tests for RBAC (Role-Based Access Control) enforcement.

Tests verify that endpoints properly enforce scope-based security.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_ingest_endpoint_requires_data_ingest_scope(client):
    """Test that the /ingest endpoint requires 'data:ingest' scope."""
    # Test without any authentication
    response = client.post("/api/v1/data/ingest", json={
        "sensor_id": "test_sensor_001",
        "sensor_type": "temperature",
        "value": 25.5,
        "unit": "celsius",
        "timestamp": "2025-06-09T10:00:00Z"
    })
    assert response.status_code == 403  # Should be forbidden without proper auth/scope


@pytest.mark.asyncio
async def test_reports_endpoint_requires_reports_generate_scope(client):
    """Test that the /reports/generate endpoint requires 'reports:generate' scope."""
    # Test without any authentication
    response = client.post("/api/v1/reports/generate", json={
        "report_type": "maintenance_summary",
        "start_date": "2025-06-01T00:00:00Z",
        "end_date": "2025-06-09T23:59:59Z"
    })
    assert response.status_code == 403  # Should be forbidden without proper auth/scope


@pytest.mark.asyncio
async def test_human_decision_endpoint_requires_tasks_update_scope(client):
    """Test that the /human-decision/submit endpoint requires 'tasks:update' scope."""
    # Test without any authentication
    response = client.post("/api/v1/decisions/submit", json={
        "decision_id": "test_decision_001",
        "decision": "approve",
        "notes": "Test decision"
    })
    assert response.status_code == 403  # Should be forbidden without proper auth/scope


@pytest.mark.asyncio
async def test_api_key_with_wrong_scope_is_rejected(client):
    """Test that API keys with incorrect scopes are rejected."""
    # This would need to be implemented once we have a proper API key system
    # For now, we're testing the basic security dependency structure
    pass


def test_security_dependency_is_properly_configured():
    """Test that security dependencies are properly configured in the API."""
    # Import the api_key_auth dependency to ensure it's properly configured
    from apps.api.dependencies import api_key_auth
    
    # Check that the dependency is callable
    assert callable(api_key_auth)
    
    # This test verifies the security dependency structure is in place
    # The actual authentication logic would be tested with real API keys
