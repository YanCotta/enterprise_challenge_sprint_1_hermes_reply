"""
Full end-to-end workflow integration test for the smart maintenance SaaS platform.

This test verifies the complete event-driven pipeline:
SensorDataReceivedEvent → DataAcquisitionAgent → DataProcessedEvent → 
AnomalyDetectionAgent → AnomalyDetectedEvent → ValidationAgent → 
AnomalyValidatedEvent → PredictionAgent → MaintenancePredictedEvent

Tests include:
- Event flow and agent communication
- Correlation ID propagation
- Event payload compatibility
- Mocked dependencies for isolated testing
"""

import asyncio
import unittest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Event models and bus
from core.events.event_bus import EventBus
from core.events.event_models import (
    SensorDataReceivedEvent,
    DataProcessedEvent,
    AnomalyDetectedEvent,
    AnomalyValidatedEvent,
    MaintenancePredictedEvent,
)

# Agents
from apps.agents.core.data_acquisition_agent import DataAcquisitionAgent
from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from apps.agents.core.validation_agent import ValidationAgent
from apps.agents.decision.prediction_agent import PredictionAgent

# Data models and processors
from data.schemas import SensorReading, SensorReadingCreate, SensorType
from data.validators.agent_data_validator import DataValidator
from data.processors.agent_data_enricher import DataEnricher


class TestFullWorkflowIntegration(unittest.IsolatedAsyncioTestCase):
    """Test the complete event-driven workflow from sensor data to maintenance prediction."""

    async def asyncSetUp(self):
        """Set up the test environment with all agents and mocked dependencies."""
        # Initialize EventBus
        self.event_bus = EventBus()
        
        # Storage for captured events (for verification)
        self.captured_events = {
            'DataProcessedEvent': [],
            'AnomalyDetectedEvent': [],
            'AnomalyValidatedEvent': [],
            'MaintenancePredictedEvent': [],
        }
        
        # Set up event handlers to capture published events
        await self._setup_event_handlers()
        
        # Initialize agents with mocked dependencies
        await self._setup_agents()
        
        # Set correlation ID for end-to-end tracking
        self.test_correlation_id = f"e2e-test-{uuid4()}"

    async def _setup_event_handlers(self):
        """Set up event handlers to capture published events for verification."""
        
        async def capture_data_processed_event(event: DataProcessedEvent):
            self.captured_events['DataProcessedEvent'].append(event)
            
        async def capture_anomaly_detected_event(event: AnomalyDetectedEvent):
            self.captured_events['AnomalyDetectedEvent'].append(event)
            
        async def capture_anomaly_validated_event(event: AnomalyValidatedEvent):
            self.captured_events['AnomalyValidatedEvent'].append(event)
            
        async def capture_maintenance_predicted_event(event: MaintenancePredictedEvent):
            self.captured_events['MaintenancePredictedEvent'].append(event)
        
        # Subscribe to all events for capturing
        await self.event_bus.subscribe(DataProcessedEvent.__name__, capture_data_processed_event)
        await self.event_bus.subscribe(AnomalyDetectedEvent.__name__, capture_anomaly_detected_event)
        await self.event_bus.subscribe(AnomalyValidatedEvent.__name__, capture_anomaly_validated_event)
        await self.event_bus.subscribe(MaintenancePredictedEvent.__name__, capture_maintenance_predicted_event)

    async def _setup_agents(self):
        """Initialize all agents with mocked dependencies."""
        
        # Mock DataValidator for DataAcquisitionAgent
        self.mock_validator = MagicMock(spec=DataValidator)
        
        # Mock DataEnricher for DataAcquisitionAgent
        self.mock_enricher = MagicMock(spec=DataEnricher)
        
        # Set up dynamic mocks that will use actual input data
        self._setup_dynamic_mocks()
        
        # Initialize DataAcquisitionAgent
        self.data_acquisition_agent = DataAcquisitionAgent(
            agent_id="test-daq-agent",
            event_bus=self.event_bus,
            validator=self.mock_validator,
            enricher=self.mock_enricher
        )
        
        # Initialize AnomalyDetectionAgent with test settings
        anomaly_settings = {
            'isolation_forest_params': {'random_state': 42, 'n_estimators': 10},
            'statistical_detector_config': {'threshold_std_dev': 2.0}
        }
        self.anomaly_detection_agent = AnomalyDetectionAgent(
            agent_id="test-anomaly-agent",
            event_bus=self.event_bus,
            specific_settings=anomaly_settings
        )
        
        # Mock dependencies for ValidationAgent
        from core.database.crud.crud_sensor_reading import CRUDSensorReading
        from apps.rules.validation_rules import RuleEngine
        
        self.mock_crud_sensor_reading = AsyncMock(spec=CRUDSensorReading)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = self._create_mock_historical_readings()
        
        self.mock_rule_engine = MagicMock(spec=RuleEngine)
        self.mock_rule_engine.evaluate_rules = AsyncMock(return_value=(0.0, ["Rule reason: no adjustment needed"]))
        
        self.mock_db_session_factory = MagicMock()
        
        # Initialize ValidationAgent
        self.validation_agent = ValidationAgent(
            agent_id="test-validation-agent",
            event_bus=self.event_bus,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            rule_engine=self.mock_rule_engine,
            db_session_factory=self.mock_db_session_factory
        )

        # Mock Prophet and database access for PredictionAgent
        with patch('apps.agents.decision.prediction_agent.Prophet') as mock_prophet_class:
            
            # Mock Prophet model
            mock_prophet_instance = MagicMock()
            mock_prophet_instance.fit.return_value = mock_prophet_instance
            mock_prophet_instance.make_future_dataframe.return_value = self._create_mock_future_dataframe()
            mock_prophet_instance.predict.return_value = self._create_mock_prophet_forecast()
            mock_prophet_class.return_value = mock_prophet_instance
            
            # Mock database session and CRUD for PredictionAgent
            self.mock_pred_crud_sensor_reading = AsyncMock(spec=CRUDSensorReading)
            self.mock_pred_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = self._create_mock_historical_readings()
            
            self.mock_pred_db_session_factory = MagicMock()
            
            # Initialize PredictionAgent
            prediction_settings = {
                'historical_data_limit': 50,
                'min_historical_points': 10,
                'prediction_horizon_days': 30,
                'confidence_threshold': 0.5
            }
            self.prediction_agent = PredictionAgent(
                agent_id="test-prediction-agent",
                event_bus=self.event_bus,
                crud_sensor_reading=self.mock_pred_crud_sensor_reading,
                db_session_factory=self.mock_pred_db_session_factory,
                specific_settings=prediction_settings
            )
            
            # Store mocks for later use
            self.mock_prophet_class = mock_prophet_class

        # Start all agents
        await self.data_acquisition_agent.start()
        await self.anomaly_detection_agent.start()
        await self.validation_agent.start()
        await self.prediction_agent.start()

    def _create_mock_sensor_reading_create(self):
        """Create a mock SensorReadingCreate object."""
        from data.schemas import SensorReadingCreate
        return SensorReadingCreate(
            sensor_id="temp_sensor_001",
            value=85.5,  # High temperature to trigger anomaly
            timestamp=datetime.now(timezone.utc),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=0.95,
            metadata={"location": "factory_floor_A", "equipment_id": "pump_001"}
        )

    def _create_mock_sensor_reading(self):
        """Create a mock enriched SensorReading object."""
        return SensorReading(
            sensor_id="temp_sensor_001",
            value=85.5,  # High temperature to trigger anomaly
            timestamp=datetime.now(timezone.utc),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=0.95,
            correlation_id=uuid4(),
            metadata={"location": "factory_floor_A", "equipment_id": "pump_001"}
        )

    def _create_mock_historical_readings(self) -> List[SensorReading]:
        """Create mock historical sensor readings for validation and prediction."""
        base_time = datetime.now(timezone.utc) - timedelta(hours=48)
        readings = []
        
        # Create 30 historical readings with normal values (around 22-25°C)
        for i in range(30):
            reading_time = base_time + timedelta(hours=i * 1.5)
            # Normal temperature range with slight variation
            normal_value = 22.0 + (i % 5) * 0.5 + (i % 3) * 0.2
            
            readings.append(SensorReading(
                sensor_id="temp_sensor_001",
                value=normal_value,
                timestamp=reading_time,
                sensor_type=SensorType.TEMPERATURE,
                unit="celsius",
                quality=0.9 + (i % 10) * 0.01,
                correlation_id=uuid4(),
                metadata={"location": "factory_floor_A", "equipment_id": "pump_001"}
            ))
        
        return readings

    def _create_mock_future_dataframe(self):
        """Create a mock future dataframe for Prophet."""
        import pandas as pd
        future_dates = pd.date_range(
            start=datetime.now(timezone.utc),
            periods=30,
            freq='D'
        )
        return pd.DataFrame({'ds': future_dates})

    def _create_mock_prophet_forecast(self):
        """Create a mock Prophet forecast result."""
        import pandas as pd
        import numpy as np
        
        future_dates = pd.date_range(
            start=datetime.now(timezone.utc),
            periods=30,
            freq='D'
        )
        
        # Simulate increasing trend toward failure
        base_values = np.linspace(25, 95, 30)  # Temperature increasing toward critical
        noise = np.random.normal(0, 2, 30)
        
        return pd.DataFrame({
            'ds': future_dates,
            'yhat': base_values + noise,
            'yhat_lower': base_values + noise - 5,
            'yhat_upper': base_values + noise + 5,
            'trend': base_values
        })

    async def asyncTearDown(self):
        """Clean up after tests."""
        # Stop all agents
        await self.data_acquisition_agent.stop()
        await self.anomaly_detection_agent.stop()
        await self.validation_agent.stop()
        await self.prediction_agent.stop()

    async def test_complete_workflow_with_anomaly_and_prediction(self):
        """Test the complete workflow from sensor data to maintenance prediction."""
        
        # Clear captured events
        for event_list in self.captured_events.values():
            event_list.clear()
        
        # Create initial sensor data event (high temperature to trigger anomaly)
        sensor_data = {
            "sensor_id": "sensor_temp_001",  # Use a sensor with known historical data
            "value": 85.5,  # High temperature (baseline is 22.5 ± 2.1, so this is clearly anomalous)
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"location": "factory_floor_A", "equipment_id": "pump_001"}
        }
        
        initial_event = SensorDataReceivedEvent(
            raw_data=sensor_data,
            correlation_id=self.test_correlation_id
        )
        
        # Publish the initial event to start the workflow
        await self.event_bus.publish(initial_event)
        
        # Wait for all async processing to complete
        await asyncio.sleep(2.0)  # Increased wait time for more complex processing
        
        # Verify DataProcessedEvent was published
        self.assertEqual(len(self.captured_events['DataProcessedEvent']), 1)
        data_processed_event = self.captured_events['DataProcessedEvent'][0]
        self.assertEqual(data_processed_event.correlation_id, self.test_correlation_id)
        self.assertEqual(data_processed_event.source_sensor_id, "sensor_temp_001")
        self.assertIsInstance(data_processed_event.processed_data, dict)
        
        # Verify AnomalyDetectedEvent was published
        self.assertGreaterEqual(len(self.captured_events['AnomalyDetectedEvent']), 1)
        anomaly_event = self.captured_events['AnomalyDetectedEvent'][0]
        self.assertEqual(anomaly_event.correlation_id, self.test_correlation_id)
        self.assertIsInstance(anomaly_event.anomaly_details, dict)
        self.assertIsInstance(anomaly_event.triggering_data, dict)
        self.assertEqual(anomaly_event.anomaly_details['sensor_id'], "sensor_temp_001")
        
        # Verify AnomalyValidatedEvent was published
        self.assertGreaterEqual(len(self.captured_events['AnomalyValidatedEvent']), 1)
        validated_event = self.captured_events['AnomalyValidatedEvent'][0]
        self.assertEqual(validated_event.correlation_id, self.test_correlation_id)
        self.assertIsInstance(validated_event.original_anomaly_alert_payload, dict)
        self.assertIsInstance(validated_event.triggering_reading_payload, dict)
        self.assertIn(validated_event.validation_status, ['credible_anomaly', 'further_investigation_needed'])
        self.assertIsInstance(validated_event.final_confidence, float)
        self.assertGreaterEqual(validated_event.final_confidence, 0.0)
        self.assertLessEqual(validated_event.final_confidence, 1.0)
        
        # Verify MaintenancePredictedEvent was published (if confidence threshold met)
        if validated_event.final_confidence >= 0.5:  # Agent's confidence threshold
            self.assertGreaterEqual(len(self.captured_events['MaintenancePredictedEvent']), 1)
            maintenance_event = self.captured_events['MaintenancePredictedEvent'][0]
            self.assertEqual(maintenance_event.correlation_id, self.test_correlation_id)
            self.assertEqual(maintenance_event.equipment_id, "pump_001")
            self.assertIsInstance(maintenance_event.predicted_failure_date, datetime)
            self.assertIsInstance(maintenance_event.time_to_failure_days, float)
            self.assertGreaterEqual(maintenance_event.time_to_failure_days, 0.0)
            self.assertIsInstance(maintenance_event.prediction_confidence, float)
            self.assertGreaterEqual(maintenance_event.prediction_confidence, 0.0)
            self.assertLessEqual(maintenance_event.prediction_confidence, 1.0)

    async def test_workflow_with_normal_sensor_data(self):
        """Test the workflow with normal sensor data that shouldn't trigger anomalies."""
        
        # Clear captured events
        for event_list in self.captured_events.values():
            event_list.clear()
        
        # Update mocks to return normal temperature
        normal_reading_create = SensorReadingCreate(
            sensor_id="temp_sensor_001",
            value=23.0,  # Normal temperature
            timestamp=datetime.now(timezone.utc),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=0.95,
            metadata={"location": "factory_floor_A", "equipment_id": "pump_001"}
        )
        
        normal_reading = SensorReading(
            sensor_id="temp_sensor_001",
            value=23.0,  # Normal temperature
            timestamp=datetime.now(timezone.utc),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=0.95,
            correlation_id=uuid4(),
            metadata={"location": "factory_floor_A", "equipment_id": "pump_001"}
        )
        
        self.mock_validator.validate.return_value = normal_reading_create
        self.mock_enricher.enrich.return_value = normal_reading
        
        # Create sensor data event with normal temperature
        sensor_data = {
            "sensor_id": "temp_sensor_001",
            "value": 23.0,  # Normal temperature
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"location": "factory_floor_A", "equipment_id": "pump_001"}
        }
        
        normal_correlation_id = f"normal-test-{uuid4()}"
        initial_event = SensorDataReceivedEvent(
            raw_data=sensor_data,
            correlation_id=normal_correlation_id
        )
        
        # Publish the initial event
        await self.event_bus.publish(initial_event)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Verify DataProcessedEvent was published
        self.assertEqual(len(self.captured_events['DataProcessedEvent']), 1)
        data_processed_event = self.captured_events['DataProcessedEvent'][0]
        self.assertEqual(data_processed_event.correlation_id, normal_correlation_id)
        
        # Verify no anomaly was detected (normal data shouldn't trigger anomalies)
        # Note: This depends on the anomaly detection algorithm and thresholds
        anomaly_events_for_normal = [
            event for event in self.captured_events['AnomalyDetectedEvent']
            if event.correlation_id == normal_correlation_id
        ]
        # Should be 0 or very low confidence
        if anomaly_events_for_normal:
            # If an anomaly event was published, it should have low confidence
            anomaly_event = anomaly_events_for_normal[0]
            self.assertLess(anomaly_event.anomaly_details.get('confidence', 1.0), 0.5)

    async def test_correlation_id_propagation(self):
        """Test that correlation_id is properly propagated through the entire workflow."""
        
        # Clear captured events
        for event_list in self.captured_events.values():
            event_list.clear()
        
        test_correlation_id = f"correlation-test-{uuid4()}"
        
        # Create sensor data event
        sensor_data = {
            "sensor_id": "temp_sensor_001",
            "value": 85.5,  # High temperature
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"location": "factory_floor_A", "equipment_id": "pump_001"}
        }
        
        initial_event = SensorDataReceivedEvent(
            raw_data=sensor_data,
            correlation_id=test_correlation_id
        )
        
        # Publish the event
        await self.event_bus.publish(initial_event)
        
        # Wait for processing
        await asyncio.sleep(1.0)
        
        # Verify correlation_id propagation through all events
        all_events = []
        for event_type, events in self.captured_events.items():
            all_events.extend([(event_type, event) for event in events])
        
        # Filter events for our test correlation ID
        our_events = [(event_type, event) for event_type, event in all_events 
                     if getattr(event, 'correlation_id', None) == test_correlation_id]
        
        # Should have at least DataProcessedEvent
        self.assertGreater(len(our_events), 0)
        
        # All events should have the same correlation_id
        for event_type, event in our_events:
            self.assertEqual(
                event.correlation_id, 
                test_correlation_id, 
                f"Event {event_type} has incorrect correlation_id"
            )

    async def test_agent_error_handling(self):
        """Test workflow behavior when agents encounter errors."""
        
        # Clear captured events
        for event_list in self.captured_events.values():
            event_list.clear()
        
        # Mock validator to raise an exception
        self.mock_validator.validate.side_effect = Exception("Validation failed")
        
        # Create sensor data event
        sensor_data = {
            "sensor_id": "temp_sensor_001",
            "value": 85.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        error_correlation_id = f"error-test-{uuid4()}"
        error_event = SensorDataReceivedEvent(
            raw_data=sensor_data,
            correlation_id=error_correlation_id
        )
        
        # Publish the event
        await self.event_bus.publish(error_event)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Should not have published DataProcessedEvent due to validation error
        processed_events_for_error = [
            event for event in self.captured_events['DataProcessedEvent']
            if event.correlation_id == error_correlation_id
        ]
        self.assertEqual(len(processed_events_for_error), 0)
        
        # Reset mock for other tests
        self.mock_validator.validate.side_effect = None
        self.mock_validator.validate.reset_mock()
        # Don't call _setup_dynamic_mocks here as it will be called by the next test setUp

    async def test_event_payload_compatibility(self):
        """Test that event payloads are compatible between agents."""
        
        # Clear captured events
        for event_list in self.captured_events.values():
            event_list.clear()
        
        # Create and publish sensor data event
        sensor_data = {
            "sensor_id": "temp_sensor_001",
            "value": 85.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"location": "factory_floor_A", "equipment_id": "pump_001"}
        }
        
        payload_correlation_id = f"payload-test-{uuid4()}"
        initial_event = SensorDataReceivedEvent(
            raw_data=sensor_data,
            correlation_id=payload_correlation_id
        )
        
        await self.event_bus.publish(initial_event)
        await asyncio.sleep(1.0)
        
        # Verify DataProcessedEvent payload structure
        data_processed_events = [
            event for event in self.captured_events['DataProcessedEvent']
            if event.correlation_id == payload_correlation_id
        ]
        if data_processed_events:
            event = data_processed_events[0]
            self.assertIsInstance(event.processed_data, dict)
            self.assertIn('sensor_id', event.processed_data)
            self.assertIn('value', event.processed_data)
            self.assertIn('timestamp', event.processed_data)
        
        # Verify AnomalyDetectedEvent payload structure
        anomaly_events = [
            event for event in self.captured_events['AnomalyDetectedEvent']
            if event.correlation_id == payload_correlation_id
        ]
        if anomaly_events:
            event = anomaly_events[0]
            self.assertIsInstance(event.anomaly_details, dict)
            self.assertIsInstance(event.triggering_data, dict)
            # Check required fields in anomaly_details
            self.assertIn('sensor_id', event.anomaly_details)
            self.assertIn('confidence', event.anomaly_details)
            self.assertIn('severity', event.anomaly_details)
        
        # Verify AnomalyValidatedEvent payload structure
        validated_events = [
            event for event in self.captured_events['AnomalyValidatedEvent']
            if event.correlation_id == payload_correlation_id
        ]
        if validated_events:
            event = validated_events[0]
            self.assertIsInstance(event.original_anomaly_alert_payload, dict)
            self.assertIsInstance(event.triggering_reading_payload, dict)
            self.assertIsInstance(event.validation_status, str)
            self.assertIsInstance(event.final_confidence, float)
            self.assertIsInstance(event.validation_reasons, list)

    def _setup_dynamic_mocks(self):
        """Set up dynamic mocks that use actual input data."""
        def mock_validate(raw_data, correlation_id=None):
            """Mock validator that uses actual input data."""
            from data.schemas import SensorReadingCreate
            return SensorReadingCreate(
                sensor_id=raw_data.get("sensor_id", "unknown_sensor"),
                value=raw_data.get("value", 0.0),
                timestamp=datetime.fromisoformat(raw_data.get("timestamp", datetime.now(timezone.utc).isoformat())),
                sensor_type=SensorType.TEMPERATURE,  # Default for test
                unit="celsius",
                quality=0.95,
                metadata=raw_data.get("metadata", {})
            )
        
        def mock_enrich(sensor_reading_create):
            """Mock enricher that uses actual input data."""
            data = sensor_reading_create.model_dump()
            return SensorReading(
                **data,
                ingestion_timestamp=datetime.now(timezone.utc)
            )
        
        # Reset and configure the validator mock
        self.mock_validator.validate.reset_mock()
        self.mock_validator.validate.side_effect = None
        self.mock_validator.validate.return_value = None
        self.mock_validator.validate.side_effect = mock_validate
        
        self.mock_enricher.enrich = mock_enrich


if __name__ == '__main__':
    unittest.main()
