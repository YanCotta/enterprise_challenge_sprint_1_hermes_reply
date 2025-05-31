import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime as dt, timezone
from uuid import UUID, uuid4

from data.processors.data_enricher import DataEnricher
from data.schemas import SensorReadingCreate, SensorReading

class TestDataEnricher(unittest.TestCase):

    def setUp(self):
        self.default_source_system = "test_default_system"
        self.enricher = DataEnricher(default_data_source_system=self.default_source_system)
        self.sensor_id = uuid4()
        self.value = 25.5
        self.timestamp_utc = dt.now(timezone.utc)
        self.correlation_id = uuid4()

        self.sample_data_create = SensorReadingCreate(
            sensor_id=self.sensor_id,
            value=self.value,
            timestamp_utc=self.timestamp_utc,
            correlation_id=self.correlation_id
        )

    @patch('data.processors.data_enricher.dt') # Note: patching 'dt' as it's imported as 'dt' in the module
    def test_basic_enrichment(self, mock_datetime_module):
        mock_now = dt(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        # Configure the mock 'dt' object's 'utcnow' method
        mock_datetime_module.utcnow.return_value = mock_now
        # Also, if dt.now is used anywhere for defaults (it is not in enricher, but good practice)
        mock_datetime_module.now.return_value = mock_now


        result = self.enricher.enrich(self.sample_data_create)

        self.assertIsInstance(result, SensorReading)
        self.assertEqual(result.sensor_id, self.sensor_id)
        self.assertEqual(result.value, self.value)
        self.assertEqual(result.timestamp_utc, self.timestamp_utc)
        self.assertEqual(result.correlation_id, self.correlation_id)

        self.assertIn("ingestion_timestamp_utc", result.metadata)
        self.assertEqual(result.metadata["ingestion_timestamp_utc"], mock_now.isoformat())

        self.assertIn("data_source_system", result.metadata)
        self.assertEqual(result.metadata["data_source_system"], self.default_source_system)

    def test_enrichment_with_data_source_system_override(self):
        override_system = "override_test_system"
        result = self.enricher.enrich(self.sample_data_create, data_source_system_override=override_system)

        self.assertIsInstance(result, SensorReading)
        self.assertIn("data_source_system", result.metadata)
        self.assertEqual(result.metadata["data_source_system"], override_system)

    def test_enrichment_with_existing_correlation_id(self):
        specific_correlation_id = uuid4()
        data_with_specific_corr_id = SensorReadingCreate(
            sensor_id=uuid4(),
            value=30.0,
            timestamp_utc=dt.now(timezone.utc),
            correlation_id=specific_correlation_id
        )
        result = self.enricher.enrich(data_with_specific_corr_id)

        self.assertIsInstance(result, SensorReading)
        self.assertEqual(result.correlation_id, specific_correlation_id)

    @patch('data.processors.data_enricher.uuid4') # Patch uuid4 where it's called
    def test_enrichment_without_correlation_id_generates_one(self, mock_uuid4):
        generated_uuid = uuid4()
        mock_uuid4.return_value = generated_uuid

        data_without_corr_id = SensorReadingCreate(
            sensor_id=uuid4(),
            value=30.0,
            timestamp_utc=dt.now(timezone.utc),
            correlation_id=None  # Explicitly None
        )
        result = self.enricher.enrich(data_without_corr_id)

        self.assertIsInstance(result, SensorReading)
        self.assertIsNotNone(result.correlation_id)
        self.assertIsInstance(result.correlation_id, UUID)
        self.assertEqual(result.correlation_id, generated_uuid)

        # Test case where correlation_id is not provided at all (if Pydantic model allows)
        # For SensorReadingCreate, correlation_id: Optional[UUID] = None, so it will be None by default
        data_missing_corr_id_field = SensorReadingCreate(
            sensor_id=uuid4(),
            value=31.0,
            timestamp_utc=dt.now(timezone.utc)
            # correlation_id is omitted, will default to None
        )
        result_missing_field = self.enricher.enrich(data_missing_corr_id_field)
        self.assertIsInstance(result_missing_field, SensorReading)
        self.assertIsNotNone(result_missing_field.correlation_id)
        self.assertIsInstance(result_missing_field.correlation_id, UUID)
        self.assertEqual(result_missing_field.correlation_id, generated_uuid)


if __name__ == '__main__':
    unittest.main()
