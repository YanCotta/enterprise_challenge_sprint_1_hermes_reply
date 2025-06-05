"""
NotificationAgent implementation for sending notifications based on system events.

This agent handles notification delivery through various channels (console, email, SMS, etc.)
based on maintenance scheduling events and other system events.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apps.agents.base_agent import AgentCapability, BaseAgent
from core.events.event_models import MaintenanceScheduledEvent
from data.schemas import NotificationChannel, NotificationRequest, NotificationResult, NotificationStatus

# Get a logger for this module
logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""
    
    @abstractmethod
    def send(self, request: NotificationRequest) -> NotificationResult:
        """
        Send a notification through this provider.
        
        Args:
            request: The notification request to send
            
        Returns:
            NotificationResult with delivery status and details
        """
        pass
    
    @abstractmethod
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """
        Check if this provider supports the given notification channel.
        
        Args:
            channel: The notification channel to check
            
        Returns:
            True if the channel is supported, False otherwise
        """
        pass


class ConsoleNotificationProvider(NotificationProvider):
    """Console-based notification provider for development and testing."""
    
    def __init__(self):
        """Initialize the console notification provider."""
        self.logger = logging.getLogger(f"{__name__}.ConsoleNotificationProvider")
        self.logger.info("ConsoleNotificationProvider initialized")
    
    def send(self, request: NotificationRequest) -> NotificationResult:
        """
        Send a notification to the console.
        
        Args:
            request: The notification request to send
            
        Returns:
            NotificationResult with delivery status
        """
        try:
            # Format the console output
            separator = "=" * 80
            output = f"""
{separator}
🔔 MAINTENANCE NOTIFICATION
{separator}
📧 To: {request.recipient}
📋 Subject: {request.subject}
⚡ Priority: {request.priority} (1=highest, 5=lowest)
📅 Sent: {datetime.now(timezone.utc).isoformat()}

💬 Message:
{request.message}

📎 Metadata:
{self._format_metadata(request.metadata)}
{separator}
"""
            
            # Print to console
            print(output)
            
            # Log the notification
            self.logger.info(f"Console notification sent to {request.recipient}: {request.subject}")
            
            # Create successful result
            result = NotificationResult(
                request_id=request.id,
                status=NotificationStatus.SENT,
                channel_used=NotificationChannel.CONSOLE,
                sent_at=datetime.now(timezone.utc),
                delivered_at=datetime.now(timezone.utc),  # Console delivery is immediate
                provider_response={"console_output": "success"},
                metadata={"output_length": len(output)}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to send console notification: {str(e)}"
            self.logger.error(error_msg)
            
            return NotificationResult(
                request_id=request.id,
                status=NotificationStatus.FAILED,
                channel_used=NotificationChannel.CONSOLE,
                sent_at=datetime.now(timezone.utc),
                error_message=error_msg,
                provider_response={"error": str(e)}
            )
    
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """Check if this provider supports the given channel."""
        return channel == NotificationChannel.CONSOLE
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for console display."""
        if not metadata:
            return "  (none)"
        
        formatted_lines = []
        for key, value in metadata.items():
            formatted_lines.append(f"  • {key}: {value}")
        
        return "\n".join(formatted_lines)


class NotificationAgent(BaseAgent):
    """
    Agent responsible for sending notifications based on system events.
    
    This agent listens for maintenance scheduling events and sends appropriate
    notifications to technicians, supervisors, and other stakeholders.
    """
    
    def __init__(self, agent_id: str, event_bus: Any):
        """
        Initialize the NotificationAgent.
        
        Args:
            agent_id: Unique identifier for this agent
            event_bus: Event bus instance for communication
        """
        super().__init__(agent_id, event_bus)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Initialize notification providers
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self._initialize_providers()
        
        # Notification templates
        self.templates = self._initialize_templates()
        
        self.status = "initialized"  # Override the BaseAgent's "initializing" status
        self.logger.info(f"NotificationAgent {agent_id} initialized")
    
    def _initialize_providers(self) -> None:
        """Initialize notification providers."""
        # Add console provider (for development/testing)
        console_provider = ConsoleNotificationProvider()
        self.providers[NotificationChannel.CONSOLE] = console_provider
        
        # Future providers can be added here:
        # - EmailNotificationProvider
        # - SMSNotificationProvider
        # - WhatsAppNotificationProvider
        # - SlackNotificationProvider
        
        self.logger.info(f"Initialized {len(self.providers)} notification providers")
    
    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize notification message templates."""
        return {
            "maintenance_scheduled": """🔧 Maintenance Scheduled for {equipment_id}

Hello {technician_name},

A maintenance task has been scheduled for equipment {equipment_id}.

📋 Details:
• Equipment: {equipment_id}
• Scheduled Time: {scheduled_start_time} - {scheduled_end_time}
• Priority: {priority}
• Estimated Duration: {estimated_duration} hours
• Location: {location}

📝 Task Description:
{task_description}

🛠️ Required Skills:
{required_skills}

📦 Parts/Materials:
{parts_needed}

Please confirm your availability and report to the maintenance area at the scheduled time.

Thank you,
Smart Maintenance System
""",
            
            "maintenance_failed_to_schedule": """⚠️ Maintenance Scheduling Failed for {equipment_id}

Attention Maintenance Supervisor,

Failed to schedule maintenance for equipment {equipment_id}.

❌ Reason: {failure_reason}
🚨 Priority: {priority}
⏰ Requested Time: {requested_time}

Please review the scheduling constraints and assign manually if needed.

Smart Maintenance System
""",
            
            "maintenance_rescheduled": """📅 Maintenance Rescheduled for {equipment_id}

Hello {technician_name},

The maintenance task for equipment {equipment_id} has been rescheduled.

🔄 New Schedule:
• From: {old_scheduled_time}
• To: {new_scheduled_time}

📋 Task remains the same:
{task_description}

Please update your calendar accordingly.

Smart Maintenance System
"""
        }
    
    async def start(self) -> None:
        """Start the NotificationAgent and subscribe to relevant events."""
        self.status = "starting"
        self.logger.info(f"Agent {self.agent_id} starting...")
        
        # Register capabilities
        await self.register_capabilities()
        
        # Subscribe to events
        await self.event_bus.subscribe("MaintenanceScheduledEvent", self.handle_maintenance_scheduled_event)
        self.logger.info(f"NotificationAgent {self.agent_id} subscribed to MaintenanceScheduledEvent")
        
        self.status = "running"
        self.logger.info(f"Agent {self.agent_id} started successfully. Status: {self.status}")
    
    async def register_capabilities(self) -> None:
        """Register the agent's capabilities."""
        capabilities = [
            AgentCapability(
                name="maintenance_notifications",
                description="Sends notifications for maintenance scheduling events",
                input_types=["MaintenanceScheduledEvent"],
                output_types=["NotificationRequest", "NotificationResult"]
            ),
            AgentCapability(
                name="multi_channel_delivery",
                description="Delivers notifications through multiple channels (console, email, SMS, etc.)",
                input_types=["NotificationRequest"],
                output_types=["NotificationResult"]
            )
        ]
        
        self.capabilities.extend(capabilities)
        self.logger.info(f"Registered {len(capabilities)} capabilities for {self.agent_id}")
    
    async def handle_maintenance_scheduled_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle MaintenanceScheduledEvent by sending appropriate notifications.
        
        Args:
            event_data: The maintenance scheduled event data
        """
        try:
            # Parse the event
            event = MaintenanceScheduledEvent(**event_data)
            self.logger.info(f"Received MaintenanceScheduledEvent for equipment {event.equipment_id}")
            
            # Create notification request from the event
            notification_request = self._create_maintenance_notification_request(event)
            
            # Send the notification
            result = await self.send_notification(notification_request)
            
            self.logger.info(f"Notification sent for equipment {event.equipment_id}: {result.status}")
            
        except Exception as e:
            error_msg = f"Error handling MaintenanceScheduledEvent: {str(e)}"
            self.logger.error(error_msg)
            # Agent continues running despite error
    
    def _create_maintenance_notification_request(self, event: MaintenanceScheduledEvent) -> NotificationRequest:
        """
        Create a NotificationRequest from a MaintenanceScheduledEvent.
        
        Args:
            event: The maintenance scheduled event
            
        Returns:
            NotificationRequest with notification details
        """
        # Extract schedule details
        schedule_details = event.schedule_details
        equipment_id = event.equipment_id
        
        # Determine recipient (for demo purposes, use a mock technician)
        recipient = f"technician_{event.assigned_technician_id or 'unassigned'}"
        
        # Determine notification type based on scheduling success
        if event.assigned_technician_id and event.scheduled_start_time:
            # Successful scheduling
            template_id = "maintenance_scheduled"
            subject = f"🔧 Maintenance Scheduled: {equipment_id}"
            priority = 2  # High priority for scheduled maintenance
        else:
            # Failed scheduling
            template_id = "maintenance_failed_to_schedule"
            subject = f"⚠️ Maintenance Scheduling Failed: {equipment_id}"
            priority = 1  # Highest priority for failures
        
        # Create template data
        template_data = {
            "equipment_id": equipment_id,
            "technician_name": f"Technician {event.assigned_technician_id or 'TBD'}",
            "scheduled_start_time": event.scheduled_start_time.strftime("%Y-%m-%d %H:%M") if event.scheduled_start_time else "TBD",
            "scheduled_end_time": event.scheduled_end_time.strftime("%Y-%m-%d %H:%M") if event.scheduled_end_time else "TBD",
            "priority": schedule_details.get("priority", "Medium"),
            "estimated_duration": schedule_details.get("estimated_duration_hours", "Unknown"),
            "location": schedule_details.get("location", "Main Facility"),
            "task_description": schedule_details.get("task_description", "Maintenance task as scheduled"),
            "required_skills": ", ".join(schedule_details.get("required_skills", [])) or "General maintenance",
            "parts_needed": ", ".join(schedule_details.get("parts_needed", [])) or "None specified",
            "failure_reason": ", ".join(event.constraints_violated) if event.constraints_violated else "Unknown",
            "requested_time": event.scheduled_start_time.strftime("%Y-%m-%d %H:%M") if event.scheduled_start_time else "Unknown"
        }
        
        # Render message from template
        message = self._render_template(template_id, template_data)
        
        # Create notification request
        request = NotificationRequest(
            id=str(uuid.uuid4()),
            recipient=recipient,
            channel=NotificationChannel.CONSOLE,  # Using console for demo
            subject=subject,
            message=message,
            priority=priority,
            template_id=template_id,
            template_data=template_data,
            metadata={
                "event_id": str(event.event_id),
                "equipment_id": equipment_id,
                "scheduling_method": event.scheduling_method,
                "optimization_score": event.optimization_score
            }
        )
        
        return request
    
    def _render_template(self, template_id: str, template_data: Dict[str, Any]) -> str:
        """
        Render a notification message from template.
        
        Args:
            template_id: ID of the template to use
            template_data: Data for template rendering
            
        Returns:
            Rendered message string
        """
        template = self.templates.get(template_id)
        if not template:
            return f"No template found for {template_id}. Data: {template_data}"
        
        try:
            return template.format(**template_data)
        except KeyError as e:
            self.logger.warning(f"Missing template data key {e} for template {template_id}")
            return f"Template rendering failed for {template_id}. Missing key: {e}"
    
    async def send_notification(self, request: NotificationRequest) -> NotificationResult:
        """
        Send a notification using the appropriate provider.
        
        Args:
            request: The notification request to send
            
        Returns:
            NotificationResult with delivery status
        """
        # Find appropriate provider for the channel
        provider = self.providers.get(request.channel)
        
        if not provider:
            error_msg = f"No provider available for channel {request.channel}"
            self.logger.error(error_msg)
            
            return NotificationResult(
                request_id=request.id,
                status=NotificationStatus.FAILED,
                channel_used=request.channel,
                sent_at=datetime.now(timezone.utc),
                error_message=error_msg,
                provider_response={"error": "provider_not_found"}
            )
        
        # Send notification
        self.logger.info(f"Sending notification {request.id} via {request.channel} to {request.recipient}")
        result = provider.send(request)
        
        # Log result
        if result.status == NotificationStatus.SENT:
            self.logger.info(f"Notification {request.id} sent successfully")
        else:
            self.logger.warning(f"Notification {request.id} failed: {result.error_message}")
        
        return result
    
    async def stop(self) -> None:
        """Stop the NotificationAgent."""
        self.status = "stopping"
        self.logger.info(f"Agent {self.agent_id} stopping...")
        
        # Clean up providers if needed
        for provider in self.providers.values():
            if hasattr(provider, 'cleanup'):
                provider.cleanup()
        
        # Call parent stop method
        await super().stop()
    
    async def get_health(self) -> Dict[str, Any]:
        """
        Get the health status of the NotificationAgent.
        
        Returns:
            Dictionary containing health information
        """
        base_health = await super().get_health()
        base_health.update({
            "providers_count": len(self.providers),
            "available_channels": [channel.value for channel in self.providers.keys()],
            "templates_count": len(self.templates),
            "capabilities_count": len(self.capabilities)
        })
        return base_health
    
    async def process(self, data: Any) -> Any:
        """
        Main processing logic for notification requests.
        
        This method handles generic data processing for the notification agent.
        For event-specific handling, use the specific event handlers like
        handle_maintenance_scheduled_event.
        
        Args:
            data: The data to be processed
            
        Returns:
            Processing result or None
        """
        self.logger.info(f"NotificationAgent {self.agent_id} processing data: {type(data)}")
        
        # If data is a NotificationRequest, send it directly
        if isinstance(data, NotificationRequest):
            return await self.send_notification(data)
        
        # If data is a MaintenanceScheduledEvent dict, handle it
        if isinstance(data, dict) and "equipment_id" in data:
            await self.handle_maintenance_scheduled_event(data)
            return None
        
        # For other data types, log and return None
        self.logger.warning(f"NotificationAgent {self.agent_id}: Unknown data type for processing: {type(data)}")
        return None
