import logging
from typing import Dict, Optional

from apps.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    A singleton registry for managing agent instances.

    This class provides a centralized way to register, unregister,
    and retrieve agent instances within the application.
    """

    _instance: Optional["AgentRegistry"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> "AgentRegistry":
        """
        Ensures that only one instance of AgentRegistry is created.
        """
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initializes the AgentRegistry.
        This constructor will only run its initialization logic once.
        """
        if AgentRegistry._initialized:
            return
        self.agents: Dict[str, BaseAgent] = {}
        AgentRegistry._initialized = True
        logger.info("AgentRegistry initialized.")

    def register_agent(self, agent_id: str, agent_instance: BaseAgent) -> None:
        """
        Registers an agent instance with the registry.

        Args:
            agent_id: The unique identifier for the agent.
            agent_instance: The instance of the agent to register.

        Raises:
            ValueError: If an agent with the same ID is already registered.
        """
        if agent_id in self.agents:
            logger.error(f"Agent with ID '{agent_id}' is already registered.")
            raise ValueError(f"Agent with ID '{agent_id}' is already registered.")
        self.agents[agent_id] = agent_instance
        logger.info(f"Agent '{agent_id}' registered.")

    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregisters an agent instance from the registry.

        Args:
            agent_id: The unique identifier for the agent to unregister.

        Raises:
            ValueError: If no agent with the given ID is found.
        """
        if agent_id not in self.agents:
            logger.error(f"Agent with ID '{agent_id}' not found for unregistration.")
            raise ValueError(
                f"Agent with ID '{agent_id}' not found for unregistration."
            )
        del self.agents[agent_id]
        logger.info(f"Agent '{agent_id}' unregistered.")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Retrieves an agent instance from the registry.

        Args:
            agent_id: The unique identifier for the agent to retrieve.

        Returns:
            The agent instance if found, otherwise None.
        """
        agent = self.agents.get(agent_id)
        if agent:
            logger.info(f"Agent '{agent_id}' retrieved.")
        else:
            logger.warning(f"Agent '{agent_id}' not found.")
        return agent

    def list_agents(self) -> Dict[str, BaseAgent]:
        """
        Lists all registered agent instances.

        Returns:
            A dictionary mapping agent IDs to agent instances.
        """
        logger.info(f"Listing all {len(self.agents)} registered agents.")
        return self.agents.copy()


# Example of how to get the singleton instance:
# registry = AgentRegistry()
# registry2 = AgentRegistry()
# assert registry is registry2 # This should be true.
