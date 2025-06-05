#!/usr/bin/env python3
"""
Demonstration script for the NotificationAgent.

This script shows how the NotificationAgent handles MaintenanceScheduledEvent
and sends notifications through the console provider.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from apps.agents.decision.notification_agent import NotificationAgent
from core.events.event_models import MaintenanceScheduledEvent
from core.events.event_bus import EventBus


async def demonstrate_notification_agent():
    """Demonstrate the NotificationAgent functionality."""
    print("=== NotificationAgent Demonstration ===\n")
    
    # Create an event bus
    event_bus = EventBus()
    
    # Create and start the NotificationAgent
    notification_agent = NotificationAgent("demo-notification-agent", event_bus)
    await notification_agent.start()
    
    print("NotificationAgent started successfully!\n")
    
    # Create a sample MaintenanceScheduledEvent for successful scheduling
    successful_event = MaintenanceScheduledEvent(
        event_id=uuid.uuid4(),
        original_prediction_event_id=uuid.uuid4(),
        equipment_id="PUMP-DEMO-001",
        scheduled_start_time=datetime(2024, 6, 15, 9, 0, tzinfo=timezone.utc),
        scheduled_end_time=datetime(2024, 6, 15, 11, 0, tzinfo=timezone.utc),
        assigned_technician_id="tech-john-doe",
        scheduling_method="optimization",
        optimization_score=0.92,
        schedule_details={
            "priority": "High",
            "estimated_duration_hours": 2.0,
            "location": "Building A - Basement",
            "task_description": "Replace worn pump bearings and check alignment",
            "required_skills": ["mechanical_systems", "bearing_replacement"],
            "parts_needed": ["bearing_set_6205", "coupling_grease", "alignment_tools"]
        },
        constraints_violated=[],
        agent_id="scheduling-agent-001"
    )
    
    print("1. Demonstrating SUCCESSFUL maintenance scheduling notification:")
    print("-" * 60)
    await notification_agent.handle_maintenance_scheduled_event(successful_event.dict())
    print("\n")
    
    # Create a sample MaintenanceScheduledEvent for failed scheduling
    failed_event = MaintenanceScheduledEvent(
        event_id=uuid.uuid4(),
        original_prediction_event_id=uuid.uuid4(),
        equipment_id="COMPRESSOR-DEMO-002",
        scheduled_start_time=None,
        scheduled_end_time=None,
        assigned_technician_id=None,
        scheduling_method="manual",
        optimization_score=0.0,
        schedule_details={
            "priority": "Critical",
            "estimated_duration_hours": 4.0,
            "task_description": "Emergency compressor repair - overheating detected"
        },
        constraints_violated=["no_available_technicians", "parts_not_in_stock"],
        agent_id="scheduling-agent-001"
    )
    
    print("2. Demonstrating FAILED maintenance scheduling notification:")
    print("-" * 60)
    await notification_agent.handle_maintenance_scheduled_event(failed_event.dict())
    print("\n")
    
    # Show agent health
    health = await notification_agent.get_health()
    print("3. Agent Health Status:")
    print("-" * 60)
    print(f"Agent ID: {health['agent_id']}")
    print(f"Status: {health['status']}")
    print(f"Available Channels: {health['available_channels']}")
    print(f"Providers Count: {health['providers_count']}")
    print(f"Templates Count: {health['templates_count']}")
    print(f"Capabilities Count: {health['capabilities_count']}")
    print("\n")
    
    # Stop the agent
    await notification_agent.stop()
    print("NotificationAgent stopped successfully!")
    print("\n=== Demonstration Complete ===")


if __name__ == "__main__":
    asyncio.run(demonstrate_notification_agent())
