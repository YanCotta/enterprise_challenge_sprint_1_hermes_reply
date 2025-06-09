import logging
import asyncio # Make sure asyncio is imported
from typing import List, Callable, Optional, Dict, Any # Added Dict, Any for specific_settings
from datetime import datetime
from unittest.mock import AsyncMock
from data.schemas import SensorReading, SensorReadingCreate, AnomalyAlert, SensorType

# Event Bus
from core.events.event_bus import EventBus

# Base Agent (though not directly instantiated, good for context if needed)
from core.base_agent_abc import BaseAgent

# Agent Imports
from apps.agents.core.data_acquisition_agent import DataAcquisitionAgent
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
from apps.agents.learning.learning_agent import LearningAgent

# Database related imports (for mock type hints)
from sqlalchemy.ext.asyncio import AsyncSession

# Mock dependency type hints (will be defined or imported later)
# from apps.mocks import MockDataValidator, MockDataEnricher, MockCRUDSensorReading, MockRuleEngine # If mocks are in a separate file

logger = logging.getLogger(__name__)

# Define Mock Classes
class MockDataValidator:
    def validate(self, data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"MockDataValidator: Validating data for correlation_id {correlation_id}")
        # Return a dict that SensorReadingCreate can parse
        return {
            "sensor_id": data.get("sensor_id", "mock_sensor_id"),
            "value": data.get("value", 0.0),
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "sensor_type": data.get("sensor_type", SensorType.TEMPERATURE.value),
            "unit": data.get("unit", "C"),
            "correlation_id": correlation_id
        }

class MockDataEnricher:
    def enrich(self, data_to_enrich: Dict[str, Any]) -> SensorReading:
        logger.info(f"MockDataEnricher: Enriching data for {data_to_enrich.get('correlation_id')}")
        ts_str = data_to_enrich.get("timestamp")
        ts_obj = datetime.fromisoformat(ts_str) if isinstance(ts_str, str) else datetime.utcnow()
        st_str = data_to_enrich.get("sensor_type", SensorType.TEMPERATURE.value)
        st_enum = SensorType(st_str) if isinstance(st_str, str) else SensorType.TEMPERATURE
        return SensorReading(
            sensor_id=data_to_enrich.get("sensor_id", "mock_sensor_id"),
            value=data_to_enrich.get("value", 0.0),
            timestamp=ts_obj,
            sensor_type=st_enum,
            unit=data_to_enrich.get("unit", "C"),
            quality=0.9,
            correlation_id=data_to_enrich.get("correlation_id"),
            metadata={"enriched_by": "MockDataEnricher"},
            ingestion_timestamp=datetime.utcnow()
        )

class MockCRUDSensorReading:
    async def get_sensor_readings_by_sensor_id(
        self, db: Any, sensor_id: str, start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None, limit: Optional[int] = None
    ) -> List[SensorReading]:
        logger.info(f"MockCRUDSensorReading: Getting readings for sensor_id {sensor_id}")
        return []

    async def create_sensor_reading(self, db: Any, reading_data: Dict[str, Any]) -> Optional[SensorReading]:
        logger.info(f"MockCRUDSensorReading: Creating reading: {reading_data}")
        try:
            # Ensure timestamp is datetime object
            if 'timestamp' in reading_data and isinstance(reading_data['timestamp'], str):
                reading_data['timestamp'] = datetime.fromisoformat(reading_data['timestamp'])
            elif 'timestamp' not in reading_data: # Add default if missing
                reading_data['timestamp'] = datetime.utcnow()

            # Ensure sensor_type is SensorType enum
            if 'sensor_type' in reading_data and isinstance(reading_data['sensor_type'], str):
                reading_data['sensor_type'] = SensorType(reading_data['sensor_type'])
            elif 'sensor_type' not in reading_data: # Add default if missing
                 reading_data['sensor_type'] = SensorType.TEMPERATURE


            # Ensure other SensorReading fields are present or have defaults
            reading_data.setdefault('sensor_id', 'default_sensor')
            reading_data.setdefault('value', 0.0)
            # 'unit' can be optional or have a default based on SensorType
            if reading_data['sensor_type'] == SensorType.TEMPERATURE and 'unit' not in reading_data:
                reading_data['unit'] = 'C'
            elif reading_data['sensor_type'] == SensorType.PRESSURE and 'unit' not in reading_data:
                reading_data['unit'] = 'kPa'
            elif reading_data['sensor_type'] == SensorType.VIBRATION and 'unit' not in reading_data:
                reading_data['unit'] = 'mm/s'
            # Add other defaults as necessary based on SensorReading model
            reading_data.setdefault('quality', 1.0) # Default quality
            reading_data.setdefault('metadata', {}) # Default metadata
            reading_data.setdefault('ingestion_timestamp', datetime.utcnow())


            return SensorReading(**reading_data)
        except Exception as e:
            logger.error(f"MockCRUDSensorReading: Error creating SensorReading from data {reading_data}: {e}", exc_info=True)
            return None

class MockRuleEngine:
    async def evaluate_rules(self, alert: AnomalyAlert, reading: SensorReading) -> tuple[float, list[str]]:
        logger.info(f"MockRuleEngine: Evaluating rules for alert {alert.id if alert else 'N/A'} and reading from sensor {reading.sensor_id if reading else 'N/A'}")
        return 0.0, ["mock_rule_reason"]

def mock_db_session_factory() -> AsyncMock:
    logger.info("mock_db_session_factory: Creating mock AsyncSession")
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session

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

        mock_validator = MockDataValidator()
        mock_enricher = MockDataEnricher()
        mock_crud_sensor = MockCRUDSensorReading()
        mock_rule_engine = MockRuleEngine()

        self.agents: List[BaseAgent] = [
            DataAcquisitionAgent(
                agent_id="data_acquisition_agent_01",
                event_bus=self.event_bus,
                validator=mock_validator,
                enricher=mock_enricher
            ),
            AnomalyDetectionAgent(
                agent_id="anomaly_detection_agent_01",
                event_bus=self.event_bus,
                specific_settings={}
            ),
            ValidationAgent(
                agent_id="validation_agent_01",
                event_bus=self.event_bus,
                crud_sensor_reading=mock_crud_sensor,
                rule_engine=mock_rule_engine,
                db_session_factory=mock_db_session_factory,
                specific_settings={}
            ),
            PredictionAgent(
                agent_id="prediction_agent_01",
                event_bus=self.event_bus,
                crud_sensor_reading=mock_crud_sensor,
                db_session_factory=mock_db_session_factory,
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
            LearningAgent(
                agent_id="learning_agent_01",
                event_bus=self.event_bus
            )
        ]
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
