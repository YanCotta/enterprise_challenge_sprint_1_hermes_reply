"""
Unit tests for the PredictionAgent.

Tests cover all major functionality including data preparation, Prophet modeling,
prediction generation, and event publishing.
"""

import unittest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid
import logging
from typing import List, Dict, Any
import pandas as pd

from apps.agents.decision.prediction_agent import PredictionAgent
from core.events.event_models import AnomalyValidatedEvent, MaintenancePredictedEvent
from data.schemas import SensorReading

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestPredictionAgent(unittest.IsolatedAsyncioTestCase):
    """Test suite for PredictionAgent functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_event_bus = AsyncMock()
        self.mock_crud_sensor_reading = AsyncMock()
        self.mock_db_session_factory = Mock()
        self.mock_db_session = AsyncMock()
        self.mock_db_session.close = AsyncMock()
        self.mock_db_session_factory.return_value = self.mock_db_session

        # Test settings
        self.test_settings = {
            "min_historical_points": 10,
            "prediction_horizon_days": 30,
            "historical_data_limit": 100,
            "prediction_confidence_threshold": 0.6
        }

        self.agent = PredictionAgent(
            agent_id="test_prediction_agent",
            event_bus=self.mock_event_bus,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            db_session_factory=self.mock_db_session_factory,
            specific_settings=self.test_settings
        )

        self.default_timestamp = datetime.utcnow()

    def _create_anomaly_validated_event(
        self,
        validation_status: str = "credible_anomaly",
        final_confidence: float = 0.8,
        sensor_id: str = "test_sensor_001",
        correlation_id: str = None
    ) -> AnomalyValidatedEvent:
        """Create a test AnomalyValidatedEvent."""
        return AnomalyValidatedEvent(
            original_anomaly_alert_payload={
                "sensor_id": sensor_id,
                "anomaly_type": "spike",
                "severity": 4,
                "confidence": 0.7
            },
            triggering_reading_payload={
                "sensor_id": sensor_id,
                "value": 100.0,
                "timestamp": self.default_timestamp.isoformat(),
                "sensor_type": "temperature"
            },
            validation_status=validation_status,
            final_confidence=final_confidence,
            validation_reasons=["Test validation"],
            agent_id="test_validation_agent",
            correlation_id=correlation_id or str(uuid.uuid4())
        )

    def _create_mock_sensor_readings(self, count: int = 50) -> List[SensorReading]:
        """Create mock sensor readings for testing."""
        readings = []
        base_time = self.default_timestamp - timedelta(days=count)
        
        for i in range(count):
            reading = SensorReading(
                id=i + 1,
                sensor_id="test_sensor_001",
                sensor_type="temperature",
                value=20.0 + (i * 0.1) + (i % 5) * 2,  # Some variation
                unit="celsius",
                timestamp=base_time + timedelta(days=i),
                quality=1.0
            )
            readings.append(reading)
        
        return readings

    # Tests for initialization and configuration

    def test_agent_initialization(self):
        """Test agent initialization with correct settings."""
        self.assertEqual(self.agent.agent_id, "test_prediction_agent")
        self.assertEqual(self.agent.min_historical_points, 10)
        self.assertEqual(self.agent.prediction_horizon_days, 30)
        self.assertEqual(self.agent.historical_data_limit, 100)
        self.assertEqual(self.agent.confidence_threshold, 0.6)

    def test_agent_initialization_default_settings(self):
        """Test agent initialization with default settings."""
        agent = PredictionAgent(
            agent_id="test_agent",
            event_bus=self.mock_event_bus,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            db_session_factory=self.mock_db_session_factory
        )
        
        # Check default values
        self.assertEqual(agent.min_historical_points, 30)
        self.assertEqual(agent.prediction_horizon_days, 90)
        self.assertEqual(agent.historical_data_limit, 1000)
        self.assertEqual(agent.confidence_threshold, 0.6)

    # Tests for agent lifecycle

    async def test_start_agent(self):
        """Test agent start process."""
        await self.agent.start()
        
        # Verify subscription
        self.mock_event_bus.subscribe.assert_called_once_with(
            event_type_name="AnomalyValidatedEvent",
            handler=self.agent.process
        )

    async def test_stop_agent(self):
        """Test agent stop process."""
        await self.agent.stop()
        
        # Verify unsubscription
        self.mock_event_bus.unsubscribe.assert_called_once_with(
            event_type_name="AnomalyValidatedEvent",
            handler=self.agent.process
        )

    # Tests for event processing conditions

    def test_extract_sensor_id_from_anomaly_payload(self):
        """Test extracting sensor_id from anomaly alert payload."""
        event = self._create_anomaly_validated_event(sensor_id="sensor_123")
        sensor_id = self.agent._extract_sensor_id(event)
        self.assertEqual(sensor_id, "sensor_123")

    def test_extract_sensor_id_from_reading_payload(self):
        """Test extracting sensor_id from triggering reading payload."""
        event = self._create_anomaly_validated_event()
        # Remove sensor_id from anomaly payload
        event.original_anomaly_alert_payload = {"anomaly_type": "spike"}
        
        sensor_id = self.agent._extract_sensor_id(event)
        self.assertEqual(sensor_id, "test_sensor_001")

    def test_extract_sensor_id_failure(self):
        """Test sensor_id extraction when not available."""
        event = self._create_anomaly_validated_event()
        event.original_anomaly_alert_payload = {}
        event.triggering_reading_payload = {}
        
        sensor_id = self.agent._extract_sensor_id(event)
        self.assertIsNone(sensor_id)

    def test_extract_equipment_id(self):
        """Test equipment_id extraction."""
        event = self._create_anomaly_validated_event()
        equipment_id = self.agent._extract_equipment_id(event)
        self.assertEqual(equipment_id, "equipment_test_sensor_001")

    def test_should_generate_prediction_confirmed(self):
        """Test prediction generation for confirmed anomaly."""
        event = self._create_anomaly_validated_event(validation_status="CONFIRMED")
        self.assertTrue(self.agent._should_generate_prediction(event))

    def test_should_generate_prediction_credible(self):
        """Test prediction generation for credible anomaly."""
        event = self._create_anomaly_validated_event(validation_status="credible_anomaly")
        self.assertTrue(self.agent._should_generate_prediction(event))

    def test_should_generate_prediction_high_confidence(self):
        """Test prediction generation for high confidence anomaly."""
        event = self._create_anomaly_validated_event(
            validation_status="uncertain", 
            final_confidence=0.8
        )
        self.assertTrue(self.agent._should_generate_prediction(event))

    def test_should_not_generate_prediction_low_confidence(self):
        """Test skipping prediction for low confidence anomaly."""
        event = self._create_anomaly_validated_event(
            validation_status="false_positive", 
            final_confidence=0.3
        )
        self.assertFalse(self.agent._should_generate_prediction(event))

    # Tests for data preparation

    def test_prepare_prophet_data_success(self):
        """Test successful Prophet data preparation."""
        readings = self._create_mock_sensor_readings(30)
        df = self.agent._prepare_prophet_data(readings)
        
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 30)
        self.assertIn('ds', df.columns)
        self.assertIn('y', df.columns)
        self.assertTrue(df['ds'].is_monotonic_increasing)

    def test_prepare_prophet_data_empty_input(self):
        """Test Prophet data preparation with empty input."""
        df = self.agent._prepare_prophet_data([])
        self.assertIsNone(df)

    def test_prepare_prophet_data_deduplication(self):
        """Test Prophet data preparation removes duplicates."""
        readings = self._create_mock_sensor_readings(20)
        # Add duplicate timestamp
        duplicate_reading = SensorReading(
            id=999,
            sensor_id="test_sensor_001",
            sensor_type="temperature",
            value=50.0,
            unit="celsius",
            timestamp=readings[0].timestamp,  # Same timestamp as first reading
            quality=1.0
        )
        readings.append(duplicate_reading)
        
        df = self.agent._prepare_prophet_data(readings)
        
        # Should have one less row due to deduplication
        self.assertEqual(len(df), 20)

    # Tests for historical data fetching

    async def test_fetch_historical_data_success(self):
        """Test successful historical data fetching."""
        # Create simple objects that are truthy (not Mock objects)
        # Use a simple class that will pass the truthiness check
        class FakeORMObject:
            def __init__(self, id_val):
                self.id = id_val
                
        mock_orm_readings = [FakeORMObject(i) for i in range(20)]
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = mock_orm_readings
        
        # Patch the SensorReading.model_validate method
        with patch('data.schemas.SensorReading.model_validate') as mock_validate:
            mock_validate.side_effect = lambda x: SensorReading(
                id=1, sensor_id="test", sensor_type="temperature", value=25.0,  # Fixed: use valid enum value
                unit="C", timestamp=datetime.utcnow(), quality=1.0
            )
            
            readings, error = await self.agent._fetch_historical_data_for_prediction(
                sensor_id="test_sensor", limit=100
            )
            
            self.assertEqual(len(readings), 20)
            self.assertIsNone(error)
            # Verify that model_validate was called for each ORM object
            self.assertEqual(mock_validate.call_count, 20)
            self.assertIsNone(error)
            self.mock_db_session.close.assert_called_once()

    async def test_fetch_historical_data_no_session_factory(self):
        """Test historical data fetching without session factory."""
        agent = PredictionAgent(
            agent_id="test_agent",
            event_bus=self.mock_event_bus,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            db_session_factory=None
        )
        
        readings, error = await agent._fetch_historical_data_for_prediction("test_sensor")
        
        self.assertEqual(len(readings), 0)
        self.assertIsNotNone(error)
        self.assertIn("Database session factory not provided", error)

    async def test_fetch_historical_data_database_error(self):
        """Test historical data fetching with database error."""
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = Exception("DB Error")
        
        readings, error = await self.agent._fetch_historical_data_for_prediction("test_sensor")
        
        self.assertEqual(len(readings), 0)
        self.assertIsNotNone(error)
        self.assertIn("Error fetching historical data", error)

    # Tests for Prophet prediction generation

    @patch('apps.agents.decision.prediction_agent.Prophet')
    async def test_generate_prediction_success(self, mock_prophet_class):
        """Test successful prediction generation."""
        # Setup mock Prophet model
        mock_model = MagicMock()
        mock_prophet_class.return_value = mock_model
        
        # Create mock forecast data
        forecast_data = {
            'ds': pd.date_range(start=datetime.utcnow(), periods=30, freq='D'),
            'yhat': [25.0 + i * 0.1 for i in range(30)],
            'yhat_lower': [20.0 + i * 0.1 for i in range(30)],
            'yhat_upper': [30.0 + i * 0.1 for i in range(30)]
        }
        mock_forecast = pd.DataFrame(forecast_data)
        mock_model.predict.return_value = mock_forecast
        
        # Create test data
        test_data = pd.DataFrame({
            'ds': pd.date_range(start=datetime.utcnow() - timedelta(days=30), periods=30, freq='D'),
            'y': [25.0 + i * 0.05 for i in range(30)]
        })
        
        result = await self.agent._generate_prediction(test_data, "test_sensor")
        
        self.assertIsNotNone(result)
        self.assertIn('predicted_failure_date', result)
        self.assertIn('confidence_interval_lower', result)
        self.assertIn('confidence_interval_upper', result)
        self.assertIn('prediction_confidence', result)
        self.assertIn('time_to_failure_days', result)
        self.assertIn('maintenance_type', result)
        self.assertIn('recommended_actions', result)
        self.assertIn('model_metrics', result)

    @patch('apps.agents.decision.prediction_agent.Prophet')
    async def test_generate_prediction_prophet_error(self, mock_prophet_class):
        """Test prediction generation with Prophet error."""
        mock_prophet_class.side_effect = Exception("Prophet error")
        
        test_data = pd.DataFrame({
            'ds': pd.date_range(start=datetime.utcnow() - timedelta(days=30), periods=30, freq='D'),
            'y': [25.0] * 30
        })
        
        result = await self.agent._generate_prediction(test_data, "test_sensor")
        
        self.assertIsNone(result)

    # Tests for maintenance recommendation generation

    def test_generate_maintenance_recommendations_urgent(self):
        """Test urgent maintenance recommendations."""
        recommendations = self.agent._generate_maintenance_recommendations(
            time_to_failure=5.0, 
            maintenance_type="urgent_corrective", 
            trend_slope=0.2
        )
        
        self.assertIn("Schedule immediate maintenance intervention", recommendations)
        self.assertIn("Monitor upward trend in sensor readings", recommendations)

    def test_generate_maintenance_recommendations_preventive(self):
        """Test preventive maintenance recommendations."""
        recommendations = self.agent._generate_maintenance_recommendations(
            time_to_failure=20.0,
            maintenance_type="preventive",
            trend_slope=-0.15  # More significant trend to trigger monitoring recommendation
        )
        
        self.assertIn("Schedule preventive maintenance within recommended timeframe", recommendations)
        self.assertIn("Monitor downward trend in sensor readings", recommendations)

    def test_generate_maintenance_recommendations_inspection(self):
        """Test inspection recommendations."""
        recommendations = self.agent._generate_maintenance_recommendations(
            time_to_failure=90.0, 
            maintenance_type="inspection", 
            trend_slope=0.05
        )
        
        self.assertIn("Schedule routine inspection", recommendations)
        self.assertNotIn("Monitor upward trend", recommendations)  # Trend not significant

    # Tests for model metrics calculation

    @patch('apps.agents.decision.prediction_agent.Prophet')
    def test_calculate_model_metrics(self, mock_prophet_class):
        """Test model metrics calculation."""
        mock_model = Mock()
        
        historical_data = pd.DataFrame({
            'ds': pd.date_range(start=datetime.utcnow() - timedelta(days=10), periods=10, freq='D'),
            'y': [25.0, 26.0, 24.0, 27.0, 25.5, 26.5, 24.5, 27.5, 25.2, 26.8]
        })
        
        forecast_data = {
            'ds': historical_data['ds'].tolist(),
            'yhat': [25.1, 25.9, 24.1, 26.9, 25.4, 26.4, 24.6, 27.4, 25.3, 26.7]
        }
        forecast = pd.DataFrame(forecast_data)
        
        metrics = self.agent._calculate_model_metrics(mock_model, historical_data, forecast)
        
        self.assertIn('mae', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('mape', metrics)
        self.assertIsInstance(metrics['mae'], float)
        self.assertIsInstance(metrics['rmse'], float)
        self.assertIsInstance(metrics['mape'], float)

    # Tests for event publishing

    async def test_publish_maintenance_prediction_success(self):
        """Test successful maintenance prediction event publishing."""
        event = self._create_anomaly_validated_event()
        prediction_result = {
            'predicted_failure_date': datetime.utcnow() + timedelta(days=30),
            'confidence_interval_lower': datetime.utcnow() + timedelta(days=25),
            'confidence_interval_upper': datetime.utcnow() + timedelta(days=35),
            'prediction_confidence': 0.8,
            'time_to_failure_days': 30.0,
            'maintenance_type': 'preventive',
            'historical_data_points': 50,
            'model_metrics': {'mae': 0.5, 'rmse': 0.7, 'mape': 2.1},
            'recommended_actions': ['Schedule maintenance']
        }
        
        await self.agent._publish_maintenance_prediction(
            event=event,
            equipment_id="test_equipment",
            sensor_id="test_sensor",
            prediction_result=prediction_result
        )
        
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertIsInstance(published_event, MaintenancePredictedEvent)
        self.assertEqual(published_event.equipment_id, "test_equipment")
        self.assertEqual(published_event.time_to_failure_days, 30.0)
        self.assertEqual(published_event.maintenance_type, "preventive")

    async def test_publish_maintenance_prediction_no_event_bus(self):
        """Test maintenance prediction publishing without event bus."""
        agent = PredictionAgent(
            agent_id="test_agent",
            event_bus=None,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            db_session_factory=self.mock_db_session_factory
        )
        
        event = self._create_anomaly_validated_event()
        prediction_result = {
            'predicted_failure_date': datetime.utcnow() + timedelta(days=30),
            'confidence_interval_lower': datetime.utcnow() + timedelta(days=25),
            'confidence_interval_upper': datetime.utcnow() + timedelta(days=35),
            'prediction_confidence': 0.8,
            'time_to_failure_days': 30.0,
            'maintenance_type': 'preventive',
            'historical_data_points': 50,
            'model_metrics': {'mae': 0.5, 'rmse': 0.7, 'mape': 2.1},
            'recommended_actions': ['Schedule maintenance']
        }
        
        # Should not raise an exception
        await agent._publish_maintenance_prediction(
            event=event,
            equipment_id="test_equipment",
            sensor_id="test_sensor",
            prediction_result=prediction_result
        )

    # Integration tests for the full process method

    @patch('apps.agents.decision.prediction_agent.Prophet')
    async def test_process_full_pipeline_success(self, mock_prophet_class):
        """Test the complete processing pipeline."""
        # Setup mocks
        mock_readings = self._create_mock_sensor_readings(50)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = [Mock() for _ in range(50)]
        
        with patch('data.schemas.SensorReading.model_validate') as mock_validate:
            mock_validate.side_effect = mock_readings
            
            # Setup Prophet mock
            mock_model = MagicMock()
            mock_prophet_class.return_value = mock_model
            
            forecast_data = {
                'ds': pd.date_range(start=datetime.utcnow(), periods=30, freq='D'),
                'yhat': [25.0 + i * 0.1 for i in range(30)],
                'yhat_lower': [20.0 + i * 0.1 for i in range(30)],
                'yhat_upper': [30.0 + i * 0.1 for i in range(30)]
            }
            mock_forecast = pd.DataFrame(forecast_data)
            mock_model.predict.return_value = mock_forecast
            
            # Process event
            event = self._create_anomaly_validated_event()
            await self.agent.process(event)
            
            # Verify event was published
            self.mock_event_bus.publish.assert_called_once()
            published_event = self.mock_event_bus.publish.call_args.args[0]
            self.assertIsInstance(published_event, MaintenancePredictedEvent)

    async def test_process_insufficient_data(self):
        """Test processing with insufficient historical data."""
        # Setup minimal data (less than min_historical_points)
        mock_readings = self._create_mock_sensor_readings(5)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = [Mock() for _ in range(5)]
        
        with patch('data.schemas.SensorReading.model_validate') as mock_validate:
            mock_validate.side_effect = mock_readings
            
            event = self._create_anomaly_validated_event()
            await self.agent.process(event)
            
            # Should not publish any event due to insufficient data
            self.mock_event_bus.publish.assert_not_called()

    async def test_process_low_confidence_anomaly(self):
        """Test processing low confidence anomaly (should be skipped)."""
        event = self._create_anomaly_validated_event(
            validation_status="false_positive",
            final_confidence=0.3
        )
        
        await self.agent.process(event)
        
        # Should not proceed with prediction
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.assert_not_called()
        self.mock_event_bus.publish.assert_not_called()

    async def test_process_no_sensor_id(self):
        """Test processing event without extractable sensor_id."""
        event = self._create_anomaly_validated_event()
        event.original_anomaly_alert_payload = {}
        event.triggering_reading_payload = {}
        
        await self.agent.process(event)
        
        # Should not proceed with prediction
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.assert_not_called()
        self.mock_event_bus.publish.assert_not_called()


if __name__ == '__main__':
    unittest.main()
