import abc
import datetime
from dataclasses import dataclass, field
from typing import Any, List

from core.events.event_bus import EventBus


@dataclass
class AgentCapability:
    """
    Represents a capability of an agent.

    Attributes:
        name: The name of the capability.
        description: A description of what the capability does.
        input_types: A list of strings representing the expected input data types.
        output_types: A list of strings representing the output data types.
    """
    name: str
    description: str
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)


class BaseAgent(abc.ABC):
    """
    Abstract base class for all agents.

    Attributes:
        agent_id: A unique identifier for the agent.
        event_bus: An instance of the EventBus for communication.
        status: The current status of the agent (e.g., "initializing", "running", "stopped").
        capabilities: A list of AgentCapability objects representing what the agent can do.
    """

    def __init__(self, agent_id: str, event_bus: EventBus):
        """
        Initializes the BaseAgent.

        Args:
            agent_id: The unique identifier for this agent.
            event_bus: The event bus instance for communication.
        """
        self.agent_id: str = agent_id
        self.event_bus: EventBus = event_bus
        self.status: str = "initializing"
        self.capabilities: List[AgentCapability] = []
        print(f"Agent {self.agent_id} initialized.")

    @abc.abstractmethod
    async def process(self, data: Any) -> Any:
        """
        Process data received by the agent.
        This method must be implemented by subclasses.

        Args:
            data: The data to be processed.

        Returns:
            The result of the processing.
        """
        pass

    async def start(self) -> None:
        """
        Starts the agent.
        Sets the status to "running" and registers its capabilities.
        """
        self.status = "running"
        await self.register_capabilities()
        print(f"Agent {self.agent_id} started.")

    async def stop(self) -> None:
        """
        Stops the agent.
        Sets the status to "stopped".
        """
        self.status = "stopped"
        print(f"Agent {self.agent_id} stopped.")

    async def register_capabilities(self) -> None:
        """
        Registers the capabilities of the agent.
        This method should be overridden by subclasses to populate self.capabilities.
        """
        # Example capability, subclasses should define their own
        # self.capabilities.append(
        #     AgentCapability(
        #         name="example_capability",
        #         description="Processes example data.",
        #         input_types=["str"],
        #         output_types=["str"]
        #     )
        # )
        print(f"Agent {self.agent_id} registered capabilities (if any).")

    async def handle_event(self, event_type: str, data: Any) -> None:
        """
        Handles an event received from the event bus.
        This is a generic handler; subclasses might want to override it for specific event types.

        Args:
            event_type: The type of the event.
            data: The data associated with the event.
        """
        print(f"Agent {self.agent_id} received event: {event_type} with data: {data}")
        # Example: route to process method if it's a known capability event
        # for cap in self.capabilities:
        #     if event_type == cap.name: # Or some other mapping
        #         await self.process(data)
        #         break

    async def get_health(self) -> dict:
        """
        Returns the health status of the agent.

        Returns:
            A dictionary containing the agent_id, status, and current timestamp.
        """
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

    async def _publish_event(self, event_type: str, data: Any) -> None:
        """
        Helper method to publish an event to the event bus.

        Args:
            event_type: The type of the event to publish.
            data: The data to publish with the event.
        """
        if self.event_bus:
            await self.event_bus.publish(event_type, data)
            print(f"Agent {self.agent_id} published event: {event_type}")
        else:
            print(f"Agent {self.agent_id} event bus not configured. Cannot publish event: {event_type}")
