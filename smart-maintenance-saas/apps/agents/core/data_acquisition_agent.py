import logging
from typing import Any, Dict

from smart_maintenance_saas.apps.agents.base_agent import BaseAgent, AgentCapability
from smart_maintenance_saas.core.events.event_models import SensorDataReceivedEvent, DataProcessedEvent
from smart_maintenance_saas.data.processors.data_validator import DataValidator
from smart_maintenance_saas.data.processors.data_enricher import DataEnricher
# Assuming EventBus is passed during initialization as per BaseAgent
# from smart_maintenance_saas.core.events.event_bus import EventBus

logger = logging.getLogger(__name__)

class DataAcquisitionAgent(BaseAgent):
    """
    Agent responsible for acquiring raw sensor data, validating it,
    enriching it, and then publishing it as processed data.
    """

    AGENT_ID = "data_acquisition_agent_001" # Class level ID for convenience

    def __init__(self, event_bus: Any, agent_id: str = None):
        """
        Initializes the DataAcquisitionAgent.

        Args:
            event_bus (Any): An instance of the system's EventBus.
            agent_id (str, optional): A unique identifier for the agent.
                                      Defaults to DataAcquisitionAgent.AGENT_ID.
        """
        super().__init__(agent_id=agent_id or DataAcquisitionAgent.AGENT_ID, event_bus=event_bus)
        self.validator = DataValidator()
        self.enricher = DataEnricher()
        logger.info(f"DataAcquisitionAgent '{self.agent_id}' initialized with DataValidator and DataEnricher.")

    async def register_capabilities(self) -> None:
        """
        Registers the capabilities of this agent.
        """
        capability = AgentCapability(
            name="data_acquisition_and_processing",
            description="Acquires raw sensor data, validates, enriches, and publishes DataProcessedEvent.",
            input_types=[SensorDataReceivedEvent.__name__], # Use class name string
            output_types=[DataProcessedEvent.__name__]  # Use class name string
        )
        self.capabilities.append(capability)
        logger.info(f"Agent '{self.agent_id}': Registered capability '{capability.name}'.")

    async def start(self) -> None:
        """
        Starts the agent: registers capabilities and subscribes to SensorDataReceivedEvent.
        """
        await super().start() # Important to call parent's start
        # Subscribe to the raw data event.
        # The BaseAgent's handle_event will call self.process with the event object.
        await self.event_bus.subscribe(SensorDataReceivedEvent.__name__, self.handle_event)
        logger.info(f"Agent '{self.agent_id}' subscribed to '{SensorDataReceivedEvent.__name__}'.")

    async def stop(self) -> None:
        """
        Stops the agent: unsubscribes from events.
        """
        logger.info(f"Agent '{self.agent_id}' stopping...")
        try:
            await self.event_bus.unsubscribe(SensorDataReceivedEvent.__name__, self.handle_event)
            logger.info(f"Agent '{self.agent_id}' unsubscribed from '{SensorDataReceivedEvent.__name__}'.")
        except Exception as e:
            # Log error if unsubscription fails but don't prevent stopping
            logger.error(f"Agent '{self.agent_id}': Error during unsubscription from '{SensorDataReceivedEvent.__name__}': {e}", exc_info=True)
        await super().stop() # Important to call parent's stop

    async def process(self, event_data: SensorDataReceivedEvent) -> None:
        """
        Processes incoming SensorDataReceivedEvent.
        Validates and enriches the raw data, then publishes a DataProcessedEvent.

        Args:
            event_data (SensorDataReceivedEvent): The event object containing raw sensor data.
        """
        if not isinstance(event_data, SensorDataReceivedEvent):
            logger.warning(f"Agent '{self.agent_id}': Received unexpected data type in process: {type(event_data)}. Expected SensorDataReceivedEvent.")
            # Optionally publish an error/warning event
            # await self._publish_event("agent_processing_error", {"error": "Unexpected data type", "received_type": str(type(event_data))})
            return

        logger.info(f"Agent '{self.agent_id}': Processing SensorDataReceivedEvent (ID: {event_data.event_id}, Sensor: {event_data.sensor_id}).")
        raw_data = event_data.raw_data

        try:
            # 1. Validate data
            self.validator.validate(raw_data) # This will raise ValueError if invalid
            logger.debug(f"Agent '{self.agent_id}': Data validation successful for event {event_data.event_id}.")

            # 2. Enrich data
            enriched_data = self.enricher.enrich(raw_data) # Pass the raw_data dict
            logger.debug(f"Agent '{self.agent_id}': Data enrichment successful for event {event_data.event_id}.")

            # 3. Create DataProcessedEvent
            processed_event = DataProcessedEvent(
                processed_data=enriched_data,
                original_event_id=event_data.event_id,
                source_sensor_id=event_data.sensor_id,
                correlation_id=event_data.correlation_id # Carry over correlation ID
            )
            logger.debug(f"Agent '{self.agent_id}': Created DataProcessedEvent (ID: {processed_event.event_id}) for original event {event_data.event_id}.")

            # 4. Publish DataProcessedEvent
            await self._publish_event(DataProcessedEvent.__name__, processed_event)
            logger.info(f"Agent '{self.agent_id}': Successfully published '{DataProcessedEvent.__name__}' (ID: {processed_event.event_id}) for original event {event_data.event_id}.")

        except ValueError as ve:
            logger.error(f"Agent '{self.agent_id}': Validation error for data from sensor '{event_data.sensor_id}' (Event ID: {event_data.event_id}): {ve}", exc_info=True)
            # Optionally, publish a specific "data_validation_failed" event
            # await self._publish_event(
            #     "data_validation_failed_event",
            #     {
            #         "sensor_id": event_data.sensor_id,
            #         "raw_data": raw_data, # Be careful with PII or large data
            #         "error": str(ve),
            #         "original_event_id": event_data.event_id
            #     }
            # )
        except Exception as e:
            logger.error(f"Agent '{self.agent_id}': Unexpected error processing data from sensor '{event_data.sensor_id}' (Event ID: {event_data.event_id}): {e}", exc_info=True)
            # Optionally, publish a generic agent error event
            # await self._publish_event(
            #     "agent_processing_error",
            #     {
            #         "agent_id": self.agent_id,
            #         "error": str(e),
            #         "original_event_id": event_data.event_id,
            #         "stage": "processing"
            #     }
            # )

# Example of how this agent might be instantiated and used (for conceptual understanding)
# This would typically be done in a main application script or agent management service.
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Mock EventBus for local testing
    class MockEventBus:
        async def subscribe(self, event_type, handler):
            logger.info(f"[MockEventBus] Handler '{handler.__name__}' subscribed to '{event_type}'.")

        async def publish(self, event_type, data):
            logger.info(f"[MockEventBus] Publishing event '{event_type}' with data: {str(data)}")

        async def unsubscribe(self, event_type, handler):
            logger.info(f"[MockEventBus] Handler '{handler.__name__}' unsubscribed from '{event_type}'.")

    async def main_test():
        mock_bus = MockEventBus()
        agent = DataAcquisitionAgent(event_bus=mock_bus)

        await agent.start() # Registers capabilities and subscribes

        # Simulate receiving a SensorDataReceivedEvent
        # Valid data
        valid_raw_data = {"sensor_id": "temp-sim-01", "timestamp": 1678886400, "value": 22.5, "unit": "C"}
        valid_event = SensorDataReceivedEvent(raw_data=valid_raw_data, sensor_id="temp-sim-01")

        logger.info("\n--- Simulating valid event ---")
        # In a real system, the event bus would call agent.handle_event, which calls agent.process
        await agent.handle_event(SensorDataReceivedEvent.__name__, valid_event)

        # Simulate receiving invalid data
        invalid_raw_data = {"sensor_id": "temp-sim-02", "value": "high"} # Missing timestamp
        invalid_event = SensorDataReceivedEvent(raw_data=invalid_raw_data, sensor_id="temp-sim-02")

        logger.info("\n--- Simulating invalid event (validation error) ---")
        await agent.handle_event(SensorDataReceivedEvent.__name__, invalid_event)

        # Simulate non-event data (edge case, if handler called directly)
        # logger.info("\n--- Simulating direct call to process with non-event data ---")
        # await agent.process({"malformed_data": True}) # type: ignore

        await agent.stop()

    import asyncio
    asyncio.run(main_test())
