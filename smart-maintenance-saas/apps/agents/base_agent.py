"""Base agent module providing core functionality for all AI agents in the system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

# Assuming event_models.py and other necessary modules are accessible
# from core.events.event_models import Event, AgentEvent
# from core.config.settings import settings


@dataclass
class AgentCapability:
    """
    Represents a specific capability of an agent, including its description,
    required parameters, and an optional method name to call for this capability.
    """
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    method_name: Optional[str] = None

    def __post_init__(self):
        if self.method_name is None:
            self.method_name = f"execute_{self.name.lower().replace(' ', '_')}"


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the Smart Maintenance SaaS platform.

    This class defines the common interface and core functionalities that all agents
    must implement. It includes lifecycle management, event handling, and capability
    registration.
    """

    def __init__(self, agent_id: Optional[UUID] = None, name: Optional[str] = None, description: Optional[str] = None):
        self.agent_id: UUID = agent_id or uuid4()
        self.name: str = name or self.__class__.__name__
        self.description: str = description or self.__doc__ or "No description available."
        self.is_active: bool = False
        self.capabilities: List[AgentCapability] = self._register_capabilities()
        # self.event_bus = None # Will be set by the AgentRegistry or system

    def _register_capabilities(self) -> List[AgentCapability]:
        """
        Registers the capabilities of the agent.
        This method should be overridden by subclasses to define their specific capabilities.
        """
        return []

    def get_capability(self, name: str) -> Optional[AgentCapability]:
        """Retrieves a capability by its name."""
        for cap in self.capabilities:
            if cap.name == name:
                return cap
        return None

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initializes the agent, setting up any necessary resources or connections.
        This method is called once when the agent is first started.
        """
        self.is_active = True
        # Example: await self.event_bus.subscribe(f"agent.{self.agent_id}.command", self.handle_command)
        print(f"Agent {self.name} (ID: {self.agent_id}) initialized.")

    @abstractmethod
    async def execute_task(self, task_name: str, params: Dict[str, Any]) -> Any:
        """
        Executes a specific task based on the task name and parameters.
        This method allows agents to perform actions based on their capabilities.
        """
        capability = self.get_capability(task_name)
        if capability and hasattr(self, capability.method_name):
            method_to_call = getattr(self, capability.method_name)
            # Potentially validate params against capability.parameters schema here
            return await method_to_call(**params)
        else:
            raise NotImplementedError(f"Task '{task_name}' not implemented or capability method missing for agent {self.name}.")

    @abstractmethod
    async def process_event(self, event: Any) -> None: # Changed from Event to Any for now
        """
        Processes an incoming event from the event bus.
        Agents should implement this method to react to system events or messages from other agents.
        """
        print(f"Agent {self.name} (ID: {self.agent_id}) received event: {event}")

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shuts down the agent, releasing any resources.
        This method is called when the agent is being stopped.
        """
        self.is_active = False
        # Example: await self.event_bus.unsubscribe_all(self.handle_command)
        print(f"Agent {self.name} (ID: {self.agent_id}) shut down.")

    async def get_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the agent.
        """
        return {
            "agent_id": str(self.agent_id),
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "capabilities": [cap.__dict__ for cap in self.capabilities]
        }

    # Example of how a capability method might be defined:
    # async def execute_sample_capability(self, parameter1: str, parameter2: int) -> str:
    #     """Executes the sample capability."""
    #     print(f"Agent {self.name} executing sample_capability with {parameter1=}, {parameter2=}")
    #     return f"Sample capability executed with {parameter1} and {parameter2}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, name='{self.name}', active={self.is_active})>"
