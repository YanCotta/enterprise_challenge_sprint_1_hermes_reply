"""
Integration tests for NotificationAgent.

This module tests the NotificationAgent's integration with the event system,
including end-to-end notification flows and real event handling.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from apps.agents.decision.notification_agent import NotificationAgent
from data.exceptions import AgentProcessingError, DataValidationException
from core.events.event_models import MaintenanceScheduledEvent
from data.schemas import (
    NotificationChannel,
    NotificationStatus,
    OptimizedSchedule,
    ScheduleStatus
)


@pytest.mark.asyncio
class TestNotificationAgentIntegration:
    """Integration tests for NotificationAgent."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus for integration testing."""
        mock_bus = AsyncMock()
        mock_bus.subscribe = AsyncMock()
        mock_bus.publish = AsyncMock()
        return mock_bus
    
    @pytest.fixture
    async def notification_agent(self, mock_event_bus):
        """Create and start a NotificationAgent for testing."""
        agent = NotificationAgent("integration-test-agent", mock_event_bus)
        await agent.start()
        return agent
    
    @pytest.fixture
    def sample_maintenance_event(self):
        """Create a sample MaintenanceScheduledEvent for testing."""
        return MaintenanceScheduledEvent(
            event_id=uuid.uuid4(),
            original_prediction_event_id=uuid.uuid4(),
            equipment_id="PUMP-INTEGRATION-001",
            agent_id="prediction-agent-123",
            maintenance_request_id="req-integration-123",
            scheduled_start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            scheduled_end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            assigned_technician_id="tech-integration-456",
            scheduling_method="optimization",
            optimization_score=0.90,
            schedule_details={
                "priority": "High",
                "estimated_duration_hours": 2.0,
                "location": "Building A - Floor 3",
                "task_description": "Preventive maintenance on centrifugal pump",
                "required_skills": ["hydraulic_systems", "electrical_safety"],
                "parts_needed": ["pump_seal_kit", "bearing_grease", "oil_filter"]
            },
            constraints_violated=[]
        )
    
    async def test_agent_lifecycle(self, mock_event_bus):
        """Test complete agent lifecycle: initialization, start, operation, stop."""
        # Create agent
        agent = NotificationAgent("lifecycle-test-agent", mock_event_bus)
        assert agent.status == "initialized"
        assert len(agent.capabilities) == 0  # Capabilities registered on start
        
        # Start agent
        await agent.start()
        assert agent.status == "running"
        assert len(agent.capabilities) >= 2
        
        # Verify event subscription
        mock_event_bus.subscribe.assert_called_once_with(
            "MaintenanceScheduledEvent",
            agent.handle_maintenance_scheduled_event
        )
        
        # Stop agent
        await agent.stop()
        assert agent.status == "stopped"
    
    async def test_event_subscription_and_handling(self, notification_agent, sample_maintenance_event):
        """Test that the agent properly subscribes to and handles events."""
        # Verify subscription occurred during start
        notification_agent.event_bus.subscribe.assert_called_with(
            "MaintenanceScheduledEvent",
            notification_agent.handle_maintenance_scheduled_event
        )
        
        # Test event handling through the process method (proper flow)
        event_data = sample_maintenance_event.dict()
        
        # Capture console output to verify notification was sent
        with patch('builtins.print') as mock_print:
            await notification_agent.process(event_data)
            
            # Verify that print was called (console notification)
            assert mock_print.called
            
            # Check that the printed content contains expected information
            printed_content = ''.join([str(call) for call in mock_print.call_args_list])
            assert "PUMP-INTEGRATION-001" in printed_content
            assert "MAINTENANCE NOTIFICATION" in printed_content
            assert "tech-integration-456" in printed_content
    
    async def test_end_to_end_notification_flow(self, notification_agent, sample_maintenance_event, capsys):
        """Test complete end-to-end notification flow from event to delivery."""
        # Create event data
        event_data = sample_maintenance_event.dict()
        
        # Handle the event through the process method
        await notification_agent.process(event_data)
        
        # Capture console output
        captured = capsys.readouterr()
        
        # Verify notification was sent to console
        assert "MAINTENANCE NOTIFICATION" in captured.out
        assert "PUMP-INTEGRATION-001" in captured.out
        assert "technician_tech-integration-456" in captured.out
        assert "🔧 Maintenance Scheduled" in captured.out
        # The template is basic and doesn't include detailed task descriptions
        assert "Tech tech-integration-456" in captured.out
    
    async def test_failed_scheduling_notification(self, notification_agent, capsys):
        """Test notification for failed scheduling scenarios."""
        # Create failed scheduling event
        failed_event = MaintenanceScheduledEvent(
            event_id=uuid.uuid4(),
            original_prediction_event_id=uuid.uuid4(),
            equipment_id="PUMP-FAILED-002",
            agent_id="prediction-agent-124",
            maintenance_request_id="req-failed-124",
            scheduled_start_time=None,
            scheduled_end_time=None,
            assigned_technician_id=None,
            scheduling_method="manual",
            optimization_score=0.0,
            schedule_details={
                "priority": "Critical",
                "task_description": "Emergency repair required"
            },
            constraints_violated=["no_available_technicians", "parts_shortage"]
        )
        
        event_data = failed_event.dict()
        
        # Handle the event through the process method
        await notification_agent.process(event_data)
        
        # Capture console output
        captured = capsys.readouterr()
        
        # Verify failure notification was sent
        assert "⚠️ Maintenance Scheduling Failed" in captured.out
        assert "PUMP-FAILED-002" in captured.out
        assert "technician_unassigned" in captured.out
    
    async def test_multiple_events_handling(self, notification_agent, capsys):
        """Test handling multiple events in sequence."""
        events = []
        
        # Create multiple events
        for i in range(3):
            event = MaintenanceScheduledEvent(
                event_id=uuid.uuid4(),
                original_prediction_event_id=uuid.uuid4(),
                equipment_id=f"PUMP-MULTI-{i:03d}",
                agent_id=f"prediction-agent-{i:03d}",
                maintenance_request_id=f"req-multi-{i:03d}",
                scheduled_start_time=datetime(2024, 1, 15 + i, 10, 0, tzinfo=timezone.utc),
                scheduled_end_time=datetime(2024, 1, 15 + i, 12, 0, tzinfo=timezone.utc),
                assigned_technician_id=f"tech-multi-{i:03d}",
                scheduling_method="optimization",
                optimization_score=0.80 + (i * 0.05),
                schedule_details={
                    "priority": "Medium",
                    "task_description": f"Maintenance task {i + 1}"
                },
                constraints_violated=[]
            )
            events.append(event)
        
        # Handle all events through the process method
        for event in events:
            await notification_agent.process(event.dict())
        
        # Capture console output
        captured = capsys.readouterr()
        
        # Verify all notifications were sent
        for i in range(3):
            assert f"PUMP-MULTI-{i:03d}" in captured.out
    
    async def test_agent_health_during_operation(self, notification_agent, sample_maintenance_event):
        """Test agent health reporting during normal operation."""
        # Check initial health
        health = await notification_agent.get_health()
        assert health["status"] == "running"
        assert health["providers_count"] == 1
        assert health["available_channels"] == ["console"]
        
        # Process an event
        await notification_agent.process(sample_maintenance_event.dict())
        
        # Check health after processing
        health = await notification_agent.get_health()
        assert health["status"] == "running"  # Should still be running
        assert "timestamp" in health
    
    async def test_error_resilience(self, notification_agent):
        """Test agent resilience to malformed events and errors."""
        # Test with completely invalid event data
        invalid_events = [
            {},  # Empty dict
            {"invalid": "data"},  # Wrong structure
            {"event_id": "not-a-uuid"},  # Invalid UUID
            None  # None type
        ]
        
        for invalid_event in invalid_events:
            # Agent should handle errors gracefully without crashing
            # For invalid data, we expect exceptions to be raised
            try:
                await notification_agent.process(invalid_event)
            except Exception as e:
                # This is expected for invalid data - agent should log errors gracefully
                assert isinstance(e, (AgentProcessingError, DataValidationException))
                
            # Agent should still be running after error
            health = await notification_agent.get_health()
            assert health["status"] == "running"
    
    async def test_concurrent_event_handling(self, notification_agent):
        """Test agent's ability to handle concurrent events."""
        # Create multiple events
        events = []
        for i in range(5):
            event = MaintenanceScheduledEvent(
                event_id=uuid.uuid4(),
                original_prediction_event_id=uuid.uuid4(),
                equipment_id=f"PUMP-CONCURRENT-{i:03d}",
                agent_id=f"prediction-agent-{i:03d}",
                maintenance_request_id=f"req-concurrent-{i:03d}",
                scheduled_start_time=datetime(2024, 1, 15, 10 + i, 0, tzinfo=timezone.utc),
                scheduled_end_time=datetime(2024, 1, 15, 12 + i, 0, tzinfo=timezone.utc),
                assigned_technician_id=f"tech-concurrent-{i:03d}",
                scheduling_method="optimization",
                optimization_score=0.75,
                schedule_details={"priority": "Medium"},
                constraints_violated=[]
            )
            events.append(event)
        
        # Handle events concurrently
        tasks = []
        for event in events:
            task = asyncio.create_task(
                notification_agent.process(event.dict())
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Agent should still be healthy after concurrent processing
        health = await notification_agent.get_health()
        assert health["status"] == "running"
    
    async def test_notification_template_rendering_integration(self, notification_agent, sample_maintenance_event):
        """Test template rendering in the context of full event processing."""
        event_data = sample_maintenance_event.dict()
        
        # Mock the provider to capture the actual notification request
        captured_requests = []
        
        original_send = notification_agent.providers[NotificationChannel.CONSOLE].send
        
        def capture_send(request):
            captured_requests.append(request)
            return original_send(request)
        
        notification_agent.providers[NotificationChannel.CONSOLE].send = capture_send
        
        # Handle event through the process method
        await notification_agent.process(event_data)
        
        # Verify request was captured and properly rendered
        assert len(captured_requests) == 1
        request = captured_requests[0]
        
        assert request.subject == "🔧 Maintenance Scheduled for PUMP-INTEGRATION-001"
        assert "PUMP-INTEGRATION-001" in request.message
        # The template is basic and doesn't include detailed task descriptions
        assert "🔧 Maintenance Scheduled for PUMP-INTEGRATION-001" in request.message
        assert "Tech tech-integration-456" in request.message
        assert request.template_id == "maintenance_scheduled"
        # Metadata contains event_id, not equipment_id (equipment_id is in template_data)
        assert "event_id" in request.metadata
        assert request.template_data["equipment_id"] == "PUMP-INTEGRATION-001"
    
    async def test_provider_integration(self, notification_agent):
        """Test integration between agent and notification providers."""
        # Verify console provider is properly initialized
        assert NotificationChannel.CONSOLE in notification_agent.providers
        console_provider = notification_agent.providers[NotificationChannel.CONSOLE]
        
        # Test provider supports expected channel
        assert console_provider.supports_channel(NotificationChannel.CONSOLE)
        assert not console_provider.supports_channel(NotificationChannel.EMAIL)
        
        # Test provider can handle notification requests
        from data.schemas import NotificationRequest
        
        test_request = NotificationRequest(
            id="integration-test-request",
            recipient="integration@test.com",
            channel=NotificationChannel.CONSOLE,
            subject="Integration Test",
            message="Testing provider integration",
            priority=3
        )
        
        result = console_provider.send(test_request)
        assert result.status == NotificationStatus.SENT
        assert result.request_id == test_request.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
