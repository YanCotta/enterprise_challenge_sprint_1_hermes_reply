import asyncio
import uuid
import logging
from datetime import datetime, timezone, timedelta # Added timedelta for timestamp comparisons
import unittest
from unittest.mock import MagicMock, patch

from apps.agents.core.data_acquisition_agent import DataAcquisitionAgent
from core.events.event_bus import EventBus # Corrected path
from core.events.event_models import SensorDataReceivedEvent, DataProcessedEvent, DataProcessingFailedEvent, BaseEventModel # Added BaseEventModel
from data.schemas import SensorReadingCreate, SensorReading, SensorType # Added SensorReading for type checks and SensorType
from data.validators.agent_data_validator import DataValidator # Corrected to agent_data_validator
from data.processors.agent_data_enricher import DataEnricher # Corrected to agent_data_enricher
from data.exceptions import DataEnrichmentException, DataValidationException

# Helper function to check if a string is a valid ISO 8601 timestamp
def is_isoformat(s: str) -> bool:
    try:
        datetime.fromisoformat(s.replace('Z', '+00:00')) # Handle Z for UTC
        return True
    except ValueError:
        return False

class TestIntegrationDataAcquisitionAgent(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.event_bus = EventBus()
        self.validator = DataValidator()
        self.enricher = DataEnricher(default_data_source_system="integration_test_source")
        self.agent_id = "integration_daq_agent_" + str(uuid.uuid4())[:8]
        self.logger = MagicMock(spec=logging.Logger)

        self.agent = DataAcquisitionAgent(
            agent_id=self.agent_id,
            event_bus=self.event_bus,
            validator=self.validator,
            enricher=self.enricher,
            logger=self.logger # Pass the MagicMock logger
        )
        # The agent's start method subscribes it to SensorDataReceivedEvent
        await self.agent.start()

        self.received_events = []
        # Ensure the handler can be awaited if the event bus publish/dispatch mechanism is async
        self.event_bus.subscribe(DataProcessedEvent.__name__, self.capture_event_handler)
        self.event_bus.subscribe(DataProcessingFailedEvent.__name__, self.capture_event_handler)


    async def capture_event_handler(self, event: BaseEventModel): # Changed Event to BaseEventModel
        self.received_events.append(event)

    async def asyncTearDown(self):
        if self.agent:
            await self.agent.stop()

    async def test_integration_success_path(self):
        correlation_id = uuid.uuid4()
        sensor_id_uuid = uuid.uuid4()
        raw_data_ts = datetime.now(timezone.utc)

        raw_data = {
            "sensor_id": str(sensor_id_uuid),
            "value": 123.45,
            "timestamp_utc": raw_data_ts.isoformat()
            # "correlation_id" is not in raw_data, will be passed by event
        }
        input_event = SensorDataReceivedEvent(raw_data=raw_data.copy(), correlation_id=str(correlation_id))

        await self.event_bus.publish(input_event)
        await asyncio.sleep(0.1) # Allow time for event processing

        self.assertEqual(len(self.received_events), 1, f"Should receive one event, got {len(self.received_events)}")
        processed_event = self.received_events[0]
        self.assertIsInstance(processed_event, DataProcessedEvent)
        self.assertEqual(processed_event.agent_id, self.agent_id)
        self.assertEqual(processed_event.correlation_id, str(correlation_id)) # Check event's correlation_id

        # Check processed_data content
        pd = processed_event.processed_data
        self.assertIsInstance(pd, dict)
        self.assertEqual(pd["sensor_id"], sensor_id_uuid) # Compare with original UUID object
        self.assertEqual(pd["value"], raw_data["value"])
        self.assertTrue(is_isoformat(pd["timestamp_utc"]))
        self.assertEqual(datetime.fromisoformat(pd["timestamp_utc"]), raw_data_ts)
        self.assertEqual(pd["correlation_id"], str(correlation_id)) # Check correlation_id within processed_data

        # Check metadata
        self.assertIn("ingestion_timestamp_utc", pd["metadata"])
        self.assertTrue(is_isoformat(pd["metadata"]["ingestion_timestamp_utc"]))
        self.assertEqual(pd["metadata"]["data_source_system"], "integration_test_source")

        self.logger.info.assert_called()
        self.logger.error.assert_not_called() # Ensure no errors logged

    async def test_integration_pydantic_validation_failure(self):
        correlation_id = uuid.uuid4()
        invalid_raw_data = {
            "sensor_id": "not-a-uuid-string", # Invalid UUID
            "value": "not-a-float",      # Invalid float
            "timestamp_utc": "invalid-date-format" # Invalid datetime
        }
        input_event = SensorDataReceivedEvent(raw_data=invalid_raw_data.copy(), correlation_id=str(correlation_id))

        await self.event_bus.publish(input_event)
        await asyncio.sleep(0.1)

        self.assertEqual(len(self.received_events), 1)
        failed_event = self.received_events[0]
        self.assertIsInstance(failed_event, DataProcessingFailedEvent)
        self.assertEqual(failed_event.failed_agent_id, self.agent_id)
        self.assertEqual(failed_event.correlation_id, str(correlation_id))
        self.assertEqual(failed_event.original_event_payload, invalid_raw_data)
        self.assertTrue(len(failed_event.error_message) > 0, "Error message should not be empty for Pydantic failure")
        # Example check for Pydantic error content (highly dependent on Pydantic version and error formatting)
        self.assertIn("sensor_id", failed_event.error_message.lower()) # Check if field name is mentioned
        self.assertIn("value", failed_event.error_message.lower())
        self.assertIn("timestamp_utc", failed_event.error_message.lower())
        self.assertIsNotNone(failed_event.traceback_str)
        self.assertEqual(failed_event.original_event_type, "SensorDataReceivedEvent")
        self.logger.error.assert_called()
        self.logger.info.assert_not_called() # Ensure no success logs

    async def test_integration_custom_validation_failure_negative_value(self):
        correlation_id = uuid.uuid4()
        sensor_id_uuid = uuid.uuid4()
        custom_invalid_raw_data = {
            "sensor_id": str(sensor_id_uuid),
            "value": -50.0, # This should trigger the custom validator rule
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }
        input_event = SensorDataReceivedEvent(raw_data=custom_invalid_raw_data.copy(), correlation_id=str(correlation_id))

        await self.event_bus.publish(input_event)
        await asyncio.sleep(0.1)

        self.assertEqual(len(self.received_events), 1)
        failed_event = self.received_events[0]
        self.assertIsInstance(failed_event, DataProcessingFailedEvent)
        self.assertEqual(failed_event.failed_agent_id, self.agent_id)
        self.assertEqual(failed_event.correlation_id, str(correlation_id))
        self.assertEqual(failed_event.original_event_payload, custom_invalid_raw_data)
        self.assertIn("Sensor value cannot be negative: -50.0", failed_event.error_message)
        self.assertIsNotNone(failed_event.traceback_str)
        self.assertEqual(failed_event.original_event_type, "SensorDataReceivedEvent")
        self.logger.error.assert_called()

    async def test_integration_enrichment_failure(self):
        correlation_id = uuid.uuid4()
        sensor_id_uuid = uuid.uuid4()
        raw_data_ts = datetime.now(timezone.utc)
        valid_raw_data = {
            "sensor_id": str(sensor_id_uuid),
            "value": 25.5,
            "timestamp_utc": raw_data_ts.isoformat(),
            "sensor_type": SensorType.TEMPERATURE.value, # Added sensor_type
            "unit": "°C" # Added unit
        }
        input_event = SensorDataReceivedEvent(raw_data=valid_raw_data.copy(), correlation_id=str(correlation_id))

        # Expected payload after validation (SensorReadingCreate model)
        # This should match the structure that DataValidator.validate is expected to produce
        # and which will be included in DataProcessingFailedEvent.original_event_payload
        expected_validated_payload_dict = SensorReadingCreate(
            sensor_id=str(sensor_id_uuid),  # Ensure sensor_id is string
            value=valid_raw_data["value"],
            timestamp=raw_data_ts,         # Use 'timestamp' field name, validator maps timestamp_utc
            sensor_type=SensorType.TEMPERATURE, # Provide sensor_type enum
            unit="°C",                      # Provide unit
            # quality and sensor_metadata have defaults in Pydantic model and are set by validator if not present
            # The SensorReadingCreate schema does not include correlation_id.
            # correlation_id is used internally by the validator but is not part of the schema or the validated payload.
            # metadata is added by the validator if not present in raw data, as per the schema's default behavior.
        ).model_dump()
        # Adjust expected_validated_payload_dict to include what validator adds, if not aligned with SensorReadingCreate schema directly
        # The validator's output SensorReadingCreate object's model_dump() is what's in the event.
        # If validator adds correlation_id to the SensorReadingCreate instance (e.g. if model has extra='allow'),
        # then it would be in the dump. Current SensorReadingCreate does not allow extra fields.
        # The validator also adds sensor_metadata if not present.
        # Let's assume metadata will be added by the validator if it's not in raw_data.
        # SensorReadingCreate schema has `sensor_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)`
        # So, an empty dict is expected if not provided.
        # The validator also maps "timestamp_utc" to "timestamp".

        # The critical part is that `expected_validated_payload_dict` must match the
        # `original_event_payload` of the `DataProcessingFailedEvent`.
        # This payload comes from `validated_data_obj.model_dump()` in DataAcquisitionAgent,
        # where `validated_data_obj` is the output of `self.validator.validate()`.
        # So, `expected_validated_payload_dict` must be a valid `SensorReadingCreate` instance,
        # created using the same logic as the validator if there are transformations.

        # The validator takes raw_data, adds correlation_id, maps fields, and then creates SensorReadingCreate.
        # raw_data for this test now includes sensor_type and unit.
        # The validator's `_map_raw_to_schema_fields` handles `timestamp_utc` -> `timestamp`.
        # It creates `SensorReadingCreate(**mapped_data, sensor_metadata=metadata, correlation_id=correlation_id_str)`
        # IF SensorReadingCreate accepted **kwargs or had correlation_id field. It does not.
        # This means the validator itself will likely fail if it tries to pass correlation_id to SensorReadingCreate
        # if the model doesn't define it or allow extra fields.
        # For now, the goal is to fix the test's direct instantiation issues.

        # Patch the 'enrich' method of the specific enricher instance used by the agent
        with patch.object(self.agent.enricher, 'enrich', side_effect=DataEnrichmentException("Simulated enrichment failure")) as mock_enrich_method:
            await self.event_bus.publish(input_event)
            await asyncio.sleep(0.1) # Allow event processing

            mock_enrich_method.assert_called_once() # Ensure enrich was actually called

        self.assertEqual(len(self.received_events), 1, f"Should receive one event, got {len(self.received_events)}")
        failed_event = self.received_events[0]
        self.assertIsInstance(failed_event, DataProcessingFailedEvent)
        self.assertEqual(failed_event.failed_agent_id, self.agent_id)
        self.assertEqual(failed_event.correlation_id, str(correlation_id))

        # The original_event_payload in DataProcessingFailedEvent for enrichment failure
        # should be the dict representation of the *validated_data* (SensorReadingCreate instance)
        self.assertEqual(failed_event.original_event_payload, expected_validated_payload_dict)
        self.assertEqual(failed_event.error_message, "Simulated enrichment failure")
        self.assertIsNotNone(failed_event.traceback_str)
        self.assertEqual(failed_event.original_event_type, "SensorDataReceivedEvent")
        self.logger.error.assert_called()

if __name__ == '__main__':
    unittest.main()
