import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import pydantic # For pydantic.ValidationError

from apps.agents.core.data_acquisition_agent import DataAcquisitionAgent
from core.events.event_models import (
    SensorDataReceivedEvent,
    DataProcessedEvent,
    DataProcessingFailedEvent,
)
from data.schemas import SensorReadingCreate, SensorReading
from data.exceptions import DataValidationException, DataEnrichmentException # Assuming DataEnrichmentException exists

class TestDataAcquisitionAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_event_bus = MagicMock()
        # Mock the publish method as an AsyncMock since the agent calls it with await
        self.mock_event_bus.publish = AsyncMock()

        self.mock_validator = MagicMock()
        self.mock_enricher = MagicMock()
        self.mock_logger = MagicMock()

        self.agent_id = "test_daq_agent"
        self.agent = DataAcquisitionAgent(
            agent_id=self.agent_id,
            event_bus=self.mock_event_bus,
            validator=self.mock_validator,
            enricher=self.mock_enricher,
            logger=self.mock_logger
        )

        self.correlation_id = uuid.uuid4()
        self.raw_data = {"device_id": "sensor_x", "value": 42.0, "timestamp": "2023-01-01T12:00:00Z"}
        # Ensure raw_data can be unpacked into SensorReadingCreate for tests
        # The agent itself takes raw_data as Dict, validator is responsible for parsing into SensorReadingCreate
        # For the purpose of this test, raw_data is what the validator receives.

        self.sensor_data_received_event = SensorDataReceivedEvent(
            raw_data=self.raw_data,
            correlation_id=self.correlation_id
        )

        # Common mock return values
        self.test_sensor_id = uuid.uuid4()
        self.test_timestamp_utc = datetime.now(timezone.utc)

        self.validated_data_mock = SensorReadingCreate(
            sensor_id=self.test_sensor_id,
            value=42.0,
            timestamp_utc=self.test_timestamp_utc,
            correlation_id=self.correlation_id
        )

        self.enriched_reading_mock = SensorReading(
            sensor_id=self.test_sensor_id,
            value=42.0,
            timestamp_utc=self.test_timestamp_utc,
            metadata={
                "ingestion_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "data_source_system": "test_source"
            },
            correlation_id=self.correlation_id
        )

    async def test_process_success(self):
        # Arrange
        self.mock_validator.validate.return_value = self.validated_data_mock
        self.mock_enricher.enrich.return_value = self.enriched_reading_mock

        # Act
        await self.agent.process(self.sensor_data_received_event)

        # Assert
        self.mock_validator.validate.assert_called_once_with(self.raw_data, self.correlation_id)
        self.mock_enricher.enrich.assert_called_once_with(self.validated_data_mock)
        self.mock_event_bus.publish.assert_awaited_once() # Use assert_awaited_once for AsyncMock

        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIsInstance(published_event, DataProcessedEvent)
        self.assertEqual(published_event.agent_id, self.agent_id)
        self.assertEqual(published_event.correlation_id, self.correlation_id)
        self.assertEqual(published_event.processed_data, self.enriched_reading_mock.model_dump())
        self.mock_logger.info.assert_called()

    async def test_process_validation_error_pydantic(self):
        # Arrange
        # Pydantic v2: errors is a list of dicts
        pydantic_errors = [{'type': 'missing', 'loc': ('sensor_id',), 'msg': 'Field required', 'input': self.raw_data}]
        validation_exception = pydantic.ValidationError.from_errors(pydantic_errors)

        self.mock_validator.validate.side_effect = validation_exception

        # Act
        await self.agent.process(self.sensor_data_received_event)

        # Assert
        self.mock_validator.validate.assert_called_once_with(self.raw_data, self.correlation_id)
        self.mock_enricher.enrich.assert_not_called()
        self.mock_event_bus.publish.assert_awaited_once()

        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIsInstance(published_event, DataProcessingFailedEvent)
        self.assertEqual(published_event.failed_agent_id, self.agent_id)
        self.assertEqual(published_event.correlation_id, self.correlation_id)
        self.assertEqual(published_event.original_event_payload, self.raw_data)
        # The string representation of pydantic.ValidationError includes the number of errors and details
        self.assertIn("1 validation error for PydanticUndefined", published_event.error_message) # PydanticUndefined is default model name
        self.assertIn("sensor_id", published_event.error_message)
        self.assertIn("Field required", published_event.error_message)
        self.assertIsNotNone(published_event.traceback_str)
        self.mock_logger.error.assert_called()

    async def test_process_validation_error_custom(self):
        # Arrange
        validation_exception = DataValidationException("Custom validation failed", errors=["some_field is wrong"])
        self.mock_validator.validate.side_effect = validation_exception

        # Act
        await self.agent.process(self.sensor_data_received_event)

        # Assert
        self.mock_validator.validate.assert_called_once_with(self.raw_data, self.correlation_id)
        self.mock_enricher.enrich.assert_not_called()
        self.mock_event_bus.publish.assert_awaited_once()

        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIsInstance(published_event, DataProcessingFailedEvent)
        self.assertEqual(published_event.failed_agent_id, self.agent_id)
        self.assertEqual(published_event.correlation_id, self.correlation_id)
        self.assertEqual(published_event.original_event_payload, self.raw_data)
        self.assertEqual(published_event.error_message, "Custom validation failed")
        self.assertIsNotNone(published_event.traceback_str)
        self.mock_logger.error.assert_called()

    async def test_process_enrichment_error_custom(self): # Using DataEnrichmentException
        # Arrange
        self.mock_validator.validate.return_value = self.validated_data_mock
        enrichment_exception = DataEnrichmentException("Enrichment process failed specifically")
        self.mock_enricher.enrich.side_effect = enrichment_exception

        # Act
        await self.agent.process(self.sensor_data_received_event)

        # Assert
        self.mock_validator.validate.assert_called_once_with(self.raw_data, self.correlation_id)
        self.mock_enricher.enrich.assert_called_once_with(self.validated_data_mock)
        self.mock_event_bus.publish.assert_awaited_once()

        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIsInstance(published_event, DataProcessingFailedEvent)
        self.assertEqual(published_event.failed_agent_id, self.agent_id)
        self.assertEqual(published_event.correlation_id, self.correlation_id)
        self.assertEqual(published_event.original_event_payload, self.validated_data_mock.model_dump())
        self.assertEqual(published_event.error_message, "Enrichment process failed specifically")
        self.assertIsNotNone(published_event.traceback_str)
        self.mock_logger.error.assert_called()

    async def test_process_enrichment_error_generic(self): # Using generic Exception
        # Arrange
        self.mock_validator.validate.return_value = self.validated_data_mock
        enrichment_exception = Exception("Generic enrichment error")
        self.mock_enricher.enrich.side_effect = enrichment_exception

        # Act
        await self.agent.process(self.sensor_data_received_event)

        # Assert
        # (Similar assertions as above for DataEnrichmentException)
        self.mock_validator.validate.assert_called_once_with(self.raw_data, self.correlation_id)
        self.mock_enricher.enrich.assert_called_once_with(self.validated_data_mock)
        self.mock_event_bus.publish.assert_awaited_once()

        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIsInstance(published_event, DataProcessingFailedEvent)
        self.assertEqual(published_event.failed_agent_id, self.agent_id)
        self.assertEqual(published_event.correlation_id, self.correlation_id)
        self.assertEqual(published_event.original_event_payload, self.validated_data_mock.model_dump())
        self.assertEqual(published_event.error_message, "Generic enrichment error")
        self.assertIsNotNone(published_event.traceback_str)
        self.mock_logger.error.assert_called()

    async def test_process_publish_data_processed_event_fails(self):
        # Arrange
        self.mock_validator.validate.return_value = self.validated_data_mock
        self.mock_enricher.enrich.return_value = self.enriched_reading_mock

        # Simulate failure when publishing DataProcessedEvent
        publish_exception_message = "Event bus unavailable"
        self.mock_event_bus.publish.side_effect = Exception(publish_exception_message)

        # Act
        await self.agent.process(self.sensor_data_received_event)

        # Assert
        self.mock_validator.validate.assert_called_once_with(self.raw_data, self.correlation_id)
        self.mock_enricher.enrich.assert_called_once_with(self.validated_data_mock)

        # Ensure publish was attempted (it will be called once for DataProcessedEvent, which fails)
        self.mock_event_bus.publish.assert_awaited_once()

        # Now check that DataProcessingFailedEvent was published as a fallback
        # This requires the mock to be reset or allow multiple calls if publish is a single mock object.
        # The agent code uses the same publish method for the fallback.
        # For this test, we check the arguments of the *final* call to publish if side_effect allows further calls
        # or if the mock is configured to handle this.
        # The current agent code will call publish again for DataProcessingFailedEvent.
        # So, we expect two calls in this scenario if the mock allows it after an exception.
        # Let's adjust the mock to have sequential side effects for more precise testing.

        self.mock_event_bus.publish.reset_mock() # Reset call stats for the next assertion

        # Re-configure for the specific scenario
        self.mock_event_bus.publish.side_effect = [
            Exception(publish_exception_message), # First call (DataProcessedEvent) fails
            AsyncMock() # Second call (DataProcessingFailedEvent) should succeed (or be captured)
        ]

        # Re-run the process with the new side_effect configuration
        await self.agent.process(self.sensor_data_received_event)

        self.assertEqual(self.mock_event_bus.publish.call_count, 2) # Called for DataProcessedEvent (failed) and DataProcessingFailedEvent (succeeded)

        final_call_args = self.mock_event_bus.publish.call_args_list[1][0][0] # Args of the second call
        self.assertIsInstance(final_call_args, DataProcessingFailedEvent)
        self.assertEqual(final_call_args.failed_agent_id, self.agent_id)
        self.assertEqual(final_call_args.correlation_id, self.correlation_id)
        self.assertIn(publish_exception_message, final_call_args.error_message)
        self.assertEqual(final_call_args.original_event_payload, self.enriched_reading_mock.model_dump())
        self.assertTrue(final_call_args.is_publish_failure)
        self.mock_logger.critical.assert_called()


if __name__ == '__main__':
    unittest.main()
