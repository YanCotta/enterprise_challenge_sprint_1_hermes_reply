"""Base agent module providing core functionality for all AI agents in the system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timezone # Add timezone
import logging # Ensure logging is imported

# Get a logger for this module
logger = logging.getLogger(__name__)

@dataclass
class AgentCapability:
    """Defines the structure for an agent's capability."""
    name: str
    description: str
    input_types: List[str] = field(default_factory=list)  # e.g., event types or data model names
    output_types: List[str] = field(default_factory=list) # e.g., event types or data model names

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Smart Maintenance SaaS system.
    Provides common lifecycle methods, event handling, capability registration,
    and health check functionalities.
    """
    def __init__(self, agent_id: str, event_bus: Any): # event_bus is an instance of our EventBus
        """
        Initializes the BaseAgent.

        Args:
            agent_id (str): A unique identifier for the agent.
            event_bus (Any): An instance of the system's EventBus for inter-agent communication.
        """
        self.agent_id: str = agent_id
        self.event_bus: Any = event_bus
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
        # Subclasses should call self.event_bus.subscribe() here for events they need to listen to.
        self.status = "running"
        logger.info(f"Agent {self.agent_id} started successfully. Status: {self.status}")

    async def stop(self) -> None:
        """
        Stops the agent and sets its status to "stopped". Subclasses can override
        this to add specific shutdown logic (e.g., releasing resources, unsubscribing
        from events) but should call super().stop().
        """
        logger.info(f"Agent {self.agent_id} stopping...")
        # Subclasses might unsubscribe from events here.
        self.status = "stopped"
        logger.info(f"Agent {self.agent_id} stopped. Status: {self.status}")

    async def register_capabilities(self) -> None:
        """
        Placeholder method for subclasses to register their specific capabilities.
        This method should be overridden by agent implementations to populate
        the `self.capabilities` list with `AgentCapability` objects.
        """
        # Example for a subclass:
        # self.capabilities.append(
        #     AgentCapability(
        #         name="data_validation",
        #         description="Validates incoming sensor data against predefined schemas.",
        #         input_types=["SensorDataReceivedEvent"],
        #         output_types=["DataProcessedEvent"]
        #     )
        # )
        logger.debug(f"Agent {self.agent_id}: No specific capabilities registered in BaseAgent.register_capabilities.")
        pass

    async def handle_event(self, event_type: str, data: Any) -> None:
        """
        Default event handler. When an agent subscribes to an event using this
        method as the handler, this method will be called.
        By default, it logs the event and calls the agent's main `process` method.
        Subclasses can override this for more specific event routing if needed.

        Args:
            event_type (str): The type of the event received.
            data (Any): The payload of the event.
        """
        logger.info(f"Agent {self.agent_id} received event '{event_type}' with data: {str(data)[:200]}...") # Log first 200 chars
        try:
            await self.process(data)
        except Exception as e:
            logger.error(f"Agent {self.agent_id}: Error processing event '{event_type}': {e}", exc_info=True)
            # Optionally, publish an error event
            # await self._publish_event("agent_processing_error", {"agent_id": self.agent_id, "event_type": event_type, "error": str(e)})


    async def get_health(self) -> Dict[str, Any]:
        """
        Returns the current health status of the agent.

        Returns:
            Dict[str, Any]: A dictionary containing the agent's ID, status, and current timestamp.
        """
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def _publish_event(self, event_type: str, data: Any) -> None:
        """
        Helper method to publish an event via the configured event bus.

        Args:
            event_type (str): The type of the event to publish.
            data (Any): The payload of the event.
        """
        if self.event_bus:
            logger.debug(f"Agent {self.agent_id} publishing event '{event_type}'...")
            try:
                await self.event_bus.publish(event_type, data)
                logger.info(f"Agent {self.agent_id} successfully published event '{event_type}'.")
            except Exception as e:
                logger.error(f"Agent {self.agent_id}: Failed to publish event '{event_type}': {e}", exc_info=True)
        else:
            logger.warning(f"Agent {self.agent_id}: Event bus not available. Cannot publish event '{event_type}'.")
