import logging
import traceback
from typing import Any, Dict, Optional
from uuid import UUID

import pydantic  # For pydantic.ValidationError

# Direct imports assuming 'smart-maintenance-saas' is the project root for Python
from core.base_agent_abc import BaseAgent
from core.events.event_bus import EventBus  # Corrected path
from core.events.event_models import (
    DataProcessedEvent,
    DataProcessingFailedEvent,
    SensorDataReceivedEvent,
)
from data.exceptions import DataEnrichmentException, DataValidationException
from data.processors.agent_data_enricher import DataEnricher
from data.schemas import SensorReading, SensorReadingCreate  # For type hinting
from data.validators.agent_data_validator import DataValidator


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
        self.logger = (
            logger if logger else logging.getLogger(f"{__name__}.{self.agent_id}")
        )
        self.logger.info(f"DataAcquisitionAgent {self.agent_id} initialized.")

    async def start(self) -> None:
        """
        Subscribes the agent to relevant events.
        """
        await super().start()
        await self.event_bus.subscribe(SensorDataReceivedEvent.__name__, self.process)
        self.logger.info(
            f"DataAcquisitionAgent {self.agent_id} started and subscribed to SensorDataReceivedEvent."
        )

    async def stop(self) -> None:
        """
        Unsubscribes the agent from events.
        """
        await super().stop()
        await self.event_bus.unsubscribe(SensorDataReceivedEvent.__name__, self.process)
        self.logger.info(
            f"DataAcquisitionAgent {self.agent_id} stopped and unsubscribed from SensorDataReceivedEvent."
        )

    async def process(self, event: SensorDataReceivedEvent):
        """
        Processes incoming sensor data events.
        Validates and enriches the data, then publishes further events.
        """
        raw_data: Dict[str, Any] = event.raw_data
        correlation_id: Optional[UUID] = event.correlation_id
        event_type: str = type(event).__name__  # Or event.event_type if it exists

        self.logger.info(
            f"[{correlation_id}] Processing started for event {event_type}"
        )
        self.logger.debug(f"[{correlation_id}] Raw data: {raw_data}")

        validated_data: Optional[SensorReadingCreate] = None  # Initialize

        # 1. Validation Step
        try:
            # Assume validator.validate returns a SensorReadingCreate instance or raises an exception
            validated_data = self.validator.validate(raw_data, correlation_id)
            self.logger.debug(f"[{correlation_id}] Data validation successful.")
        except (DataValidationException, pydantic.ValidationError) as e:
            error_message = (
                f"Validation failed for data with correlation_id {correlation_id}: {e}"
            )
            self.logger.error(error_message, exc_info=True)

            failure_payload = {
                "agent_id": self.agent_id,
                "error_message": str(e),
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                "original_event_payload": raw_data,  # Send the original raw data
                "correlation_id": str(correlation_id) if correlation_id else None,
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))
            return  # Stop processing

        # 2. Enrichment Step
        try:
            # enricher.enrich expects SensorReadingCreate and returns SensorReading
            enriched_reading = self.enricher.enrich(validated_data)  # type: ignore
            self.logger.debug(f"[{correlation_id}] Data enrichment successful.")
        except DataEnrichmentException as e:  # Catch specific enrichment errors first
            error_message = (
                f"Enrichment failed for data with correlation_id {correlation_id}: {e}"
            )
            self.logger.error(error_message, exc_info=True)

            failure_payload = {
                "agent_id": self.agent_id,
                "error_message": str(e),
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                "original_event_payload": validated_data.model_dump() if validated_data else raw_data,  # type: ignore
                "correlation_id": str(correlation_id) if correlation_id else None,
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))
            return  # Stop processing
        except Exception as e:  # Catch any other unexpected errors during enrichment
            error_message = f"An unexpected error occurred during enrichment for correlation_id {correlation_id}: {e}"
            self.logger.error(error_message, exc_info=True)

            failure_payload = {
                "agent_id": self.agent_id,
                "error_message": str(e),
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                "original_event_payload": validated_data.model_dump() if validated_data else raw_data,  # type: ignore
                "correlation_id": str(correlation_id) if correlation_id else None,
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))
            return  # Stop processing

        # 3. Success Path: Publish DataProcessedEvent
        try:
            processed_payload = {
                "processed_data": enriched_reading.model_dump(),  # SensorReading to dict
                "original_event_id": event.event_id,  # From the input SensorDataReceivedEvent
                "source_sensor_id": enriched_reading.sensor_id,  # Already a string from schema
                "correlation_id": str(correlation_id)
                if correlation_id
                else None,  # From original event
            }
            await self.event_bus.publish(DataProcessedEvent(**processed_payload))
            self.logger.info(
                f"[{correlation_id}] Successfully processed data and published DataProcessedEvent."
            )
        except Exception as e:
            error_message = f"Failed to publish DataProcessedEvent for correlation_id {correlation_id} after successful processing: {e}"
            self.logger.critical(error_message, exc_info=True)
            failure_payload = {
                "agent_id": self.agent_id,
                "error_message": f"Failed to publish DataProcessedEvent: {str(e)}",
                "traceback_str": traceback.format_exc(),
                "original_event_type": event_type,
                "original_event_payload": enriched_reading.model_dump(),  # The data that was successfully processed but not announced
                "correlation_id": str(correlation_id) if correlation_id else None,
                "is_publish_failure": True,
            }
            await self.event_bus.publish(DataProcessingFailedEvent(**failure_payload))

    async def example_usage(self):
        # This is an example and would not typically be part of the agent's core logic
        pass


# Example (for illustration, not part of the core file usually):
if __name__ == "__main__":
    # This section is for example and testing purposes.
    # In a real application, agents are managed by an agent runner or similar system.

    # Mockups
    class MockEventBus(EventBus):
        async def publish(self, event):
            print(
                f"MockEventBus: Published event {type(event).__name__} with data: {event.model_dump(exclude_none=True)}"
            )

        def subscribe(self, event_type, handler):
            print(
                f"MockEventBus: Subscribed {handler.__name__} to {event_type.__name__}"
            )

        def unsubscribe(self, event_type, handler):
            print(
                f"MockEventBus: Unsubscribed {handler.__name__} from {event_type.__name__}"
            )

    # Direct imports for __main__ block, assuming smart-maintenance-saas is in PYTHONPATH
    from data.exceptions import DataEnrichmentException, DataValidationException
    from data.schemas import SensorReading, SensorReadingCreate

    class MockDataValidator(DataValidator):
        def __init__(self):
            pass

        def validate(
            self, data: Dict[str, Any], correlation_id: Optional[UUID] = None
        ) -> SensorReadingCreate:
            print(f"MockDataValidator: Validating data for {correlation_id}")
            if "invalid_key" in data:
                raise DataValidationException(
                    "Contains invalid_key", errors=["invalid_key found"]
                )
            if not data.get("sensor_id"):
                # Pydantic v2 errors are dicts, not Pydantic models
                raise pydantic.ValidationError.from_exception_data(
                    title="SensorReadingCreate",
                    line_errors=[
                        {
                            "input": data,
                            "loc": ("sensor_id",),
                            "msg": "Field required",
                            "type": "missing",
                        }
                    ],
                )

            try:
                return SensorReadingCreate(**data)
            except pydantic.ValidationError as e:
                # Extract errors for DataValidationException
                errors_list = []
                for error in e.errors():
                    errors_list.append(
                        f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
                    )
                raise DataValidationException(
                    f"Pydantic validation failed during mock validation: {str(e)}",
                    errors=errors_list,
                )

    class MockDataEnricher(DataEnricher):
        def __init__(self):
            super().__init__(default_data_source_system="mock_enricher_default")

        def enrich(
            self,
            data_to_enrich: SensorReadingCreate,
            data_source_system_override: Optional[str] = None,
        ) -> SensorReading:
            print(
                f"MockDataEnricher: Enriching data for {data_to_enrich.correlation_id}"
            )
            if data_to_enrich.value == -999.0:
                raise DataEnrichmentException(
                    "Value -999.0 indicates an error during enrichment mock."
                )

            enriched = super().enrich(data_to_enrich, data_source_system_override)
            if enriched.metadata is None:  # Should not happen with default_factory
                enriched.metadata = {}
            enriched.metadata["mock_enricher_applied"] = True
            return enriched

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("DAQAgentExample")

    event_bus = MockEventBus()
    validator = MockDataValidator()
    enricher = MockDataEnricher()

    agent = DataAcquisitionAgent(
        "daq_agent_001", event_bus, validator, enricher, logger
    )
    agent.start()

    import asyncio
    from datetime import (
        datetime as dt,  # Ensure datetime is imported as dt for the example
    )
    from datetime import timezone
    from uuid import uuid4

    async def run_simulations():
        # Scenario 1: Successful processing
        good_data = {
            "sensor_id": str(uuid4()),
            "value": 25.5,
            "timestamp": dt.now(timezone.utc).isoformat(),
        }
        good_event = SensorDataReceivedEvent(raw_data=good_data, correlation_id=uuid4())
        await agent.process(good_event)
        print("-" * 20)

        # Scenario 2: Validation failure (custom DataValidationException)
        invalid_data_custom = {"invalid_key": "some_value", "sensor_id": str(uuid4())}
        fail_event_custom_validation = SensorDataReceivedEvent(
            raw_data=invalid_data_custom, correlation_id=uuid4()
        )
        await agent.process(fail_event_custom_validation)
        print("-" * 20)

        # Scenario 3: Validation failure (Pydantic ValidationError)
        invalid_data_pydantic = {
            "value": 10.0,
            "timestamp": dt.now(timezone.utc).isoformat(),
        }  # Missing sensor_id
        fail_event_pydantic = SensorDataReceivedEvent(
            raw_data=invalid_data_pydantic, correlation_id=uuid4()
        )
        await agent.process(fail_event_pydantic)
        print("-" * 20)

        # Scenario 4: Enrichment failure
        enrich_fail_data = {
            "sensor_id": str(uuid4()),
            "value": -999.0,
            "timestamp": dt.now(timezone.utc).isoformat(),
        }
        fail_event_enrich = SensorDataReceivedEvent(
            raw_data=enrich_fail_data, correlation_id=uuid4()
        )
        await agent.process(fail_event_enrich)
        print("-" * 20)

    asyncio.run(run_simulations())
    agent.stop()
