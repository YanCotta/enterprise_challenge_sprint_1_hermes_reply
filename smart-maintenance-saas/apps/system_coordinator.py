import logging
import asyncio # Make sure asyncio is imported
from typing import List, Callable, Optional, Dict, Any # Added Dict, Any for specific_settings
from datetime import datetime
from data.schemas import SensorReading, SensorReadingCreate, AnomalyAlert, SensorType

# Event Bus
from core.events.event_bus import EventBus

# Base Agent (though not directly instantiated, good for context if needed)
from core.base_agent_abc import BaseAgent

# Enhanced Golden Path Agent Imports
from apps.agents.core.data_acquisition_agent import DataAcquisitionAgent
from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from apps.agents.core.validation_agent import ValidationAgent
from apps.agents.core.notification_agent import EnhancedNotificationAgent
import os

# Additional Decision Layer Agents
from apps.agents.decision.prediction_agent import PredictionAgent
from apps.agents.core.orchestrator_agent import OrchestratorAgent
from apps.agents.decision.scheduling_agent import SchedulingAgent
from apps.agents.interface.human_interface_agent import HumanInterfaceAgent
from apps.agents.decision.reporting_agent import ReportingAgent

# Conditionally import LearningAgent only if ChromaDB is not disabled
if os.getenv('DISABLE_CHROMADB', '').lower() != 'true':
    try:
        from apps.agents.learning.learning_agent import LearningAgent
        LEARNING_AGENT_AVAILABLE = True
    except ImportError:
        LEARNING_AGENT_AVAILABLE = False
        LearningAgent = None
else:
    LEARNING_AGENT_AVAILABLE = False
    LearningAgent = None

from apps.agents.decision.maintenance_log_agent import MaintenanceLogAgent

# Real Service Imports
from data.validators.agent_data_validator import DataValidator
from data.processors.agent_data_enricher import DataEnricher
from core.database.crud.crud_sensor_reading import crud_sensor_reading
from core.database.crud.crud_maintenance_log import crud_maintenance_log
from apps.rules.validation_rules import RuleEngine
from core.database.session import AsyncSessionLocal

# Database related imports
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class SystemCoordinator:
    """
    The SystemCoordinator acts as the central nervous system for the entire agent ecosystem.

    It is responsible for initializing, managing the lifecycle of, and coordinating the
    various agents within the smart maintenance SaaS platform. This class is designed to
    integrate seamlessly with FastAPI's lifespan events, specifically `startup` and
    `shutdown`.

    During startup, it instantiates all configured agents, calls their respective
    `initialize` (if applicable, though current agents use `__init__` primarily) and `start`
    methods, effectively bringing the system online. Conversely, during shutdown,
    it ensures a graceful termination of all agents by invoking their `stop` methods.
    """
    def __init__(self):
        """
        Initializes the SystemCoordinator.

        This involves setting up the core event bus, preparing a dictionary to hold
        all agent instances, and loading any necessary configurations (though
        agent-specific configurations are typically passed during their instantiation).
        It then proceeds to create instances of all predefined agents.
        """
        logger.info("SystemCoordinator initializing...")
        self.event_bus: EventBus = EventBus()

        # Database session factory
        self.db_session_factory = lambda: AsyncSessionLocal()

        # Instantiate real services
        data_validator = DataValidator()
        data_enricher = DataEnricher()
        rule_engine = RuleEngine()

        # Enhanced Golden Path agent configurations
        data_acquisition_settings = {
            'batch_processing_enabled': True,
            'batch_size': 10,
            'batch_timeout_seconds': 5.0,
            'quality_threshold': 0.8,
            'enable_circuit_breaker': True,
            'circuit_breaker_threshold': 5,
            'rate_limit_per_second': 100,
            'enable_sensor_profiling': True
        }
        
        anomaly_detection_settings = {
            'serverless_mode_enabled': True,
            'model_cache_ttl_minutes': 60,
            'max_concurrent_model_loads': 3,
            'enable_fallback_models': True,
            'performance_monitoring': True
        }
        
        validation_settings = {
            'credible_threshold': 0.7,
            'false_positive_threshold': 0.4,
            'recent_stability_window': 5,
            'recent_stability_factor': 0.1,
            'recurring_anomaly_threshold_pct': 0.25,
            'historical_check_limit': 20
        }
        
        notification_settings = {
            'deduplication_window_minutes': 5,
            'rate_limit_per_user_per_hour': 20,
            'batch_size': 10,
            'batch_timeout_seconds': 30,
            'circuit_breaker_threshold': 5,
            'circuit_breaker_timeout_minutes': 10,
            'enable_batch_processing': True
        }

        self._agents_list: List[BaseAgent] = [
            # Enhanced Golden Path Agents
            DataAcquisitionAgent(
                agent_id="enhanced_data_acquisition_agent",
                event_bus=self.event_bus,
                validator=data_validator,
                enricher=data_enricher,
                specific_settings=data_acquisition_settings
            ),
            AnomalyDetectionAgent(
                agent_id="enhanced_anomaly_detection_agent",
                event_bus=self.event_bus,
                specific_settings=anomaly_detection_settings
            ),
            ValidationAgent(
                agent_id="enhanced_validation_agent",
                event_bus=self.event_bus,
                crud_sensor_reading=crud_sensor_reading,
                rule_engine=rule_engine,
                db_session_factory=self.db_session_factory,
                specific_settings=validation_settings
            ),
            EnhancedNotificationAgent(
                agent_id="enhanced_notification_agent",
                event_bus=self.event_bus,
                specific_settings=notification_settings
            ),
            PredictionAgent(
                agent_id="prediction_agent_01",
                event_bus=self.event_bus,
                crud_sensor_reading=crud_sensor_reading,
                db_session_factory=self.db_session_factory,
                specific_settings={}
            ),
            OrchestratorAgent(
                agent_id="orchestrator_agent_01",
                event_bus=self.event_bus
            ),
            SchedulingAgent(
                agent_id="scheduling_agent_01",
                event_bus=self.event_bus
            ),
            HumanInterfaceAgent(
                agent_id="human_interface_agent_01",
                event_bus=self.event_bus
            ),
            # Additional specialized agents continue to use existing implementations
            ReportingAgent(
                agent_id="reporting_agent_01",
                event_bus=self.event_bus
            ),
            MaintenanceLogAgent(
                agent_id="maintenance_log_agent_01",
                event_bus=self.event_bus,
                crud_maintenance_log=crud_maintenance_log,
                db_session_factory=self.db_session_factory
            )
        ]
        
        # Conditionally add LearningAgent if ChromaDB is available
        if LEARNING_AGENT_AVAILABLE and LearningAgent is not None:
            self._agents_list.append(
                LearningAgent(
                    agent_id="learning_agent_01",
                    event_bus=self.event_bus
                )
            )
        else:
            logger.warning("LearningAgent is disabled due to ChromaDB being unavailable or disabled")
            
        logger.info(f"SystemCoordinator initialized with {len(self._agents_list)} agents and event bus.")

    @property
    def reporting_agent(self) -> Optional[ReportingAgent]:
        """Get the ReportingAgent instance from the agents list."""
        for agent in self._agents_list:
            if isinstance(agent, ReportingAgent):
                return agent
        return None

    @property
    def agents(self) -> Dict[str, BaseAgent]:
        """
        Get agents as a dictionary mapping logical names to agent instances.
        This property creates a mapping for easy access by test and integration code.
        """
        if not hasattr(self, '_agents_dict'):
            self._agents_dict = {}
            for agent in self._agents_list:
                # Map agents by their logical names for test compatibility
                if isinstance(agent, DataAcquisitionAgent):
                    self._agents_dict['data_acquisition_agent'] = agent
                elif isinstance(agent, AnomalyDetectionAgent):
                    self._agents_dict['anomaly_detection_agent'] = agent
                elif isinstance(agent, ValidationAgent):
                    self._agents_dict['validation_agent'] = agent
                elif isinstance(agent, EnhancedNotificationAgent):
                    self._agents_dict['notification_agent'] = agent
                # Add other agents by their instance type or agent_id
                else:
                    # Use agent_id for other agents
                    self._agents_dict[agent.agent_id] = agent
        return self._agents_dict

    @agents.setter
    def agents(self, value: List[BaseAgent]):
        """Set the agents list and reset the dictionary cache."""
        self._agents_list = value
        if hasattr(self, '_agents_dict'):
            delattr(self, '_agents_dict')

    async def startup_system(self):
        """
        Manages the startup sequence of all agents in the system.

        This method is typically connected to the FastAPI `startup` event. It iterates
        through the list of configured agents, which were instantiated in `__init__`.
        For each agent, it calls its `start` method to perform any necessary
        initialization (e.g., subscribing to event bus topics, starting background tasks).

        Logs the successful startup of each agent or any errors encountered during
        their startup process.
        """
        logger.info("SystemCoordinator starting up all agents...")
        
        # First, register all agent capabilities
        for agent in self._agents_list:
            try:
                await agent.register_capabilities()
                logger.info(f"Registered capabilities for agent {agent.agent_id}")
            except Exception as e:
                logger.warning(f"Could not register capabilities for agent {agent.agent_id}: {e}")
        
        # Then start all agents concurrently
        startup_tasks = []
        for agent in self._agents_list:
            startup_tasks.append(agent.start())

        results = await asyncio.gather(*startup_tasks, return_exceptions=True)

        for agent, result in zip(self._agents_list, results):
            if isinstance(result, Exception):
                logger.error(f"Error starting agent {agent.agent_id}: {result}", exc_info=result)
            else:
                logger.info(f"Agent {agent.agent_id} started successfully.")
        
        # Log event bus subscription status
        logger.info(f"Event bus has {len(self.event_bus._subscribers)} event subscriptions")
        logger.info("All agents startup process initiated concurrently.")

    async def shutdown_system(self):
        """
        Manages the graceful shutdown sequence of all agents in the system.

        This method is typically connected to the FastAPI `shutdown` event. It iterates
        through the list of active agents, usually in the reverse order of their startup,
        and calls their `stop` method. This allows agents to perform cleanup tasks
        such as unsubscribing from event topics, releasing resources, or finishing
        any ongoing processes.

        Logs the successful shutdown of each agent or any errors encountered during
        their shutdown process. Also handles the shutdown of the event bus itself.
        """
        logger.info("SystemCoordinator shutting down all agents...")
        for agent in reversed(self._agents_list): # Stop in reverse order of start
            try:
                await agent.stop()
                logger.info(f"Agent {agent.agent_id} stopped successfully.")
            except Exception as e:
                logger.error(f"Error stopping agent {agent.agent_id}: {e}", exc_info=True)

        if hasattr(self.event_bus, 'shutdown'):
            try:
                await self.event_bus.shutdown()
                logger.info("Event bus shutdown successfully.")
            except Exception as e:
                logger.error(f"Error shutting down event bus: {e}", exc_info=True)
        logger.info("All agents shutdown process completed.")

if __name__ == '__main__':
    # Basic test logic
    async def main():
        logging.basicConfig(level=logging.INFO)
        coordinator = SystemCoordinator()
        await coordinator.startup_system()
        # Simulate some work or keep alive
        # await asyncio.sleep(10)
        await coordinator.shutdown_system()

    import asyncio
    # asyncio.run(main()) # Commented out for now, will be part of actual testing
    logger.info("SystemCoordinator skeleton created. Run 'python -m apps.system_coordinator' to test (after implementing mocks and agent instantiations).")
