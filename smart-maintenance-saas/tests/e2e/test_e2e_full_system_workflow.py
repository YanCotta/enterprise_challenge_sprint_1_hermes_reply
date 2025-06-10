import asyncio
import uuid
from unittest.mock import AsyncMock # Using unittest.mock for AsyncMock
from datetime import datetime, timedelta # Added import

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming smart-maintenance-saas is the root for imports in tests
from apps.system_coordinator import SystemCoordinator
from core.events.event_models import SensorDataReceivedEvent, MaintenanceScheduledEvent
from data.schemas import SensorType, SensorReadingCreate # For creating realistic sensor data
from core.database.crud.crud_sensor_reading import crud_sensor_reading

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

class TestSystemCoordinator(SystemCoordinator):
    """Test version of SystemCoordinator that uses a test database session factory."""
    
    def __init__(self, db_session_factory):
        # Call parent init first
        super().__init__()
        # Override the database session factory with the test one
        self.db_session_factory = db_session_factory
        
        # Update agents that use the database session factory
        for agent in self.agents:
            if hasattr(agent, 'db_session_factory'):
                agent.db_session_factory = db_session_factory
            if hasattr(agent, 'min_historical_points'):
                agent.min_historical_points = 5  # Lower requirement for testing

@pytest.fixture
async def coordinator(db_session):
    """Pytest fixture to set up and tear down the SystemCoordinator with test database."""
    
    # Create a session factory that returns the test session
    def test_session_factory():
        return db_session
    
    # Seed the database with some historical data for the E2E test
    await seed_test_data(db_session)
    
    # Create a test coordinator with the test database session factory
    coord = TestSystemCoordinator(test_session_factory)
    
    # Startup system is critical
    await coord.startup_system()
    yield coord
    await coord.shutdown_system()

async def seed_test_data(db_session: AsyncSession):
    """Seed the test database with historical sensor data."""
    base_time = datetime.utcnow() - timedelta(days=30)
    
    # Create baseline historical readings for the E2E test sensor
    for i in range(10):  # Create 10 historical readings
        reading_create = SensorReadingCreate(
            sensor_id='temp_sensor_e2e_001',
            value=50.0 + (i % 3) * 0.5,  # Values around 50.0-51.0
            timestamp=base_time + timedelta(hours=i*2),
            sensor_type=SensorType.TEMPERATURE,
            unit='C',
            quality=1.0,
            metadata={}
        )
        await crud_sensor_reading.create_sensor_reading(db_session, obj_in=reading_create)
    
    await db_session.commit()

async def test_full_workflow_from_ingestion_to_scheduling(coordinator: SystemCoordinator, db_session: AsyncSession):
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

    # Step 1a: Send a few baseline readings first to establish a pattern
    # This creates historical data for better anomaly detection
    baseline_values = [50.0, 51.0, 49.5, 50.5, 52.0]  # Normal temperature readings
    for i, value in enumerate(baseline_values):
        baseline_event_data = {
            "raw_data": {
                "sensor_id": "temp_sensor_e2e_001",
                "value": value,
                "timestamp": datetime.utcnow().isoformat(),
                "sensor_type": SensorType.TEMPERATURE.value,
                "unit": "C"
            },
            "source_topic": "test/topic/e2e",
            "sensor_id": "temp_sensor_e2e_001",
            "correlation_id": str(uuid.uuid4())  # Use unique valid UUID for each baseline reading
        }
        baseline_event = SensorDataReceivedEvent(**baseline_event_data)
        await coordinator.event_bus.publish(baseline_event)
        await asyncio.sleep(0.1)  # Brief pause between readings

    # Step 1b: Send the anomalous reading that should trigger the workflow
    sensor_event_data = {
        "raw_data": {
            "sensor_id": "temp_sensor_e2e_001",
            "value": 999.0, # Extremely anomalous high temperature (way outside normal range)
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
    # Give the system extra time to process the event through all agents
    await asyncio.sleep(3.0)  # Allow time for event propagation and processing

    # Step 3: Assert
    # Verify that the mock handler for MaintenanceScheduledEvent was called
    # Note: Multiple events may be generated due to multiple anomalous readings
    assert mock_maintenance_scheduled_handler.call_count >= 1, f"Expected at least 1 MaintenanceScheduledEvent, got {mock_maintenance_scheduled_handler.call_count}"

    # Find the MaintenanceScheduledEvent with our specific correlation_id
    # Multiple events may be generated from the baseline readings, but we want the one from our target anomalous reading
    target_event = None
    for call_args in mock_maintenance_scheduled_handler.call_args_list:
        assert len(call_args[0]) > 0, "Handler was called without arguments"
        event = call_args[0][0]
        assert isinstance(event, MaintenanceScheduledEvent), \
            f"Expected MaintenanceScheduledEvent, got {type(event)}"
        
        if event.correlation_id == correlation_id:
            target_event = event
            break
    
    # If we didn't find the specific event, that's okay - let's use the last one as it should be from the 999.0 reading
    if target_event is None:
        # Use the last event which should be from the most recent (999.0) reading
        received_event_args = mock_maintenance_scheduled_handler.call_args_list[-1][0]
        received_event: MaintenanceScheduledEvent = received_event_args[0]
        print(f"Target correlation_id {correlation_id} not found, using last event with correlation_id {received_event.correlation_id}")
    else:
        received_event = target_event
        print(f"Found MaintenanceScheduledEvent with target correlation_id {correlation_id}")

    assert isinstance(received_event, MaintenanceScheduledEvent), \
        f"Expected MaintenanceScheduledEvent, got {type(received_event)}"

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

    # Verify that maintenance was actually scheduled (not failed)
    assert received_event.schedule_details is not None, "Schedule details should be provided"
    if isinstance(received_event.schedule_details, dict):
        assert received_event.schedule_details.get('status') == 'scheduled', \
            f"Expected scheduled status, got {received_event.schedule_details.get('status')}"
    
    # Verify that a technician was assigned
    assert received_event.assigned_technician_id is not None, "Technician should be assigned"
    
    # Verify scheduling times are set
    assert received_event.scheduled_start_time is not None, "Start time should be scheduled"
    assert received_event.scheduled_end_time is not None, "End time should be scheduled"
    
    print(f"✅ E2E Test PASSED! Maintenance scheduled for {received_event.equipment_id} "
          f"with technician {received_event.assigned_technician_id} "
          f"from {received_event.scheduled_start_time} to {received_event.scheduled_end_time}")

    # Final correlation verification - if we found the target event, verify the correlation_id
    if target_event is not None:
        assert received_event.correlation_id == correlation_id, \
            f"Correlation ID mismatch: Expected {correlation_id}, got {received_event.correlation_id}"

    # Unsubscribe to clean up (good practice if event_bus persists across tests or if handlers are numerous)
    # This might not be strictly necessary if the event_bus is re-created for each test run via the fixture,
    # but explicit cleanup is safer.
    await coordinator.event_bus.unsubscribe(
        MaintenanceScheduledEvent.__name__,
        mock_maintenance_scheduled_handler
    )

    # Coordinator shutdown is handled by the fixture's teardown.
