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

from pydantic import ValidationError # Ensure ValidationError is imported

from core.base_agent_abc import AgentCapability, BaseAgent
from core.events.event_models import MaintenanceScheduledEvent
from data.schemas import NotificationChannel, NotificationRequest, NotificationResult, NotificationStatus
from data.exceptions import (
    AgentProcessingError, WorkflowError, ConfigurationError,
    SmartMaintenanceBaseException, ServiceUnavailableError, DataValidationException
)

# Get a logger for this module
logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""
    
    @abstractmethod
    def send(self, request: NotificationRequest) -> NotificationResult:
        """Send a notification. Raise ServiceUnavailableError or other specific errors on failure."""
        pass
    
    @abstractmethod
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """Check if this provider supports the given notification channel."""
        pass


class ConsoleNotificationProvider(NotificationProvider):
    """Console-based notification provider for development and testing."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ConsoleNotificationProvider")
        self.logger.info("ConsoleNotificationProvider initialized")
    
    def send(self, request: NotificationRequest) -> NotificationResult:
        """Send a notification to the console."""
        try:
            separator = "=" * 80
            output = f"\n{separator}\n🔔 MAINTENANCE NOTIFICATION\n{separator}\n" \
                     f"📧 To: {request.recipient}\n📋 Subject: {request.subject}\n" \
                     f"⚡ Priority: {request.priority}\n📅 Sent: {datetime.now(timezone.utc).isoformat()}\n\n" \
                     f"💬 Message:\n{request.message}\n\n" \
                     f"📎 Metadata:\n{self._format_metadata(request.metadata)}\n{separator}\n"
            print(output)
            self.logger.info(f"Console notification sent to {request.recipient}: {request.subject}")
            return NotificationResult(
                request_id=request.id, status=NotificationStatus.SENT,
                channel_used=NotificationChannel.CONSOLE, sent_at=datetime.now(timezone.utc),
                delivered_at=datetime.now(timezone.utc), provider_response={"console_output": "success"},
                metadata={"output_length": len(output)}
            )
        except Exception as e: # Catch any exception during console output generation or printing
            error_msg = f"Failed to send console notification: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # For console provider, this is likely an internal error, not a service being unavailable.
            # However, to align with the idea that providers might fail, we can use AgentProcessingError
            # or a more specific internal error if defined. Here, just returning FAILED.
            # If this were a real external service, ServiceUnavailableError would be appropriate.
            return NotificationResult(
                request_id=request.id, status=NotificationStatus.FAILED,
                channel_used=NotificationChannel.CONSOLE, sent_at=datetime.now(timezone.utc),
                error_message=error_msg, provider_response={"error": str(e)}
            ) # No custom exception raised here, just FAILED result as per original logic
    
    def supports_channel(self, channel: NotificationChannel) -> bool:
        return channel == NotificationChannel.CONSOLE
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        if not metadata: return "  (none)"
        return "\n".join([f"  • {key}: {value}" for key, value in metadata.items()])


class NotificationAgent(BaseAgent):
    """Agent for sending notifications based on system events."""
    
    def __init__(self, agent_id: str, event_bus: Any):
        super().__init__(agent_id, event_bus)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self._initialize_providers()
        self.templates = self._initialize_templates()
        self.status = "initialized"
        self.logger.info(f"NotificationAgent {agent_id} initialized")
    
    def _initialize_providers(self) -> None:
        try:
            console_provider = ConsoleNotificationProvider()
            self.providers[NotificationChannel.CONSOLE] = console_provider
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize notification providers: {e}", original_exception=e) from e
        self.logger.info(f"Initialized {len(self.providers)} notification providers")
    
    def _initialize_templates(self) -> Dict[str, str]:
        # If templates were loaded from files, this could raise ConfigurationError
        return {
            "maintenance_scheduled": "🔧 Maintenance Scheduled for {equipment_id}...\nHello {technician_name}...", # Truncated for brevity
            "maintenance_failed_to_schedule": "⚠️ Maintenance Scheduling Failed for {equipment_id}...\nAttention Supervisor...",
            "maintenance_rescheduled": "📅 Maintenance Rescheduled for {equipment_id}...\nHello {technician_name}...",
        } # Keeping templates short for this example. Real templates are longer.
    
    async def start(self) -> None:
        await super().start() # Includes capability registration
        # Changed to use MaintenanceScheduledEvent.__name__ for consistency
        await self.event_bus.subscribe(MaintenanceScheduledEvent.__name__, self.handle_maintenance_scheduled_event)
        self.logger.info(f"NotificationAgent {self.agent_id} subscribed to {MaintenanceScheduledEvent.__name__}")
    
    async def register_capabilities(self) -> None:
        capabilities = [
            AgentCapability(name="maintenance_notifications", description="Sends notifications for maintenance events",
                            input_types=[MaintenanceScheduledEvent.__name__], output_types=["NotificationResult"]),
            AgentCapability(name="multi_channel_delivery", description="Delivers via multiple channels",
                            input_types=["NotificationRequest"], output_types=["NotificationResult"])
        ]
        self.capabilities.extend(capabilities)
        self.logger.info(f"Registered {len(capabilities)} capabilities for {self.agent_id}")
    
    async def handle_maintenance_scheduled_event(self, event_type_or_event: Union[str, MaintenanceScheduledEvent], data: Optional[MaintenanceScheduledEvent] = None) -> None:
        """Handles MaintenanceScheduledEvent. Errors raised here will be caught by BaseAgent.handle_event."""
        event = data if isinstance(event_type_or_event, str) else event_type_or_event
        _event_id_for_log = getattr(event, 'event_id', 'N/A')
        _equipment_id_for_log = getattr(event, 'equipment_id', 'N/A')
        self.logger.info(f"Received {MaintenanceScheduledEvent.__name__} for equipment {_equipment_id_for_log} (Event ID: {_event_id_for_log})")

        if not isinstance(event, MaintenanceScheduledEvent):
            # Validate that the event object is of the expected type, if it was passed directly
            # This case might be less common if event bus always sends (type_name, data_dict)
            self.logger.error(f"Invalid event type: expected MaintenanceScheduledEvent, got {type(event)}. Event ID: {_event_id_for_log}")
            # Not raising custom error here as it's more of an internal type check / guard.
            # BaseAgent.handle_event might log it as a generic error if process() fails due to this.
            return

        try:
            # _create_maintenance_notification_request can raise ConfigurationError or WorkflowError
            notification_request = self._create_maintenance_notification_request(event)
            
            # send_notification can raise ConfigurationError or ServiceUnavailableError (from provider)
            result = await self.send_notification(notification_request)
            
            self.logger.info(f"Notification for event {_event_id_for_log} (equip: {_equipment_id_for_log}): {result.status}")
            
        except (ConfigurationError, WorkflowError, ServiceUnavailableError, DataValidationException) as app_exc:
            # Re-raise application-specific errors to be caught by BaseAgent.handle_event
            self.logger.error(f"Application error handling {MaintenanceScheduledEvent.__name__} for event {_event_id_for_log}: {app_exc}", exc_info=False)
            raise
        except Exception as e:
            # Wrap unexpected errors in AgentProcessingError
            self.logger.error(f"Generic error handling {MaintenanceScheduledEvent.__name__} for event {_event_id_for_log}: {e}", exc_info=True)
            raise AgentProcessingError(
                message=f"Generic error handling {MaintenanceScheduledEvent.__name__} for event {_event_id_for_log}: {str(e)}",
                original_exception=e
            ) from e

    def _create_maintenance_notification_request(self, event: MaintenanceScheduledEvent) -> NotificationRequest:
        """Creates NotificationRequest. Can raise DataValidationException or ConfigurationError."""
        try:
            schedule_details = event.schedule_details
            equipment_id = event.equipment_id
            recipient = f"technician_{event.assigned_technician_id or 'unassigned'}"
            
            template_id = "maintenance_scheduled" if event.assigned_technician_id and event.scheduled_start_time else "maintenance_failed_to_schedule"
            subject = f"🔧 Maint Sched: {equipment_id}" if template_id == "maintenance_scheduled" else f"⚠️ Maint Sched Fail: {equipment_id}"
            priority = 2 if template_id == "maintenance_scheduled" else 1

            template_data = {
                "equipment_id": equipment_id, "technician_name": f"Tech {event.assigned_technician_id or 'TBD'}",
                "scheduled_start_time": event.scheduled_start_time.strftime("%Y-%m-%d %H:%M") if event.scheduled_start_time else "TBD",
                "scheduled_end_time": event.scheduled_end_time.strftime("%Y-%m-%d %H:%M") if event.scheduled_end_time else "TBD",
                "priority": schedule_details.get("priority", "Medium"),
                "task_description": schedule_details.get("task_description", "N/A"),
                # ... other fields from original, kept brief here
            }
            message = self._render_template(template_id, template_data) # Can raise ConfigurationError

            return NotificationRequest(
                id=str(uuid.uuid4()), recipient=recipient, channel=NotificationChannel.CONSOLE,
                subject=subject, message=message, priority=priority, template_id=template_id,
                template_data=template_data, metadata={"event_id": str(event.event_id)}
            )
        except DataValidationException: # If NotificationRequest Pydantic validation fails
            raise
        except ConfigurationError: # If _render_template fails due to missing template config
            raise
        except Exception as e: # Other unexpected errors
            raise WorkflowError(f"Failed to create notification request for event {event.event_id}: {e}", original_exception=e) from e
    
    def _render_template(self, template_id: str, template_data: Dict[str, Any]) -> str:
        """Render template. Raise ConfigurationError on failure."""
        template = self.templates.get(template_id)
        if not template:
            raise ConfigurationError(f"Notification template '{template_id}' not found.")
        try:
            return template.format(**template_data)
        except KeyError as e:
            raise ConfigurationError(
                f"Missing data for template '{template_id}': key {e} not found in {list(template_data.keys())}",
                original_exception=e
            ) from e
    
    async def send_notification(self, request: NotificationRequest) -> NotificationResult:
        """Send notification. Raise ConfigurationError or allow provider errors (e.g. ServiceUnavailableError) to pass."""
        provider = self.providers.get(request.channel)
        if not provider:
            raise ConfigurationError(f"No notification provider configured for channel {request.channel.value}")
        
        self.logger.info(f"Sending notification {request.id} via {request.channel.value} to {request.recipient}")
        try:
            # Provider's send method should handle its own errors and return NotificationResult,
            # or raise specific exceptions like ServiceUnavailableError.
            result = provider.send(request)
        except SmartMaintenanceBaseException: # Let our specific exceptions pass through
            raise
        except Exception as e: # Wrap unexpected provider errors
            self.logger.error(f"Unexpected error from provider for channel {request.channel.value}: {e}", exc_info=True)
            raise ServiceUnavailableError(
                f"Provider for channel {request.channel.value} failed unexpectedly: {str(e)}",
                original_exception=e
            ) from e

        if result.status == NotificationStatus.FAILED:
            self.logger.warning(f"Notification {request.id} failed: {result.error_message}")
        else:
            self.logger.info(f"Notification {request.id} sent successfully via {request.channel.value}")
        return result
    
    async def process(self, data: Any) -> Any:
        """Main processing logic. Errors raised here will be caught by BaseAgent.handle_event."""
        _data_type_for_log = type(data).__name__
        self.logger.info(f"NotificationAgent {self.agent_id} processing data of type: {_data_type_for_log}")
        
        try:
            if isinstance(data, NotificationRequest):
                return await self.send_notification(data)
            elif isinstance(data, MaintenanceScheduledEvent): # If full event object is passed
                 await self.handle_maintenance_scheduled_event(MaintenanceScheduledEvent.__name__, data) # Adapt to expected handler signature
                 return None
            elif isinstance(data, dict) and "schedule_details" in data and "equipment_id" in data : # Heuristic for event data dict
                try:
                    event_obj = MaintenanceScheduledEvent(**data)
                    await self.handle_maintenance_scheduled_event(MaintenanceScheduledEvent.__name__, event_obj)
                    return None
                except ValidationError as ve:
                    raise DataValidationException(f"Could not parse generic dict data as MaintenanceScheduledEvent: {ve}", errors=ve.errors(), original_exception=ve) from ve
            else:
                self.logger.warning(f"NotificationAgent {self.agent_id}: Unknown data type for processing: {_data_type_for_log}")
                # Consider raising an AgentProcessingError if this is unexpected
                raise AgentProcessingError(f"Unsupported data type for NotificationAgent: {_data_type_for_log}")
        except (DataValidationException, ConfigurationError, WorkflowError, ServiceUnavailableError) as app_exc:
            self.logger.error(f"Application error in NotificationAgent.process: {app_exc}", exc_info=False)
            raise
        except Exception as e:
            self.logger.error(f"Generic unhandled error in NotificationAgent.process for data type {_data_type_for_log}: {e}", exc_info=True)
            raise AgentProcessingError(
                f"Generic unhandled error processing data type {_data_type_for_log}: {str(e)}",
                original_exception=e
            ) from e

    # Stop and get_health methods remain largely unchanged from original, not directly impacted by these error handling changes.
    async def stop(self) -> None:
        await super().stop()
    
    async def get_health(self) -> Dict[str, Any]:
        base_health = await super().get_health()
        base_health.update({
            "providers_count": len(self.providers),
            "available_channels": [channel.value for channel in self.providers.keys()],
            "templates_count": len(self.templates),
        })
        return base_health
