"""
Unit tests for NotificationAgent and related components.

This module tests the NotificationAgent's core functionality including:
- Event handling and notification creation
- Provider interaction and error handling
- Template rendering and message formatting
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from apps.agents.decision.notification_agent import (
    NotificationAgent,
    ConsoleNotificationProvider,
    NotificationProvider
)
from core.events.event_models import MaintenanceScheduledEvent
from data.schemas import (
    NotificationChannel,
    NotificationRequest,
    NotificationResult,
    NotificationStatus,
    OptimizedSchedule,
    ScheduleStatus
)


class TestConsoleNotificationProvider:
    """Test cases for ConsoleNotificationProvider."""
    
    def test_init(self):
        """Test provider initialization."""
        provider = ConsoleNotificationProvider()
        assert provider is not None
        assert hasattr(provider, 'logger')
    
    def test_supports_channel(self):
        """Test channel support checking."""
        provider = ConsoleNotificationProvider()
        
        # Should support console channel
        assert provider.supports_channel(NotificationChannel.CONSOLE) is True
        
        # Should not support other channels
        assert provider.supports_channel(NotificationChannel.EMAIL) is False
        assert provider.supports_channel(NotificationChannel.SMS) is False
    
    def test_send_success(self, capsys):
        """Test successful notification sending."""
        provider = ConsoleNotificationProvider()
        
        # Create test notification request
        request = NotificationRequest(
            id="test-123",
            recipient="test@example.com",
            channel=NotificationChannel.CONSOLE,
            subject="Test Notification",
            message="This is a test message",
            priority=2,
            metadata={"test_key": "test_value"}
        )
        
        # Send notification
        result = provider.send(request)
        
        # Check result
        assert result.request_id == request.id
        assert result.status == NotificationStatus.SENT
        assert result.channel_used == NotificationChannel.CONSOLE
        assert result.sent_at is not None
        assert result.delivered_at is not None
        assert result.error_message is None
        
        # Check console output
        captured = capsys.readouterr()
        assert "MAINTENANCE NOTIFICATION" in captured.out
        assert "Test Notification" in captured.out
        assert "This is a test message" in captured.out
        assert "test@example.com" in captured.out
    
    @patch('apps.agents.decision.notification_agent.print')
    def test_send_failure(self, mock_print):
        """Test notification sending failure."""
        provider = ConsoleNotificationProvider()
        
        # Mock print to raise an exception
        mock_print.side_effect = Exception("Print failed")
        
        request = NotificationRequest(
            id="test-456",
            recipient="test@example.com",
            channel=NotificationChannel.CONSOLE,
            subject="Test Notification",
            message="This is a test message",
            priority=2
        )
        
        # Send notification
        result = provider.send(request)
        
        # Check result
        assert result.request_id == request.id
        assert result.status == NotificationStatus.FAILED
        assert result.channel_used == NotificationChannel.CONSOLE
        assert result.sent_at is not None
        assert result.delivered_at is None
        assert "Print failed" in result.error_message
    
    def test_format_metadata_empty(self):
        """Test metadata formatting with empty metadata."""
        provider = ConsoleNotificationProvider()
        
        result = provider._format_metadata({})
        assert result == "  (none)"
    
    def test_format_metadata_with_data(self):
        """Test metadata formatting with data."""
        provider = ConsoleNotificationProvider()
        
        metadata = {
            "key1": "value1",
            "key2": "value2"
        }
        
        result = provider._format_metadata(metadata)
        assert "key1: value1" in result
        assert "key2: value2" in result


class TestNotificationAgent:
    """Test cases for NotificationAgent."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus."""
        mock_bus = AsyncMock()
        mock_bus.subscribe = AsyncMock()
        return mock_bus
    
    @pytest.fixture
    def notification_agent(self, mock_event_bus):
        """Create a NotificationAgent instance for testing."""
        return NotificationAgent("test-agent-001", mock_event_bus)
    
    def test_init(self, notification_agent):
        """Test agent initialization."""
        assert notification_agent.agent_id == "test-agent-001"
        assert notification_agent.status == "initialized"
        assert len(notification_agent.providers) == 1
        assert NotificationChannel.CONSOLE in notification_agent.providers
        assert len(notification_agent.templates) > 0
        assert "maintenance_scheduled" in notification_agent.templates
    
    @pytest.mark.asyncio
    async def test_start(self, notification_agent, mock_event_bus):
        """Test agent startup."""
        await notification_agent.start()
        
        assert notification_agent.status == "running"
        assert len(notification_agent.capabilities) >= 2
        
        # Check event subscription
        mock_event_bus.subscribe.assert_called_once_with(
            "MaintenanceScheduledEvent",
            notification_agent.handle_maintenance_scheduled_event
        )
    
    @pytest.mark.asyncio
    async def test_stop(self, notification_agent):
        """Test agent shutdown."""
        await notification_agent.stop()
        
        assert notification_agent.status == "stopped"
    
    @pytest.mark.asyncio
    async def test_get_health(self, notification_agent):
        """Test health status retrieval."""
        health = await notification_agent.get_health()
        
        assert health["agent_id"] == "test-agent-001"
        assert health["status"] == "initialized"
        assert health["providers_count"] == 1
        assert health["available_channels"] == ["console"]
        assert health["templates_count"] > 0
        assert "timestamp" in health
    
    def test_create_maintenance_notification_request_success(self, notification_agent):
        """Test creating notification request from successful scheduling event."""
        # Create test event with successful scheduling
        event = MaintenanceScheduledEvent(
            original_prediction_event_id=uuid.uuid4(),
            agent_id="scheduling-agent-001",
            event_id=uuid.uuid4(),
            equipment_id="PUMP-001",
            scheduled_start_time=datetime.now(timezone.utc),
            scheduled_end_time=datetime.now(timezone.utc),
            assigned_technician_id="tech-456",
            scheduling_method="optimization",
            optimization_score=0.85,
            schedule_details={
                "priority": "High",
                "estimated_duration_hours": 2.5,
                "task_description": "Pump maintenance",
                "required_skills": ["hydraulic", "electrical"],
                "parts_needed": ["seal-kit", "oil-filter"]
            },
            constraints_violated=[]
        )
        
        # Create notification request
        request = notification_agent._create_maintenance_notification_request(event)
        
        # Verify request
        assert request.recipient == "technician_tech-456"
        assert request.channel == NotificationChannel.CONSOLE
        assert "🔧 Maintenance Scheduled" in request.subject
        assert "PUMP-001" in request.subject
        assert request.priority == 2  # High priority for scheduled maintenance
        assert request.template_id == "maintenance_scheduled"
        assert "equipment_id" in request.metadata
        assert request.metadata["equipment_id"] == "PUMP-001"
    
    def test_create_maintenance_notification_request_failure(self, notification_agent):
        """Test creating notification request from failed scheduling event."""
        # Create test event with failed scheduling
        event = MaintenanceScheduledEvent(
            original_prediction_event_id=uuid.uuid4(),
            agent_id="scheduling-agent-002",
            event_id=uuid.uuid4(),
            equipment_id="PUMP-002",
            scheduled_start_time=None,
            scheduled_end_time=None,
            assigned_technician_id=None,
            scheduling_method="manual",
            optimization_score=0.0,
            schedule_details={"priority": "Critical"},
            constraints_violated=["resource_unavailable", "time_conflict"]
        )
        
        # Create notification request
        request = notification_agent._create_maintenance_notification_request(event)
        
        # Verify request
        assert request.recipient == "technician_unassigned"
        assert "⚠️ Maintenance Scheduling Failed" in request.subject
        assert request.priority == 1  # Highest priority for failures
        assert request.template_id == "maintenance_failed_to_schedule"
    
    def test_render_template_success(self, notification_agent):
        """Test successful template rendering."""
        template_data = {
            "equipment_id": "PUMP-001",
            "technician_name": "John Doe",
            "scheduled_start_time": "2024-01-15 10:00",
            "scheduled_end_time": "2024-01-15 12:00",
            "priority": "High",
            "estimated_duration": "2",
            "location": "Building A",
            "task_description": "Routine maintenance",
            "required_skills": "hydraulic, electrical",
            "parts_needed": "seal-kit"
        }
        
        result = notification_agent._render_template("maintenance_scheduled", template_data)
        
        assert "PUMP-001" in result
        assert "John Doe" in result
        assert "2024-01-15 10:00" in result
        assert "Routine maintenance" in result
    
    def test_render_template_missing_template(self, notification_agent):
        """Test template rendering with missing template."""
        result = notification_agent._render_template("nonexistent_template", {})
        
        assert "No template found for nonexistent_template" in result
    
    def test_render_template_missing_data(self, notification_agent):
        """Test template rendering with missing data."""
        incomplete_data = {"equipment_id": "PUMP-001"}  # Missing required fields
        
        result = notification_agent._render_template("maintenance_scheduled", incomplete_data)
        
        assert "Template rendering failed" in result or "KeyError" in result
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self, notification_agent):
        """Test successful notification sending."""
        request = NotificationRequest(
            id="test-789",
            recipient="test@example.com",
            channel=NotificationChannel.CONSOLE,
            subject="Test Subject",
            message="Test Message",
            priority=3
        )
        
        # Mock the provider
        mock_provider = MagicMock(spec=NotificationProvider)
        mock_result = NotificationResult(
            request_id=request.id,
            status=NotificationStatus.SENT,
            channel_used=NotificationChannel.CONSOLE,
            sent_at=datetime.now(timezone.utc)
        )
        mock_provider.send.return_value = mock_result
        notification_agent.providers[NotificationChannel.CONSOLE] = mock_provider
        
        # Send notification
        result = await notification_agent.send_notification(request)
        
        # Verify
        assert result.status == NotificationStatus.SENT
        mock_provider.send.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_send_notification_no_provider(self, notification_agent):
        """Test notification sending with no available provider."""
        request = NotificationRequest(
            id="test-999",
            recipient="test@example.com",
            channel=NotificationChannel.EMAIL,  # No email provider available
            subject="Test Subject",
            message="Test Message",
            priority=3
        )
        
        # Send notification
        result = await notification_agent.send_notification(request)
        
        # Verify failure
        assert result.status == NotificationStatus.FAILED
        assert "No provider available" in result.error_message
        assert result.channel_used == NotificationChannel.EMAIL
    
    @pytest.mark.asyncio
    async def test_handle_maintenance_scheduled_event_success(self, notification_agent):
        """Test successful handling of maintenance scheduled event."""
        # Create test event data
        event_data = {
            "original_prediction_event_id": str(uuid.uuid4()),
            "agent_id": "scheduling-agent-003",
            "event_id": str(uuid.uuid4()),
            "equipment_id": "PUMP-001",
            "scheduled_start_time": datetime.now(timezone.utc).isoformat(),
            "scheduled_end_time": datetime.now(timezone.utc).isoformat(),
            "assigned_technician_id": "tech-456",
            "scheduling_method": "optimization",
            "optimization_score": 0.85,
            "schedule_details": {
                "priority": "High",
                "task_description": "Pump maintenance"
            },
            "constraints_violated": []
        }
        
        # Mock send_notification
        with patch.object(notification_agent, 'send_notification') as mock_send:
            mock_send.return_value = NotificationResult(
                request_id="test-123",
                status=NotificationStatus.SENT,
                channel_used=NotificationChannel.CONSOLE,
                sent_at=datetime.now(timezone.utc)
            )
            
            # Handle event
            await notification_agent.handle_maintenance_scheduled_event(event_data)
            
            # Verify send_notification was called
            assert mock_send.called
            call_args = mock_send.call_args[0][0]
            assert isinstance(call_args, NotificationRequest)
            assert call_args.recipient == "technician_tech-456"
    
    @pytest.mark.asyncio
    async def test_handle_maintenance_scheduled_event_error(self, notification_agent):
        """Test error handling in maintenance scheduled event handler."""
        # Create invalid event data
        invalid_event_data = {"invalid": "data"}
        
        # Handle event (should not raise exception)
        await notification_agent.handle_maintenance_scheduled_event(invalid_event_data)
        
        # Agent should continue running despite error
        # No assertion needed, just verify no exception is raised


class TestNotificationProviderInterface:
    """Test the NotificationProvider abstract interface."""
    
    def test_abstract_methods(self):
        """Test that NotificationProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            NotificationProvider()
    
    def test_concrete_implementation_required_methods(self):
        """Test that concrete implementations must implement all abstract methods."""
        
        class IncompleteProvider(NotificationProvider):
            # Missing both abstract methods
            pass
        
        with pytest.raises(TypeError):
            IncompleteProvider()
        
        class CompleteProvider(NotificationProvider):
            def send(self, request):
                return NotificationResult(
                    request_id=request.id,
                    status=NotificationStatus.SENT,
                    channel_used=request.channel,
                    sent_at=datetime.now(timezone.utc)
                )
            
            def supports_channel(self, channel):
                return True
        
        # Should not raise exception
        provider = CompleteProvider()
        assert provider is not None


if __name__ == "__main__":
    pytest.main([__file__])
