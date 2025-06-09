"""
Integration tests for MaintenanceLogAgent.
"""

import asyncio
import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.agents.decision.maintenance_log_agent import MaintenanceLogAgent
from core.database.crud.crud_maintenance_log import crud_maintenance_log
from core.database.orm_models import MaintenanceTaskStatus
from core.events.event_bus import EventBus
from core.events.event_models import MaintenanceCompletedEvent
from data.schemas import MaintenanceLogCreate


@pytest.mark.asyncio
async def test_maintenance_log_agent_creates_log_entry(db_session: AsyncSession):
    """
    Test that MaintenanceLogAgent correctly creates a maintenance log entry
    when it receives a MaintenanceCompletedEvent.
    """
    # Setup
    event_bus = EventBus()
    agent = MaintenanceLogAgent(
        agent_id="test_maintenance_log_agent",
        event_bus=event_bus,
        crud_maintenance_log=crud_maintenance_log,
        db_session_factory=lambda: db_session
    )
    
    # Start the agent
    await agent.start()
    
    try:
        # Create test data
        task_id = str(uuid.uuid4())
        equipment_id = "test_equipment_001"
        technician_id = "tech_001"
        completion_date = datetime.utcnow()
        
        # Create and publish MaintenanceCompletedEvent
        event = MaintenanceCompletedEvent(
            task_id=task_id,
            equipment_id=equipment_id,
            technician_id=technician_id,
            completion_date=completion_date,
            status=MaintenanceTaskStatus.COMPLETED.value,
            notes="Test maintenance completion",
            actual_duration_hours=2.5
        )
        
        # Publish the event
        await event_bus.publish(event)
        
        # Wait for event processing
        await asyncio.sleep(0.5)
        
        # Verify the maintenance log was created
        logs = await crud_maintenance_log.get_by_task_id(db_session, uuid.UUID(task_id))
        
        assert len(logs) == 1
        log = logs[0]
        
        assert str(log.task_id) == task_id
        assert log.equipment_id == equipment_id
        assert log.technician_id == technician_id
        assert log.status == MaintenanceTaskStatus.COMPLETED
        assert log.notes == "Test maintenance completion"
        assert log.actual_duration_hours == 2.5
        
    finally:
        # Cleanup
        await agent.stop()


@pytest.mark.asyncio
async def test_maintenance_log_agent_handles_multiple_events(db_session: AsyncSession):
    """
    Test that MaintenanceLogAgent can handle multiple MaintenanceCompletedEvents.
    """
    # Setup
    event_bus = EventBus()
    agent = MaintenanceLogAgent(
        agent_id="test_maintenance_log_agent_multi",
        event_bus=event_bus,
        crud_maintenance_log=crud_maintenance_log,
        db_session_factory=lambda: db_session
    )
    
    # Start the agent
    await agent.start()
    
    try:
        # Create multiple test events
        events = []
        for i in range(3):
            task_id = str(uuid.uuid4())
            event = MaintenanceCompletedEvent(
                task_id=task_id,
                equipment_id=f"test_equipment_{i:03d}",
                technician_id=f"tech_{i:03d}",
                completion_date=datetime.utcnow(),
                status=MaintenanceTaskStatus.COMPLETED.value,
                notes=f"Test maintenance completion {i}",
                actual_duration_hours=float(i + 1)
            )
            events.append(event)
        
        # Publish all events
        for event in events:
            await event_bus.publish(event)
        
        # Wait for event processing
        await asyncio.sleep(1.0)
        
        # Verify all maintenance logs were created
        for i, event in enumerate(events):
            logs = await crud_maintenance_log.get_by_task_id(db_session, uuid.UUID(event.task_id))
            assert len(logs) == 1
            log = logs[0]
            assert log.equipment_id == f"test_equipment_{i:03d}"
            assert log.technician_id == f"tech_{i:03d}"
            assert log.actual_duration_hours == float(i + 1)
        
    finally:
        # Cleanup
        await agent.stop()


@pytest.mark.asyncio
async def test_maintenance_log_agent_handles_error_gracefully(db_session: AsyncSession):
    """
    Test that MaintenanceLogAgent handles errors gracefully and continues processing.
    """
    # Setup
    event_bus = EventBus()
    agent = MaintenanceLogAgent(
        agent_id="test_maintenance_log_agent_error",
        event_bus=event_bus,
        crud_maintenance_log=crud_maintenance_log,
        db_session_factory=lambda: db_session
    )
    
    # Start the agent
    await agent.start()
    
    try:
        # Create an event with invalid data (this should cause an error but not crash the agent)
        invalid_event = MaintenanceCompletedEvent(
            task_id="invalid-uuid",  # Invalid UUID format
            equipment_id="test_equipment_error",
            technician_id="tech_error",
            completion_date=datetime.utcnow(),
            status=MaintenanceTaskStatus.COMPLETED.value,
            notes="Test error handling"
        )
        
        # Create a valid event to ensure the agent continues working
        valid_task_id = str(uuid.uuid4())
        valid_event = MaintenanceCompletedEvent(
            task_id=valid_task_id,
            equipment_id="test_equipment_valid",
            technician_id="tech_valid",
            completion_date=datetime.utcnow(),
            status=MaintenanceTaskStatus.COMPLETED.value,
            notes="Test valid event after error"
        )
        
        # Publish both events
        await event_bus.publish(invalid_event)
        await event_bus.publish(valid_event)
        
        # Wait for event processing
        await asyncio.sleep(1.0)
        
        # Verify that the valid event was processed despite the error
        logs = await crud_maintenance_log.get_by_task_id(db_session, uuid.UUID(valid_task_id))
        assert len(logs) == 1
        log = logs[0]
        assert log.equipment_id == "test_equipment_valid"
        assert log.notes == "Test valid event after error"
        
    finally:
        # Cleanup
        await agent.stop()
