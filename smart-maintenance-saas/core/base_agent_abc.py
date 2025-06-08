"""Core Abstract Base Class for agents."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

# Assuming 'data' is a top-level package sibling to 'core' and 'apps'
# and is structured to allow this import.
from data.exceptions import AgentProcessingError, SmartMaintenanceBaseException

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Defines the structure for an agent's capability."""

    name: str
    description: str
    input_types: List[str] = field(
        default_factory=list
    )  # e.g., event types or data model names
    output_types: List[str] = field(
        default_factory=list
    )  # e.g., event types or data model names


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Smart Maintenance SaaS system.
    Provides common lifecycle methods, event handling, capability registration,
    and health check functionalities.
    """

    def __init__(
        self, agent_id: str, event_bus: Any
    ):  # event_bus is an instance of our EventBus
        """
        Initializes the BaseAgent.

        Args:
            agent_id (str): A unique identifier for the agent.
            event_bus (Any): An instance of the system's EventBus for inter-agent communication.
        """
        self.agent_id: str = agent_id
        self.event_bus: Any = event_bus # Should be typed to EventBus ideally
        self.capabilities: List[AgentCapability] = []
        self.status: str = "initializing"
        logger.info(f"Agent {self.agent_id} initialized. Status: {self.status}")

    @abstractmethod
    async def process(self, data: Any) -> Any:
        """
        Main processing logic for the agent. This method MUST be implemented by subclasses.
        It's typically called by handle_event or other internal agent logic.

        Args:
            data (Any): The data to be processed by the agent.

        Returns:
            Any: The result of the processing, if applicable.
        """
        pass

    async def start(self) -> None:
        """
        Starts the agent, registers its capabilities, subscribes to relevant events,
        and sets its status to "running". Subclasses can override this to add
        specific startup logic (e.g., event subscriptions) but should call super().start().
        """
        logger.info(f"Agent {self.agent_id} starting...")
        await self.register_capabilities()
        self.status = "running"
        logger.info(
            f"Agent {self.agent_id} started successfully. Status: {self.status}"
        )

    async def stop(self) -> None:
        """
        Stops the agent and sets its status to "stopped". Subclasses can override
        this to add specific shutdown logic (e.g., releasing resources, unsubscribing
        from events) but should call super().stop().
        """
        logger.info(f"Agent {self.agent_id} stopping...")
        self.status = "stopped"
        logger.info(f"Agent {self.agent_id} stopped. Status: {self.status}")

    async def register_capabilities(self) -> None:
        """
        Placeholder method for subclasses to register their specific capabilities.
        """
        logger.debug(
            f"Agent {self.agent_id}: No specific capabilities registered in BaseAgent.register_capabilities."
        )
        pass

    async def handle_event(self, event_type: str, data: Any) -> None:
        """
        Default event handler.
        """
        logger.info(
            f"Agent {self.agent_id} received event '{event_type}' with data: {str(data)[:200]}..."
        )
        try:
            await self.process(data)
        except SmartMaintenanceBaseException as app_exc: # SmartMaintenanceBaseException is caught first
            logger.error(
                f"Agent {self.agent_id}: Application-specific error processing event '{event_type}': {app_exc}",
                exc_info=True,
            )
            if self.event_bus:
                error_event_payload = {
                    "agent_id": self.agent_id,
                    "failed_event_type": event_type,
                    "error_message": str(app_exc),
                    "error_class": app_exc.__class__.__name__,
                    "original_exception_message": str(app_exc.original_exception) if app_exc.original_exception else None,
                    "original_exception_class": app_exc.original_exception.__class__.__name__ if app_exc.original_exception else None,
                }
                try:
                    await self.event_bus.publish("AgentExceptionEvent", error_event_payload)
                except Exception as pub_exc:
                    logger.error(f"Agent {self.agent_id}: Failed to publish AgentExceptionEvent after app error: {pub_exc}", exc_info=True)

        except Exception as e: # Generic exceptions are caught last
            logger.error(
                f"Agent {self.agent_id}: Generic unhandled error processing event '{event_type}': {e}",
                exc_info=True,
            )
            if self.event_bus:
                error_event_payload = {
                    "agent_id": self.agent_id,
                    "failed_event_type": event_type,
                    "error_message": str(e),
                    "error_class": e.__class__.__name__,
                }
                try:
                    await self.event_bus.publish("AgentExceptionEvent", error_event_payload)
                except Exception as pub_exc:
                    logger.error(f"Agent {self.agent_id}: Failed to publish AgentExceptionEvent after generic error: {pub_exc}", exc_info=True)

    async def _publish_event(self, event_type: str, event_data: Any) -> None:
        """
        Helper method to publish events through the event bus.
        
        Args:
            event_type (str): The type of event to publish
            event_data (Any): The event data to publish
        """
        if self.event_bus:
            try:
                await self.event_bus.publish(event_type, event_data)
                logger.debug(f"Agent {self.agent_id}: Published {event_type} event")
            except Exception as e:
                logger.error(f"Agent {self.agent_id}: Failed to publish {event_type} event: {e}")
                raise
        else:
            logger.warning(f"Agent {self.agent_id}: No event bus available to publish {event_type} event")

    async def get_health(self) -> Dict[str, Any]:
        """
        Returns the current health status of the agent.
        """
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
