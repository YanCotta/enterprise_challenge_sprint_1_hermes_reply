import asyncio
import uuid
from unittest.mock import AsyncMock # Using unittest.mock for AsyncMock
from datetime import datetime # Added import

import pytest

# Assuming smart-maintenance-saas is the root for imports in tests
from apps.system_coordinator import SystemCoordinator
from core.events.event_models import SensorDataReceivedEvent, MaintenanceScheduledEvent
from data.schemas import SensorType # For creating realistic sensor data

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
async def coordinator():
    """Pytest fixture to set up and tear down the SystemCoordinator."""
    coord = SystemCoordinator()
    # Ensure all mock dependencies within SystemCoordinator are fully initialized
    # This might involve awaiting parts of its __init__ if it were async,
    # but currently, SystemCoordinator.__init__ is synchronous.
    # Startup system is critical.
    await coord.startup_system()
    yield coord
    await coord.shutdown_system()

async def test_full_workflow_from_ingestion_to_scheduling(coordinator: SystemCoordinator):
    """
    Tests the full workflow from sensor data ingestion to maintenance scheduling.
    """
    # Test setup is largely handled by the coordinator fixture.
    # Mock handler for MaintenanceScheduledEvent
    mock_maintenance_scheduled_handler = AsyncMock()

    # Subscribe the mock handler to the MaintenanceScheduledEvent
    # The event name for subscription should match how it's defined/published
    await coordinator.event_bus.subscribe(
        MaintenanceScheduledEvent.__name__,
        mock_maintenance_scheduled_handler
    )

    correlation_id = str(uuid.uuid4())

    # Step 1: Ingest - Create and publish a SensorDataReceivedEvent
    # This data should be designed to be anomalous to trigger the workflow.
    # The exact values might need tuning based on default mock agent logic.
    sensor_event_data = {
        "raw_data": {
            "sensor_id": "temp_sensor_e2e_001",
            "value": 105.0, # Anomalously high temperature
            "timestamp": datetime.utcnow().isoformat(), # Current time for relevance
            "sensor_type": SensorType.TEMPERATURE.value, # Explicitly set sensor_type
            "unit": "C"
        },
        "source_topic": "test/topic/e2e",
        "sensor_id": "temp_sensor_e2e_001", # Repeating sensor_id here as per SensorDataReceivedEvent schema
        "correlation_id": correlation_id
    }
    sensor_event = SensorDataReceivedEvent(**sensor_event_data)

    await coordinator.event_bus.publish(sensor_event)

    # Step 2: Wait for processing
    # Wait for the event to be processed
    await asyncio.wait_for(event_processed.wait(), timeout=10)

    # Step 3: Assert
    # Verify that the mock handler for MaintenanceScheduledEvent was called
    mock_maintenance_scheduled_handler.assert_called_once()

    # Check the details of the received MaintenanceScheduledEvent
    assert mock_maintenance_scheduled_handler.call_count == 1
    received_event_args = mock_maintenance_scheduled_handler.call_args_list[0][0] # Get args from the first call

    assert len(received_event_args) > 0, "Handler was called without arguments"
    # Assuming the handler is called with the event object as the first argument
    # This aligns with how BaseAgent._handle_event typically calls handlers.
    received_event: MaintenanceScheduledEvent = received_event_args[0]

    assert isinstance(received_event, MaintenanceScheduledEvent), \
        f"Expected MaintenanceScheduledEvent, got {type(received_event)}"

    # Critical: Check that the correlation_id propagated through the system
    assert received_event.correlation_id == correlation_id, \
        f"Correlation ID mismatch: Expected {correlation_id}, got {received_event.correlation_id}"

    # Additional checks (optional, but good for verifying data flow)
    assert received_event.equipment_id is not None, "Equipment ID should be set in MaintenanceScheduledEvent"
    # Based on mock logic, equipment_id might be derived from sensor_id
    # e.g., if PredictionAgent._extract_equipment_id uses sensor_id
    # The default mock prediction agent might not set a specific equipment_id pattern,
    # so checking for non-None is a reasonable start.
    # Example of a more specific check if logic was known:
    # expected_equipment_id_pattern = f"equipment_{sensor_event_data['raw_data']['sensor_id']}"
    # assert received_event.equipment_id == expected_equipment_id_pattern, \
    #    f"Equipment ID mismatch: Expected pattern {expected_equipment_id_pattern}, got {received_event.equipment_id}"

    assert received_event.agent_id == "scheduling_agent_01", \
        f"MaintenanceScheduledEvent should be from SchedulingAgent, got from {received_event.agent_id}"

    # Unsubscribe to clean up (good practice if event_bus persists across tests or if handlers are numerous)
    # This might not be strictly necessary if the event_bus is re-created for each test run via the fixture,
    # but explicit cleanup is safer.
    await coordinator.event_bus.unsubscribe(
        MaintenanceScheduledEvent.__name__,
        mock_maintenance_scheduled_handler
    )

    # Coordinator shutdown is handled by the fixture's teardown.
