import logging
import traceback
from typing import Optional, Dict, Any
from uuid import UUID

import pydantic # For pydantic.ValidationError

from apps.agents.base_agent import BaseAgent # Assuming this path is correct
from core.event_bus.event_bus import EventBus # Assuming this path is correct
from core.events.event_models import ( # Assuming this path is correct
    SensorDataReceivedEvent,
    DataProcessedEvent,
    DataProcessingFailedEvent,
)
from data.validators.data_validator import DataValidator # Assuming this path is correct
from data.processors.data_enricher import DataEnricher
from data.schemas import SensorReadingCreate # For type hinting
from data.exceptions import DataValidationException, DataEnrichmentException


class DataAcquisitionAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        validator: DataValidator,
        enricher: DataEnricher,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(agent_id, event_bus)
        self.validator = validator
        self.enricher = enricher
        self.logger = logger if logger else logging.getLogger(f"{__name__}.{self.agent_id}")
        self.logger.info(f"DataAcquisitionAgent {self.agent_id} initialized.")

    def start(self):
        """
        Subscribes the agent to relevant events.
        """
        self.event_bus.subscribe(SensorDataReceivedEvent, self.process)
        self.logger.info(f"DataAcquisitionAgent {self.agent_id} started and subscribed to SensorDataReceivedEvent.")

    def stop(self):
        """
        Unsubscribes the agent from events.
        """
        self.event_bus.unsubscribe(SensorDataReceivedEvent, self.process)
        self.logger.info(f"DataAcquisitionAgent {self.agent_id} stopped and unsubscribed from SensorDataReceivedEvent.")

    async def process(self, event: SensorDataReceivedEvent):
        """
        Processes incoming sensor data events.
        Validates and enriches the data, then publishes further events.
        """
        raw_data: Dict[str, Any] = event.raw_data
        correlation_id: Optional[UUID] = event.correlation_id
        event_type: str = type(event).__name__ # Or event.event_type if it exists

        self.logger.debug(f"[{correlation_id}] Received event {event_type} for processing.")

        validated_data: Optional[SensorReadingCreate] = None # Initialize

        # 1. Validation Step
        try:
            # Assume validator.validate returns a SensorReadingCreate instance or raises an exception
            validated_data = self.validator.validate(raw_data, correlation_id)
            self.logger.debug(f"[{correlation_id}] Data validation successful.")
        except (DataValidationException, pydantic.ValidationError) as e:
            error_message = f"Validation failed for data with correlation_id {correlation_id}: {e}"
            self.logger.error(error_message, exc_info=True)

            failure_payload = {
                "failed_agent_id": self.agent_id,
                "error_message": str(e),
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                "original_event_payload": raw_data, # Send the original raw data
                "correlation_id": correlation_id,
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))
            return # Stop processing

        # 2. Enrichment Step
        try:
            # enricher.enrich expects SensorReadingCreate and returns SensorReading
            # The enricher might have its own default for data_source_system or it could be passed here.
            # For this task, we assume the enricher handles it or uses its default.
            enriched_reading = self.enricher.enrich(validated_data)
            self.logger.debug(f"[{correlation_id}] Data enrichment successful.")
        except DataEnrichmentException as e: # Catch specific enrichment errors first
            error_message = f"Enrichment failed for data with correlation_id {correlation_id}: {e}"
            self.logger.error(error_message, exc_info=True)

            failure_payload = {
                "failed_agent_id": self.agent_id,
                "error_message": str(e),
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                # Send validated data if available, else original raw data
                "original_event_payload": validated_data.dict() if validated_data else raw_data,
                "correlation_id": correlation_id,
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))
            return # Stop processing
        except Exception as e: # Catch any other unexpected errors during enrichment
            error_message = f"An unexpected error occurred during enrichment for correlation_id {correlation_id}: {e}"
            self.logger.error(error_message, exc_info=True)

            failure_payload = {
                "failed_agent_id": self.agent_id,
                "error_message": str(e),
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                "original_event_payload": validated_data.dict() if validated_data else raw_data,
                "correlation_id": correlation_id,
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))
            return # Stop processing

        # 3. Success Path: Publish DataProcessedEvent
        try:
            processed_payload = {
                "processed_data": enriched_reading.dict(), # SensorReading to dict
                "agent_id": self.agent_id,
                "correlation_id": enriched_reading.correlation_id, # Ensure this is correctly propagated
            }
            await self.event_bus.publish(DataProcessedEvent(**processed_payload))
            self.logger.info(
                f"[{correlation_id}] Successfully processed data and published DataProcessedEvent."
            )
        except Exception as e:
            # This is an edge case: processing was successful but publishing the success event failed.
            error_message = f"Failed to publish DataProcessedEvent for correlation_id {correlation_id} after successful processing: {e}"
            self.logger.critical(error_message, exc_info=True)
            # Depending on desired system resilience, could try to publish a DataProcessingFailedEvent here,
            # but the primary data processing was technically successful.
            # For now, just log critically. The data is processed but downstream systems won't know.
            # Alternatively, if event bus publish is critical, this could re-raise or publish a specific "PublishingFailed" event.
            # Let's publish a DataProcessingFailedEvent to indicate the overall transaction couldn't complete.
            failure_payload = {
                "failed_agent_id": self.agent_id,
                "error_message": f"Failed to publish DataProcessedEvent: {str(e)}",
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                "original_event_payload": enriched_reading.dict(), # The data that was successfully processed but not announced
                "correlation_id": correlation_id,
                "is_publish_failure": True # Custom flag to indicate this specific failure mode
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))


    async def example_usage(self):
        # This is an example and would not typically be part of the agent's core logic
        # It requires setting up a mock event bus, validator, and enricher.
        pass

# Example (for illustration, not part of the core file usually):
if __name__ == '__main__':
    # This section is for example and testing purposes.
    # In a real application, agents are managed by an agent runner or similar system.

    # Mockups
    class MockEventBus(EventBus):
        async def publish(self, event):
            print(f"MockEventBus: Published event {type(event).__name__} with data: {event.dict(exclude_none=True)}")
        def subscribe(self, event_type, handler):
            print(f"MockEventBus: Subscribed {handler.__name__} to {event_type.__name__}")
        def unsubscribe(self, event_type, handler):
            print(f"MockEventBus: Unsubscribed {handler.__name__} from {event_type.__name__}")


    class MockDataValidator(DataValidator):
        def __init__(self): pass # No base class init to call for this mock
        def validate(self, data: Dict[str, Any], correlation_id: Optional[UUID] = None) -> SensorReadingCreate:
            print(f"MockDataValidator: Validating data for {correlation_id}")
            if "invalid_key" in data:
                raise DataValidationException("Contains invalid_key", errors=["invalid_key found"])
            if not data.get("sensor_id"):
                raise pydantic.ValidationError(errors=[{'loc': ('sensor_id',), 'msg': 'field required', 'type': 'value_error.missing'}], model=SensorReadingCreate)

            # Simulate successful validation, returning SensorReadingCreate
            # In a real scenario, this would involve actual Pydantic model creation & validation
            try:
                # Attempt to create, this will raise pydantic.ValidationError if fields are missing/wrong type
                return SensorReadingCreate(**data)
            except pydantic.ValidationError as e:
                # Re-raise or wrap in DataValidationException if preferred
                raise DataValidationException("Pydantic validation failed during mock validation", errors=e.errors())


    class MockDataEnricher(DataEnricher):
        def __init__(self):
            super().__init__(default_data_source_system="mock_enricher_default")

        def enrich(self, data_to_enrich: SensorReadingCreate, data_source_system_override: Optional[str] = None) -> SensorReading:
            print(f"MockDataEnricher: Enriching data for {data_to_enrich.correlation_id}")
            if data_to_enrich.value == -999.0: # Simulate an enrichment error
                raise DataEnrichmentException("Value -999.0 indicates an error during enrichment mock.")

            # Call actual enricher logic to ensure it's covered
            enriched = super().enrich(data_to_enrich, data_source_system_override)
            # Add some mock-specific metadata if needed, or just rely on parent
            enriched.metadata["mock_enricher_applied"] = True
            return enriched

    # Setup basic logging for the example
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("DAQAgentExample")

    # Instantiate components
    event_bus = MockEventBus()
    validator = MockDataValidator()
    enricher = MockDataEnricher() # Uses the actual enricher logic with a mock wrapper

    # Create and start the agent
    agent = DataAcquisitionAgent("daq_agent_001", event_bus, validator, enricher, logger)
    agent.start()

    # Simulate some events
    import asyncio
    from uuid import uuid4

    async def run_simulations():
        # Scenario 1: Successful processing
        good_data = {
            "sensor_id": str(uuid4()), "value": 25.5, "timestamp_utc": dt.now(timezone.utc).isoformat()
        }
        good_event = SensorDataReceivedEvent(raw_data=good_data, correlation_id=uuid4())
        await agent.process(good_event)
        print("-" * 20)

        # Scenario 2: Validation failure (custom DataValidationException)
        invalid_data_custom = {"invalid_key": "some_value", "sensor_id": str(uuid4())}
        fail_event_custom_validation = SensorDataReceivedEvent(raw_data=invalid_data_custom, correlation_id=uuid4())
        await agent.process(fail_event_custom_validation)
        print("-" * 20)

        # Scenario 3: Validation failure (Pydantic ValidationError)
        invalid_data_pydantic = {"value": 10.0} # Missing sensor_id and timestamp_utc
        fail_event_pydantic = SensorDataReceivedEvent(raw_data=invalid_data_pydantic, correlation_id=uuid4())
        await agent.process(fail_event_pydantic)
        print("-" * 20)

        # Scenario 4: Enrichment failure
        enrich_fail_data = {
            "sensor_id": str(uuid4()), "value": -999.0, "timestamp_utc": dt.now(timezone.utc).isoformat()
        }
        # This data should pass validation by MockDataValidator, then fail in MockDataEnricher
        fail_event_enrich = SensorDataReceivedEvent(raw_data=enrich_fail_data, correlation_id=uuid4())
        await agent.process(fail_event_enrich)
        print("-" * 20)

    asyncio.run(run_simulations())
    agent.stop()
