import logging
import asyncio # Make sure asyncio is imported
from typing import List, Callable, Optional, Dict, Any # Added Dict, Any for specific_settings
from datetime import datetime
from data.schemas import SensorReading, SensorReadingCreate, AnomalyAlert, SensorType

# Event Bus
from core.events.event_bus import EventBus

# Base Agent (though not directly instantiated, good for context if needed)
from core.base_agent_abc import BaseAgent

# Agent Imports
from apps.agents.core.data_acquisition_agent import DataAcquisitionAgent
import os
from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from apps.agents.core.validation_agent import ValidationAgent
# from apps.agents.core.prediction_agent import PredictionAgent # Path was decision/prediction_agent.py
from apps.agents.decision.prediction_agent import PredictionAgent
from apps.agents.core.orchestrator_agent import OrchestratorAgent
from apps.agents.decision.scheduling_agent import SchedulingAgent
from apps.agents.interface.human_interface_agent import HumanInterfaceAgent
# from apps.agents.interface.notification_agent import NotificationAgent # Path was decision/notification_agent.py
from apps.agents.decision.notification_agent import NotificationAgent
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
from core.database.crud.crud_sensor_reading import crud_sensor_reading as CRUDSensorReading
from core.database.crud.crud_maintenance_log import crud_maintenance_log as CRUDMaintenanceLog
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

        self.agents: List[BaseAgent] = [
            DataAcquisitionAgent(
                agent_id="data_acquisition_agent_01",
                event_bus=self.event_bus,
                validator=data_validator,
                enricher=data_enricher
            ),
            AnomalyDetectionAgent(
                agent_id="anomaly_detection_agent_01",
                event_bus=self.event_bus,
                specific_settings={}
            ),
            ValidationAgent(
                agent_id="validation_agent_01",
                event_bus=self.event_bus,
                crud_sensor_reading=CRUDSensorReading,
                rule_engine=rule_engine,
                db_session_factory=self.db_session_factory,
                specific_settings={}
            ),
            PredictionAgent(
                agent_id="prediction_agent_01",
                event_bus=self.event_bus,
                crud_sensor_reading=CRUDSensorReading,
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
            NotificationAgent(
                agent_id="notification_agent_01",
                event_bus=self.event_bus
            ),
            ReportingAgent(
                agent_id="reporting_agent_01",
                event_bus=self.event_bus
            ),
            MaintenanceLogAgent(
                agent_id="maintenance_log_agent_01",
                event_bus=self.event_bus,
                crud_maintenance_log=CRUDMaintenanceLog,
                db_session_factory=self.db_session_factory
            )
        ]
        
        # Conditionally add LearningAgent if ChromaDB is available
        if LEARNING_AGENT_AVAILABLE and LearningAgent is not None:
            self.agents.append(
                LearningAgent(
                    agent_id="learning_agent_01",
                    event_bus=self.event_bus
                )
            )
        else:
            logger.warning("LearningAgent is disabled due to ChromaDB being unavailable or disabled")
            
        logger.info(f"SystemCoordinator initialized with {len(self.agents)} agents and event bus.")

    @property
    def reporting_agent(self) -> Optional[ReportingAgent]:
        """Get the ReportingAgent instance from the agents list."""
        for agent in self.agents:
            if isinstance(agent, ReportingAgent):
                return agent
        return None

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
        startup_tasks = []
        for agent in self.agents:
            startup_tasks.append(agent.start())

        results = await asyncio.gather(*startup_tasks, return_exceptions=True)

        for agent, result in zip(self.agents, results):
            if isinstance(result, Exception):
                logger.error(f"Error starting agent {agent.agent_id}: {result}", exc_info=result)
            else:
                logger.info(f"Agent {agent.agent_id} started successfully.")
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
        for agent in reversed(self.agents): # Stop in reverse order of start
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
