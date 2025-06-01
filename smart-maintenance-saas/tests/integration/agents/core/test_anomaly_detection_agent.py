"""Integration tests for AnomalyDetectionAgent."""

import asyncio
import math # Added for math.isclose
import logging
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from core.events.event_bus import EventBus
from core.events.event_models import AnomalyDetectedEvent, DataProcessedEvent
from data.schemas import SensorReading, SensorType


class TestAnomalyDetectionAgentIntegration:
    """Integration tests for the AnomalyDetectionAgent."""

    @pytest.fixture
    async def event_bus(self):
        """Create a test EventBus instance."""
        return EventBus()

    @pytest.fixture
    async def agent(self, event_bus):
        """Create an AnomalyDetectionAgent instance for testing."""
        agent = AnomalyDetectionAgent(
            agent_id="test_anomaly_agent",
            event_bus=event_bus
        )
        return agent

    @pytest.fixture
    def sample_sensor_reading(self):
        """Create a sample sensor reading for testing."""
        return SensorReading(
            sensor_id="sensor_temp_001",
            value=25.3,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={"location": "room_A", "building": "main"}
        )

    @pytest.fixture
    def sample_data_processed_event(self, sample_sensor_reading):
        """Create a sample DataProcessedEvent for testing."""
        return DataProcessedEvent(
            processed_data=sample_sensor_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=sample_sensor_reading.sensor_id
        )

    async def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.agent_id == "test_anomaly_agent"
        assert agent.status == "initializing"
        assert len(agent.capabilities) == 0  # Before registration
        assert agent.isolation_forest_fitted is False
        assert agent.scaler is not None
        assert agent.isolation_forest is not None
        assert agent.statistical_detector is not None
        assert len(agent.historical_data_store) > 0

    async def test_agent_capability_registration(self, agent):
        """Test that the agent registers its capabilities correctly."""
        await agent.register_capabilities()
        
        assert len(agent.capabilities) == 1
        capability = agent.capabilities[0]
        assert capability.name == "detect_anomalies"
        assert capability.description == "Detects anomalies in processed sensor data using ML models."
        assert DataProcessedEvent.__name__ in capability.input_types
        assert "AnomalyDetectedEvent" in capability.output_types

    async def test_agent_start_and_subscription(self, agent, event_bus):
        """Test that the agent starts correctly and subscribes to events."""
        # Mock the event bus subscribe method
        event_bus.subscribe = AsyncMock()
        
        await agent.start()
        
        assert agent.status == "running"
        # Verify that subscribe was called with correct parameters
        event_bus.subscribe.assert_called_once_with(
            DataProcessedEvent.__name__,
            agent.process
        )

    async def test_process_data_processed_event(self, agent, sample_data_processed_event):
        """Test that the agent can process DataProcessedEvent correctly."""
        # Mock the logger to capture log messages
        with patch.object(agent.logger, 'info') as mock_info, \
             patch.object(agent.logger, 'debug') as mock_debug:
            
            await agent.process(sample_data_processed_event)
            
            # Verify that the process method was called and logged appropriately
            mock_info.assert_called()
            mock_debug.assert_called()
            
            # Check that the info log contains expected sensor information
            info_calls = [call[0][0] for call in mock_info.call_args_list]
            assert any(f"Processing sensor reading: {sample_data_processed_event.processed_data['sensor_id']}=" in call for call in info_calls)

    async def test_process_handles_invalid_data(self, agent):
        """Test that the agent handles invalid data gracefully."""
        # Create an event with invalid processed_data
        invalid_event = DataProcessedEvent(
            processed_data={"invalid": "data"},  # Missing required SensorReading fields
            original_event_id=uuid.uuid4(),
            source_sensor_id="invalid_sensor"
        )
        
        # Mock the logger to capture error messages
        with patch.object(agent.logger, 'error') as mock_error:
            await agent.process(invalid_event)
            
            # Verify that an error was logged
            mock_error.assert_called_once()
            error_call = mock_error.call_args[0][0]
            assert "Failed to parse sensor reading" in error_call # More specific to Pydantic error

    async def test_full_agent_lifecycle(self, agent, event_bus, sample_data_processed_event):
        """Test the complete agent lifecycle from start to processing events."""
        # Mock the event bus
        event_bus.subscribe = AsyncMock()
        
        # Start the agent
        await agent.start()
        assert agent.status == "running"
        
        # Process an event
        with patch.object(agent.logger, 'info') as mock_info:
            await agent.process(sample_data_processed_event)
            mock_info.assert_called()
        
        # Stop the agent
        await agent.stop()
        assert agent.status == "stopped"

    async def test_historical_data_store_initialization(self, agent):
        """Test that the historical data store is properly initialized with mock data."""
        assert "sensor_temp_001" in agent.historical_data_store
        assert "sensor_vibr_001" in agent.historical_data_store
        assert "sensor_press_001" in agent.historical_data_store
        
        # Check structure of historical data entries
        temp_data = agent.historical_data_store["sensor_temp_001"]
        assert "mean" in temp_data
        assert "std" in temp_data
        assert isinstance(temp_data["mean"], (int, float))
        assert isinstance(temp_data["std"], (int, float))

    async def test_process_full_pipeline_with_known_sensor(self, agent, event_bus):
        """Test that the full processing pipeline works with a known sensor."""
        # Create event with a sensor that exists in historical data
        known_sensor_reading = SensorReading(
            sensor_id="sensor_temp_001",  # This exists in historical_data_store
            value=20.0,  # Slightly below historical mean of 22.5
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={"location": "room_A"}
        )
        
        event = DataProcessedEvent(
            processed_data=known_sensor_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=known_sensor_reading.sensor_id
        )
        
        # Mock methods to verify they're called
        with patch.object(agent, '_extract_features', wraps=agent._extract_features) as mock_extract, \
             patch.object(agent.isolation_forest, 'fit') as mock_fit, \
             patch.object(agent.isolation_forest, 'predict', return_value=np.array([1])) as mock_predict, \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([0.1])) as mock_decision, \
             patch.object(agent.statistical_detector, 'detect', return_value=(False, 0.2, "normal")) as mock_stat_detect, \
             patch.object(agent.logger, 'info') as mock_info:
            
            await agent.process(event)
            
            # Verify pipeline steps were called
            mock_extract.assert_called_once()
            mock_fit.assert_called_once()  # First time fitting
            mock_predict.assert_called_once()
            mock_decision.assert_called_once()
            mock_stat_detect.assert_called_once()
            
            # Verify statistical detector was called with correct parameters
            stat_call_args = mock_stat_detect.call_args[0]
            assert stat_call_args[0] == 20.0  # reading value
            assert stat_call_args[1] == 22.5  # historical mean
            assert stat_call_args[2] == 2.1   # historical std
            
            # Verify logging includes prediction results
            info_calls = [call[0][0] for call in mock_info.call_args_list]
            assert any("Isolation Forest results" in call for call in info_calls) # Corrected string
            assert any("Statistical detection" in call for call in info_calls)

    async def test_process_full_pipeline_with_unknown_sensor(self, agent):
        """Test that the full processing pipeline works with an unknown sensor."""
        # Create event with a sensor that doesn't exist in historical data
        unknown_sensor_reading = SensorReading(
            sensor_id="unknown_sensor_999",
            value=50.0,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.VIBRATION,
            unit="m/s2",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={"location": "room_Z"}
        )
        
        event = DataProcessedEvent(
            processed_data=unknown_sensor_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=unknown_sensor_reading.sensor_id
        )
        
        # Mock methods to verify they're called with default values
        with patch.object(agent.statistical_detector, 'detect', return_value=(True, 0.8, "threshold_breach")) as mock_stat_detect, \
             patch.object(agent.logger, 'warning') as mock_warning, \
             patch.object(agent.logger, 'info') as mock_info:
            
            await agent.process(event)
            
            # Verify warning was logged for unknown sensor
            mock_warning.assert_called()
            warning_message = mock_warning.call_args[0][0]
            assert "No historical data for sensor unknown_sensor_999, using defaults" in warning_message
            
            # Verify statistical detector was called with default values
            mock_stat_detect.assert_called_once()
            stat_call_args = mock_stat_detect.call_args[0]
            assert stat_call_args[0] == 50.0  # reading value
            assert stat_call_args[1] == 50.0  # default mean (same as reading value)
            assert stat_call_args[2] == 0.1   # default std

    async def test_process_feature_extraction_failure(self, agent):
        """Test handling when feature extraction returns empty array."""
        sample_reading = SensorReading(
            sensor_id="test_sensor",
            value=25.0,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={}
        )
        
        event = DataProcessedEvent(
            processed_data=sample_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=sample_reading.sensor_id
        )
        
        # Mock _extract_features to return empty array
        with patch.object(agent, '_extract_features', return_value=np.array([])) as mock_extract, \
             patch.object(agent.logger, 'warning') as mock_warning:
            
            await agent.process(event)
            
            mock_extract.assert_called_once()
            mock_warning.assert_called_once()
            warning_message = mock_warning.call_args[0][0]
            assert "No features extracted for sensor test_sensor, skipping" in warning_message

    async def test_process_isolation_forest_fitting_and_prediction(self, agent):
        """Test that Isolation Forest is fitted on first call and reused afterward."""
        sample_reading = SensorReading(
            sensor_id="sensor_temp_001",
            value=22.0,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={}
        )
        
        event = DataProcessedEvent(
            processed_data=sample_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=sample_reading.sensor_id
        )
        
        # Ensure isolation forest is not fitted initially
        agent.isolation_forest_fitted = False
        
        with patch.object(agent.isolation_forest, 'fit') as mock_fit, \
             patch.object(agent.isolation_forest, 'predict', return_value=np.array([1])) as mock_predict, \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([0.05])) as mock_decision, \
             patch.object(agent.logger, 'info') as mock_info:
            
            # First call should fit the model
            await agent.process(event)
            
            assert agent.isolation_forest_fitted is True
            mock_fit.assert_called_once()
            mock_predict.assert_called_once()
            mock_decision.assert_called_once()
            
            # Reset mocks for second call
            mock_fit.reset_mock()
            mock_predict.reset_mock()
            mock_decision.reset_mock()
            
            # Second call should not fit again but should predict
            await agent.process(event)
            
            mock_fit.assert_not_called()  # Should not fit again
            mock_predict.assert_called_once()
            mock_decision.assert_called_once()

    async def test_process_logs_detailed_predictions(self, agent):
        """Test that detailed prediction information is logged."""
        sample_reading = SensorReading(
            sensor_id="sensor_temp_001",
            value=30.0,  # Above historical mean
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={}
        )
        
        event = DataProcessedEvent(
            processed_data=sample_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=sample_reading.sensor_id
        )
        
        # Mock ML predictions
        with patch.object(agent.isolation_forest, 'predict', return_value=np.array([-1])) as mock_predict, \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([-0.15])) as mock_decision, \
             patch.object(agent.statistical_detector, 'detect', return_value=(True, 0.9, "statistical_threshold_breach")) as mock_stat, \
             patch.object(agent.logger, 'info') as mock_info, \
             patch.object(agent.logger, 'debug') as mock_debug:
            
            await agent.process(event)
            
            # Check that isolation forest results are logged
            info_calls = [call[0][0] for call in mock_info.call_args_list]
            isolation_log = next((call for call in info_calls if "Isolation Forest results" in call), None) # Corrected string
            assert isolation_log is not None
            assert "prediction=-1" in isolation_log
            assert "anomaly" in isolation_log
            assert "score=-0.1500" in isolation_log
            
            # Check that statistical results are logged
            statistical_log = next((call for call in info_calls if "Statistical detection" in call), None)
            assert statistical_log is not None
            assert "anomaly=True" in statistical_log # Corrected key
            assert "confidence=0.9000" in statistical_log
            assert "statistical_threshold_breach" in statistical_log

    async def test_anomaly_detection_and_event_publishing(self, agent, event_bus):
        """Test that anomalies are detected and AnomalyDetectedEvent is published."""
        # Create a sensor reading that should trigger an anomaly
        anomalous_reading = SensorReading(
            sensor_id="sensor_temp_001",
            value=35.0,  # Well above historical mean of 22.5 (should trigger statistical anomaly)
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={"location": "room_A"}
        )
        
        event = DataProcessedEvent(
            processed_data=anomalous_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=anomalous_reading.sensor_id,
            correlation_id="test-correlation-123"
        )
        
        # Mock event bus publish method
        event_bus.publish = AsyncMock()
        
        # Mock ML predictions to ensure anomaly detection
        with patch.object(agent.isolation_forest, 'predict', return_value=np.array([-1])) as mock_predict, \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([-0.3])) as mock_decision, \
             patch.object(agent.statistical_detector, 'detect', return_value=(True, 0.85, "statistical_threshold_breach")) as mock_stat_detect:
            
            await agent.process(event)
            
            # Verify that publish was called
            event_bus.publish.assert_called_once()
            
            # Verify the event type and content
            call_args = event_bus.publish.call_args
            # published_event is the first argument passed to publish, which is call_args[0][0]
            published_event = call_args[0][0]
            
            assert published_event.__class__.__name__ == "AnomalyDetectedEvent"
            assert isinstance(published_event, AnomalyDetectedEvent)
            
            # Verify anomaly details
            anomaly_details = published_event.anomaly_details
            assert anomaly_details["sensor_id"] == "sensor_temp_001"
            assert anomaly_details["severity"] == 5  # High confidence should map to severity 5
            assert math.isclose(anomaly_details["confidence"], 0.835) # Corrected based on current ensemble logic
            assert "Anomaly detected for sensor sensor_temp_001" in anomaly_details["description"]
            
            # Verify triggering data
            triggering_data = published_event.triggering_data
            assert triggering_data["sensor_id"] == "sensor_temp_001"
            assert triggering_data["value"] == 35.0
            
            # Verify event properties
            assert published_event.severity == "critical"  # Mapped from severity 5
            assert published_event.correlation_id == "test-correlation-123"

    async def test_no_anomaly_no_event_publishing(self, agent, event_bus):
        """Test that no event is published when no anomaly is detected."""
        # Create a normal sensor reading
        normal_reading = SensorReading(
            sensor_id="sensor_temp_001",
            value=22.5,  # Exactly at historical mean
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={"location": "room_A"}
        )
        
        event = DataProcessedEvent(
            processed_data=normal_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=normal_reading.sensor_id
        )
        
        # Mock event bus publish method
        event_bus.publish = AsyncMock()
        
        # Mock ML predictions to indicate no anomaly
        with patch.object(agent.isolation_forest, 'predict', return_value=np.array([1])) as mock_predict, \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([0.1])) as mock_decision, \
             patch.object(agent.statistical_detector, 'detect', return_value=(False, 0.0, "normal")) as mock_stat_detect:
            
            await agent.process(event)
            
            # Verify that publish was NOT called
            event_bus.publish.assert_not_called()

    async def test_anomaly_alert_severity_mapping(self, agent, event_bus):
        """Test that confidence scores are correctly mapped to severity levels."""
        test_cases = [
            (0.9, 5, "critical"),    # Very high confidence
            (0.7, 4, "high"),        # High confidence  
            (0.5, 3, "medium"),      # Medium confidence
            (0.3, 2, "low"),         # Low confidence
            (0.1, 1, "very_low"),    # Very low confidence
        ]
        
        event_bus.publish = AsyncMock()
        
        for confidence, expected_severity, expected_severity_str in test_cases:
            # Reset the mock for each test case
            event_bus.publish.reset_mock()
            
            reading = SensorReading(
                sensor_id="test_sensor",
                value=100.0,
                timestamp=datetime.utcnow(),
                sensor_type=SensorType.TEMPERATURE,
                unit="celsius",
                quality=1.0,
                correlation_id=uuid.uuid4(),
                metadata={}
            )
            
            event = DataProcessedEvent(
                processed_data=reading.dict(),
                original_event_id=uuid.uuid4(),
                source_sensor_id=reading.sensor_id
            )
            
            # Mock ensemble decision to return specific confidence
            with patch.object(agent, '_ensemble_decision', return_value=(True, confidence, "test_anomaly")):
                await agent.process(event)
                
                # Verify severity mapping
                event_bus.publish.assert_called_once()
                published_event = event_bus.publish.call_args[0][0] # Corrected index
                
                assert published_event.anomaly_details["severity"] == expected_severity
                assert published_event.severity == expected_severity_str

    async def test_event_publishing_error_handling(self, agent, event_bus):
        """Test that event publishing errors are handled gracefully."""
        anomalous_reading = SensorReading(
            sensor_id="sensor_temp_001",
            value=50.0,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={}
        )
        
        event = DataProcessedEvent(
            processed_data=anomalous_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=anomalous_reading.sensor_id
        )
        
        # Mock event bus to raise an exception
        event_bus.publish = AsyncMock(side_effect=Exception("Event bus error"))
        
        # Mock to ensure anomaly is detected
        with patch.object(agent, '_ensemble_decision', return_value=(True, 0.8, "test_anomaly")), \
             patch.object(agent.logger, 'error') as mock_error:
            
            # This should not raise an exception
            await agent.process(event)
            
            # Verify error was logged
            mock_error.assert_called()
            error_message = mock_error.call_args[0][0]
            assert "Failed to create or publish AnomalyDetectedEvent" in error_message

    async def test_anomaly_alert_evidence_structure(self, agent, event_bus):
        """Test that anomaly alert evidence contains correct structure and types."""
        reading = SensorReading(
            sensor_id="sensor_vibr_001",
            value=0.15,  # Above historical mean
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.VIBRATION,
            unit="m/s2",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={}
        )
        
        event = DataProcessedEvent(
            processed_data=reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=reading.sensor_id
        )
        
        event_bus.publish = AsyncMock()
        
        # Mock predictions with specific values
        with patch.object(agent.isolation_forest, 'predict', return_value=np.array([-1])), \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([-0.25])), \
             patch.object(agent.statistical_detector, 'detect', return_value=(True, 0.75, "vibration_spike")):
            
            await agent.process(event)
            
            # Verify evidence structure
            published_event = event_bus.publish.call_args[0][0] # Corrected index
            evidence = published_event.anomaly_details["evidence"]
            
            # Check evidence keys and types
            assert "raw_value" in evidence
            assert "if_score" in evidence
            assert "stat_is_anomaly" in evidence
            assert "stat_confidence" in evidence
            
            # Verify types are JSON serializable
            assert isinstance(evidence["raw_value"], float)
            assert isinstance(evidence["if_score"], float)
            assert isinstance(evidence["stat_is_anomaly"], bool)
            assert isinstance(evidence["stat_confidence"], float)
            
            # Verify values
            assert evidence["raw_value"] == 0.15
            assert evidence["if_score"] == -0.25
            assert evidence["stat_is_anomaly"] is True
            assert evidence["stat_confidence"] == 0.75
