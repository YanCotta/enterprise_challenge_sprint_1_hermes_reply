"""
Integration tests for PredictionAgent to verify event flow and system integration.

These tests verify that the PredictionAgent can properly:
1. Subscribe to AnomalyValidatedEvent
2. Process events and generate predictions using Prophet
3. Publish MaintenancePredictedEvent
4. Integrate with the database layer for historical data
"""

import unittest
import logging
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from apps.agents.decision.prediction_agent import PredictionAgent
from core.events.event_bus import EventBus
from core.events.event_models import AnomalyValidatedEvent, MaintenancePredictedEvent
from core.database.crud.crud_sensor_reading import CRUDSensorReading
from data.schemas import SensorReading


# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestPredictionAgentIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration test suite for PredictionAgent."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
        self.mock_crud_sensor_reading = AsyncMock()
        self.mock_db_session_factory = Mock()
        self.mock_db_session = AsyncMock()
        self.mock_db_session.close = AsyncMock()
        self.mock_db_session_factory.return_value = self.mock_db_session

        # Test settings for faster processing
        self.test_settings = {
            "min_historical_points": 5,  # Lower threshold for testing
            "prediction_horizon_days": 7,
            "historical_data_limit": 50,
            "prediction_confidence_threshold": 0.6
        }

        self.agent = PredictionAgent(
            agent_id="test_prediction_agent_integration",
            event_bus=self.event_bus,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            db_session_factory=self.mock_db_session_factory,
            specific_settings=self.test_settings
        )

        # Start the agent
        await self.agent.start()

    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.agent.stop()

    def _create_anomaly_validated_event(
        self,
        validation_status: str = "credible_anomaly",
        final_confidence: float = 0.8,
        sensor_id: str = "sensor_temp_001"
    ) -> AnomalyValidatedEvent:
        """Create a test AnomalyValidatedEvent."""
        return AnomalyValidatedEvent(
            original_anomaly_alert_payload={
                "sensor_id": sensor_id,
                "anomaly_type": "spike",
                "severity": 4,
                "confidence": 0.7,
                "equipment_id": f"equipment_{sensor_id}"
            },
            triggering_reading_payload={
                "sensor_id": sensor_id,
                "value": 85.0,  # High temperature
                "timestamp": datetime.utcnow().isoformat(),
                "sensor_type": "temperature",
                "unit": "C",
                "quality": 0.95
            },
            validation_status=validation_status,
            final_confidence=final_confidence,
            validation_reasons=["Test validation for integration"],
            agent_id="test_validation_agent",
            correlation_id=str(uuid4())
        )

    def _create_historical_sensor_readings(self, count: int = 30) -> list:
        """Create mock historical sensor readings."""
        readings = []
        base_time = datetime.utcnow() - timedelta(days=30)
        
        for i in range(count):
            # Create a simple object that passes truthiness check
            class FakeORMReading:
                def __init__(self, idx):
                    self.id = idx
                    self.sensor_id = "sensor_temp_001"
                    self.value = 20.0 + (idx % 10)  # Values between 20-30
                    self.timestamp = base_time + timedelta(days=idx)
                    
            readings.append(FakeORMReading(i))
        return readings

    async def test_end_to_end_prediction_workflow(self):
        """Test the complete prediction workflow from event to event."""
        # Setup mock historical data
        mock_historical_readings = self._create_historical_sensor_readings(30)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = mock_historical_readings

        # Create a valid anomaly event
        test_event = self._create_anomaly_validated_event()
        
        # Mock the event publishing to capture the result
        published_events = []
        
        async def capture_published_event(event):
            published_events.append(event)
        
        # Subscribe to MaintenancePredictedEvent to capture the result
        await self.event_bus.subscribe(
            event_type_name="MaintenancePredictedEvent",
            handler=capture_published_event
        )

        # Mock SensorReading.model_validate to return valid objects
        with patch('data.schemas.SensorReading.model_validate') as mock_validate:
            mock_validate.side_effect = lambda x: SensorReading(
                id=x.id,
                sensor_id=x.sensor_id,
                sensor_type="temperature",
                value=x.value,
                unit="C",
                timestamp=x.timestamp,
                quality=0.95
            )

            # Mock Prophet to avoid actual ML computation in integration test
            with patch('apps.agents.decision.prediction_agent.Prophet') as mock_prophet:
                mock_model = Mock()
                mock_prophet.return_value = mock_model
                
                # Mock fit method
                mock_model.fit.return_value = None
                
                # Mock make_future_dataframe
                import pandas as pd
                future_df = pd.DataFrame({
                    'ds': pd.date_range(start=datetime.utcnow(), periods=7, freq='D')
                })
                mock_model.make_future_dataframe.return_value = future_df
                
                # Mock predict method
                forecast_df = pd.DataFrame({
                    'ds': future_df['ds'],
                    'yhat': [25.0] * 7,  # Predicted values
                    'yhat_lower': [20.0] * 7,
                    'yhat_upper': [30.0] * 7
                })
                mock_model.predict.return_value = forecast_df
                
                # Trigger the event processing
                await self.event_bus.publish(test_event)
                
                # Wait a bit for async processing
                await asyncio.sleep(0.1)

        # Verify that a MaintenancePredictedEvent was published
        self.assertEqual(len(published_events), 1)
        published_event = published_events[0]
        self.assertIsInstance(published_event, MaintenancePredictedEvent)
        
        # Verify event content
        self.assertEqual(published_event.equipment_id, "equipment_sensor_temp_001")
        self.assertIsNotNone(published_event.predicted_failure_date)
        self.assertIsNotNone(published_event.time_to_failure_days)
        self.assertIn(published_event.maintenance_type, ["urgent_corrective", "preventive", "inspection"])
        self.assertIsInstance(published_event.recommended_actions, list)
        self.assertGreater(len(published_event.recommended_actions), 0)

        # Verify the original event correlation is maintained
        self.assertEqual(published_event.correlation_id, test_event.correlation_id)

    async def test_low_confidence_anomaly_skipped(self):
        """Test that low confidence anomalies are skipped for prediction."""
        # Create a low confidence event
        test_event = self._create_anomaly_validated_event(
            validation_status="false_positive",
            final_confidence=0.4
        )
        
        # Track published events
        published_events = []
        
        async def capture_published_event(event):
            published_events.append(event)
        
        await self.event_bus.subscribe(
            event_type_name="MaintenancePredictedEvent",
            handler=capture_published_event
        )

        # Trigger the event processing
        await self.event_bus.publish(test_event)
        
        # Wait a bit for async processing
        await asyncio.sleep(0.1)

        # Verify that no prediction event was published
        self.assertEqual(len(published_events), 0)

    async def test_insufficient_historical_data_handling(self):
        """Test handling when there's insufficient historical data."""
        # Setup insufficient mock historical data (less than min_historical_points)
        mock_historical_readings = self._create_historical_sensor_readings(3)  # Less than threshold
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = mock_historical_readings

        # Create a valid anomaly event
        test_event = self._create_anomaly_validated_event()
        
        # Track published events
        published_events = []
        
        async def capture_published_event(event):
            published_events.append(event)
        
        await self.event_bus.subscribe(
            event_type_name="MaintenancePredictedEvent",
            handler=capture_published_event
        )

        # Mock SensorReading.model_validate
        with patch('data.schemas.SensorReading.model_validate') as mock_validate:
            mock_validate.side_effect = lambda x: SensorReading(
                id=x.id,
                sensor_id=x.sensor_id,
                sensor_type="temperature",
                value=x.value,
                unit="C",
                timestamp=x.timestamp,
                quality=0.95
            )

            # Trigger the event processing
            await self.event_bus.publish(test_event)
            
            # Wait a bit for async processing
            await asyncio.sleep(0.1)

        # Verify that no prediction event was published due to insufficient data
        self.assertEqual(len(published_events), 0)

    async def test_agent_subscription_and_capability_registration(self):
        """Test that the agent properly registers capabilities and subscribes to events."""
        # Check that capabilities are registered
        self.assertIsNotNone(self.agent.capabilities)
        self.assertGreater(len(self.agent.capabilities), 0)
        
        # Check that the agent has subscribed to the correct event type
        subscriptions = self.event_bus.subscriptions.get("AnomalyValidatedEvent", [])
        self.assertGreater(len(subscriptions), 0)
        
        # Verify that our agent's process method is in the subscriptions
        handler_functions = [handler.__name__ for handler in subscriptions]
        self.assertIn("process", handler_functions)

    async def test_database_session_lifecycle(self):
        """Test that database sessions are properly managed."""
        # Setup mock historical data
        mock_historical_readings = self._create_historical_sensor_readings(10)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = mock_historical_readings

        # Create a valid anomaly event
        test_event = self._create_anomaly_validated_event()

        # Mock SensorReading.model_validate
        with patch('data.schemas.SensorReading.model_validate') as mock_validate:
            mock_validate.side_effect = lambda x: SensorReading(
                id=x.id,
                sensor_id=x.sensor_id,
                sensor_type="temperature",
                value=x.value,
                unit="C",
                timestamp=x.timestamp,
                quality=0.95
            )

            # Trigger the event processing
            await self.event_bus.publish(test_event)
            
            # Wait a bit for async processing
            await asyncio.sleep(0.1)

        # Verify that the database session factory was called
        self.mock_db_session_factory.assert_called()
        
        # Verify that the session was closed
        self.mock_db_session.close.assert_called()
