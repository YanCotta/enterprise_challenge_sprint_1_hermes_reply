"""
Integration tests for the SchedulingAgent.

Tests the full integration of the SchedulingAgent with the event bus system            # Verify that a MaintenanceScheduledEvent was published
            scheduled_events = [
                (event_type, event_data) for event_type, event_data in published_events
                if event_type == "MaintenanceScheduledEvent"
            ]
            
            assert len(scheduled_events) == 1
            event_type, event_data = scheduled_events[0]
            
            # Verify event data (event_data is now a MaintenanceScheduledEvent object)
            assert event_data.equipment_id == "integration_test_pump_001"
            assert event_data.assigned_technician_id == "tech_002"
            assert event_data.scheduled_start_time is not None
            assert event_data.scheduled_end_time is not Noneent subscription, publishing, and end-to-end workflows.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.agents.decision.scheduling_agent import SchedulingAgent
from core.events.event_models import MaintenancePredictedEvent
from core.events.event_bus import EventBus


class TestSchedulingAgentIntegration:
    """Integration tests for SchedulingAgent with event bus."""
    
    @pytest.fixture
    async def event_bus(self):
        """Create a real EventBus instance for integration testing."""
        event_bus = EventBus()
        await event_bus.start()
        yield event_bus
        await event_bus.stop()
    
    @pytest.fixture
    def scheduling_agent(self, event_bus):
        """Create a SchedulingAgent instance with real event bus."""
        return SchedulingAgent("integration_test_scheduling_agent", event_bus)
    
    @pytest.fixture
    def sample_prediction_event(self):
        """Create a sample MaintenancePredictedEvent for testing."""
        return MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="integration_test_pump_001",
            predicted_failure_date=datetime.utcnow() + timedelta(days=15),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=10),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=20),
            prediction_confidence=0.85,
            time_to_failure_days=15.0,
            maintenance_type="preventive",
            prediction_method="prophet",
            historical_data_points=100,
            model_metrics={"mae": 0.1, "rmse": 0.15},
            recommended_actions=["inspect_bearings", "check_vibration"],
            agent_id="prediction_agent_001"
        )
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, event_bus, scheduling_agent):
        """Test complete agent lifecycle: initialization, start, and stop."""
        # Test initialization
        assert scheduling_agent.agent_id == "integration_test_scheduling_agent"
        assert scheduling_agent.event_bus == event_bus
        assert scheduling_agent.status == "initializing"
        
        # Test startup
        await scheduling_agent.start()
        assert scheduling_agent.status == "running"
        
        # Verify capabilities were registered
        assert len(scheduling_agent.capabilities) == 2
        
        # Test stop
        await scheduling_agent.stop()
        assert scheduling_agent.status == "stopped"
    
    @pytest.mark.asyncio
    async def test_event_subscription(self, event_bus, scheduling_agent):
        """Test that the agent correctly subscribes to MaintenancePredictedEvent."""
        # Start the agent
        await scheduling_agent.start()
        
        # Check that the agent has subscribed to the correct event
        # Note: This assumes the EventBus has a way to check subscriptions
        # The actual implementation may vary based on your EventBus design
        subscribers = getattr(event_bus, '_subscribers', {})
        assert "MaintenancePredictedEvent" in subscribers
        
        # Verify the handler is correctly registered
        handlers = subscribers.get("MaintenancePredictedEvent", [])
        assert any(handler.__name__ == "handle_maintenance_predicted_event" for handler in handlers)
    
    @pytest.mark.asyncio
    async def test_end_to_end_successful_scheduling(self, event_bus, scheduling_agent, sample_prediction_event):
        """Test end-to-end successful scheduling workflow."""
        # Keep track of published events
        published_events = []
        
        # Mock the event bus publish method to capture events
        original_publish = event_bus.publish
        async def mock_publish(event_type_or_object, data_payload_arg=None):
            if data_payload_arg is None:
                # Pattern 1: event object
                event_obj = event_type_or_object
                event_type_name = event_obj.__class__.__name__
                published_events.append((event_type_name, event_obj))
            else:
                # Pattern 2: explicit event type and data
                event_type_name = str(event_type_or_object)
                published_events.append((event_type_name, data_payload_arg))
            return await original_publish(event_type_or_object, data_payload_arg)
        
        event_bus.publish = mock_publish
        
        # Mock calendar service for successful scheduling
        with patch.object(scheduling_agent.calendar_service, 'check_availability', return_value=True), \
             patch.object(scheduling_agent.calendar_service, 'book_slot', return_value=True):
            
            # Start the agent
            await scheduling_agent.start()
            
            # Publish the prediction event
            await event_bus.publish("MaintenancePredictedEvent", sample_prediction_event.dict())
            
            # Give some time for event processing
            await asyncio.sleep(0.1)
            
            # Verify that a MaintenanceScheduledEvent was published
            scheduled_events = [
                (event_type, event_data) for event_type, event_data in published_events
                if event_type == "MaintenanceScheduledEvent"
            ]
            
            assert len(scheduled_events) == 1
            event_type, event_data = scheduled_events[0]
            
            # Verify event data (event_data is now a MaintenanceScheduledEvent object)
            assert event_data.equipment_id == "integration_test_pump_001"
            assert event_data.assigned_technician_id is not None
            assert event_data.scheduled_start_time is not None
            assert event_data.scheduled_end_time is not None
            assert event_data.scheduling_method == "greedy"
            assert event_data.agent_id == "integration_test_scheduling_agent"
    
    @pytest.mark.asyncio
    async def test_end_to_end_failed_scheduling(self, event_bus, scheduling_agent, sample_prediction_event):
        """Test end-to-end failed scheduling workflow."""
        # Keep track of published events
        published_events = []
        
        # Mock the event bus publish method to capture events
        original_publish = event_bus.publish
        async def mock_publish(event_type_or_object, data_payload_arg=None):
            if data_payload_arg is None:
                # Pattern 1: event object
                event_obj = event_type_or_object
                event_type_name = event_obj.__class__.__name__
                published_events.append((event_type_name, event_obj))
            else:
                # Pattern 2: explicit event type and data
                event_type_name = str(event_type_or_object)
                published_events.append((event_type_name, data_payload_arg))
            return await original_publish(event_type_or_object, data_payload_arg)
        
        event_bus.publish = mock_publish
        
        # Mock calendar service for failed scheduling (no availability)
        with patch.object(scheduling_agent.calendar_service, 'check_availability', return_value=False):
            
            # Start the agent
            await scheduling_agent.start()
            
            # Publish the prediction event
            await event_bus.publish("MaintenancePredictedEvent", sample_prediction_event.dict())
            
            # Give some time for event processing
            await asyncio.sleep(0.1)
            
            # Verify that NO MaintenanceScheduledEvent was published (since scheduling failed)
            scheduled_events = [
                (event_type, event_data) for event_type, event_data in published_events
                if event_type == "MaintenanceScheduledEvent"
            ]
            
            assert len(scheduled_events) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_prediction_events(self, event_bus, scheduling_agent):
        """Test handling multiple prediction events in sequence."""
        published_events = []
        
        # Mock the event bus publish method to capture events
        original_publish = event_bus.publish
        async def mock_publish(event_type_or_object, data_payload_arg=None):
            if data_payload_arg is None:
                # Pattern 1: event object
                event_obj = event_type_or_object
                event_type_name = event_obj.__class__.__name__
                published_events.append((event_type_name, event_obj))
            else:
                # Pattern 2: explicit event type and data
                event_type_name = str(event_type_or_object)
                published_events.append((event_type_name, data_payload_arg))
            return await original_publish(event_type_or_object, data_payload_arg)
        
        event_bus.publish = mock_publish
        
        # Mock calendar service for successful scheduling
        with patch.object(scheduling_agent.calendar_service, 'check_availability', return_value=True), \
             patch.object(scheduling_agent.calendar_service, 'book_slot', return_value=True):
            
            # Start the agent
            await scheduling_agent.start()
            
            # Create multiple prediction events
            events = []
            for i in range(3):
                event = MaintenancePredictedEvent(
                    original_anomaly_event_id=uuid4(),
                    equipment_id=f"test_equipment_{i:03d}",
                    predicted_failure_date=datetime.utcnow() + timedelta(days=10 + i),
                    confidence_interval_lower=datetime.utcnow() + timedelta(days=5 + i),
                    confidence_interval_upper=datetime.utcnow() + timedelta(days=15 + i),
                    prediction_confidence=0.8 + (i * 0.05),
                    time_to_failure_days=10.0 + i,
                    maintenance_type="preventive",
                    historical_data_points=100,
                    agent_id="prediction_agent"
                )
                events.append(event)
            
            # Publish all events
            for event in events:
                await event_bus.publish("MaintenancePredictedEvent", event.dict())
            
            # Give time for processing
            await asyncio.sleep(0.2)
            
            # Verify that 3 MaintenanceScheduledEvent were published
            scheduled_events = [
                (event_type, event_data) for event_type, event_data in published_events
                if event_type == "MaintenanceScheduledEvent"
            ]
            
            assert len(scheduled_events) == 3
            
            # Verify each event has correct equipment ID
            equipment_ids = {event_data.equipment_id for _, event_data in scheduled_events}
            expected_ids = {"test_equipment_000", "test_equipment_001", "test_equipment_002"}
            assert equipment_ids == expected_ids
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, event_bus, scheduling_agent):
        """Test agent health check functionality."""
        # Start the agent
        await scheduling_agent.start()
        
        # Get health status
        health = await scheduling_agent.get_health()
        
        assert health["agent_id"] == "integration_test_scheduling_agent"
        assert health["status"] == "running"
        assert "timestamp" in health
        
        # Verify timestamp is recent (within last minute)
        timestamp = datetime.fromisoformat(health["timestamp"].replace('Z', '+00:00'))
        time_diff = abs((datetime.now(timestamp.tzinfo) - timestamp).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, event_bus, scheduling_agent):
        """Test agent error handling with malformed event data."""
        # Start the agent
        await scheduling_agent.start()
        
        # Publish malformed event data
        malformed_data = {
            "equipment_id": "test_equipment",
            # Missing required fields
        }
        
        # This should not crash the agent
        await event_bus.publish("MaintenancePredictedEvent", malformed_data)
        
        # Give time for processing
        await asyncio.sleep(0.1)
        
        # Agent should still be running
        health = await scheduling_agent.get_health()
        assert health["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, event_bus, scheduling_agent):
        """Test that the agent can handle concurrent events correctly."""
        published_events = []
        
        # Mock the event bus publish method to capture events
        original_publish = event_bus.publish
        async def mock_publish(event_type_or_object, data_payload_arg=None):
            if data_payload_arg is None:
                # Pattern 1: event object
                event_obj = event_type_or_object
                event_type_name = event_obj.__class__.__name__
                published_events.append((event_type_name, event_obj))
            else:
                # Pattern 2: explicit event type and data
                event_type_name = str(event_type_or_object)
                published_events.append((event_type_name, data_payload_arg))
            return await original_publish(event_type_or_object, data_payload_arg)
        
        event_bus.publish = mock_publish
        
        # Mock calendar service for successful scheduling
        with patch.object(scheduling_agent.calendar_service, 'check_availability', return_value=True), \
             patch.object(scheduling_agent.calendar_service, 'book_slot', return_value=True):
            
            # Start the agent
            await scheduling_agent.start()
            
            # Create and publish multiple events concurrently
            async def publish_event(equipment_id):
                event = MaintenancePredictedEvent(
                    original_anomaly_event_id=uuid4(),
                    equipment_id=equipment_id,
                    predicted_failure_date=datetime.utcnow() + timedelta(days=15),
                    confidence_interval_lower=datetime.utcnow() + timedelta(days=10),
                    confidence_interval_upper=datetime.utcnow() + timedelta(days=20),
                    prediction_confidence=0.8,
                    time_to_failure_days=15.0,
                    historical_data_points=100,
                    agent_id="prediction_agent"
                )
                await event_bus.publish("MaintenancePredictedEvent", event.dict())
            
            # Publish 5 events concurrently
            tasks = [publish_event(f"concurrent_equipment_{i}") for i in range(5)]
            await asyncio.gather(*tasks)
            
            # Give time for processing
            await asyncio.sleep(0.3)
            
            # Verify all events were processed
            scheduled_events = [
                (event_type, event_data) for event_type, event_data in published_events
                if event_type == "MaintenanceScheduledEvent"
            ]
            
            assert len(scheduled_events) == 5
            
            # Verify all equipment IDs are present
            equipment_ids = {event_data.equipment_id for _, event_data in scheduled_events}
            expected_ids = {f"concurrent_equipment_{i}" for i in range(5)}
            assert equipment_ids == expected_ids
