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
from data.exceptions import DataValidationException


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
            # Process method should raise DataValidationException for invalid data
            with pytest.raises(DataValidationException) as exc_info:
                await agent.process(invalid_event)
            
            # Verify that errors were logged (both validation and application error)
            assert mock_error.call_count == 2
            error_calls = [call[0][0] for call in mock_error.call_args_list]
            assert any("Failed to parse sensor reading" in call for call in error_calls)
            assert any("Application error in AnomalyDetectionAgent.process" in call for call in error_calls)
            
            # Verify the exception details
            assert "Invalid sensor data payload" in str(exc_info.value)

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
            assert any("Isolation Forest for" in call for call in info_calls) # Corrected string
            assert any("Statistical for" in call for call in info_calls)

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
            
            # Verify info was logged for unknown sensor (changed from warning to info for first encounter)
            mock_info.assert_called()
            # Check that one of the info calls contains the expected message about first encounter
            info_calls = [str(call) for call in mock_info.call_args_list]
            assert any("First encounter for unknown_sensor_999" in call_str for call_str in info_calls)
            
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
            isolation_log = next((call for call in info_calls if "Isolation Forest for" in call), None) # Corrected string
            assert isolation_log is not None
            assert "pred=-1" in isolation_log
            assert "score=-0.1500" in isolation_log
            
            # Check that statistical results are logged
            statistical_log = next((call for call in info_calls if "Statistical for" in call), None)
            assert statistical_log is not None
            assert "anom=True" in statistical_log # Corrected key
            assert "conf=0.9000" in statistical_log
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
            assert anomaly_details["severity"] == 4  # Confidence 0.73 should map to severity 4
            assert math.isclose(anomaly_details["confidence"], 0.73, abs_tol=0.01) # Corrected based on current ensemble logic
            assert "Anomaly: sensor_temp_001" in anomaly_details["description"]
            
            # Verify triggering data
            triggering_data = published_event.triggering_data
            assert triggering_data["sensor_id"] == "sensor_temp_001"
            assert triggering_data["value"] == 35.0
            
            # Verify event properties
            assert published_event.severity == "high"  # Mapped from severity 4
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
            with patch.object(agent, '_ensemble_decision', return_value=(True, confidence, "other_type")):
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
        with patch.object(agent, '_ensemble_decision', return_value=(True, 0.8, "other_type")), \
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


    async def test_unknown_sensor_baseline_caching(self, agent):
        """Test that unknown sensor baselines are cached and reused."""
        unknown_sensor_id = "unknown_sensor_cache_test"
        
        # First reading for unknown sensor
        reading1 = SensorReading(
            sensor_id=unknown_sensor_id,
            value=42.0,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={}
        )
        
        event1 = DataProcessedEvent(
            processed_data=reading1.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=reading1.sensor_id
        )
        
        # Verify baseline cache is empty initially
        assert unknown_sensor_id not in agent.unknown_sensor_baselines
        
        with patch.object(agent.logger, 'info') as mock_info:
            await agent.process(event1)
            
            # Check that baseline was cached
            assert unknown_sensor_id in agent.unknown_sensor_baselines
            cached_baseline = agent.unknown_sensor_baselines[unknown_sensor_id]
            assert cached_baseline["mean"] == 42.0
            assert cached_baseline["std"] == 0.1  # Default std
            
            # Verify first encounter was logged
            info_calls = [str(call) for call in mock_info.call_args_list]
            assert any(f"First encounter for {unknown_sensor_id}" in call_str for call_str in info_calls)
        
        # Second reading for same unknown sensor
        reading2 = SensorReading(
            sensor_id=unknown_sensor_id,
            value=45.0,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={}
        )
        
        event2 = DataProcessedEvent(
            processed_data=reading2.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=reading2.sensor_id
        )
        
        with patch.object(agent.statistical_detector, 'detect') as mock_detect, \
             patch.object(agent.logger, 'info') as mock_info:
            
            await agent.process(event2)
            
            # Verify cached baseline was used
            mock_detect.assert_called_once()
            stat_call_args = mock_detect.call_args[0]
            assert stat_call_args[0] == 45.0  # reading value
            assert stat_call_args[1] == 42.0  # cached mean
            assert stat_call_args[2] == 0.1   # cached std
            
            # Verify no "first encounter" message this time
            info_calls = [str(call) for call in mock_info.call_args_list]
            assert not any(f"First encounter for unknown sensor {unknown_sensor_id}" in call_str for call_str in info_calls)


    async def test_agent_initialization_parameter_validation(self):
        """Test that agent initialization validates parameters correctly."""
        from core.events.event_bus import EventBus
        
        event_bus = EventBus()
        
        # Test with valid parameters
        agent = AnomalyDetectionAgent(
            agent_id="test_agent",
            event_bus=event_bus,
            specific_settings={
                "statistical_detector_config": {
                    "sigma_threshold": 2.5,
                    "min_confidence": 0.2,
                    "tolerance": 1e-8
                }
            }
        )
        
        # Verify parameters were passed to statistical detector
        assert agent.statistical_detector.sigma_threshold == 2.5
        assert agent.statistical_detector.min_confidence == 0.2
        assert agent.statistical_detector.tolerance == 1e-8
        
        # Test with invalid parameters should raise errors
        with pytest.raises(ValueError, match="sigma_threshold must be positive"):
            AnomalyDetectionAgent(
                agent_id="test_agent",
                event_bus=event_bus,
                specific_settings={
                    "statistical_detector_config": {
                        "sigma_threshold": 0.0
                    }
                }
            )
        
        with pytest.raises(ValueError, match="min_confidence must be between 0 and 1"):
            AnomalyDetectionAgent(
                agent_id="test_agent",
                event_bus=event_bus,
                specific_settings={
                    "statistical_detector_config": {
                        "min_confidence": 1.5
                    }
                }
            )
        
        # Test basic parameter validation
        with pytest.raises(ValueError, match="agent_id cannot be empty"):
            AnomalyDetectionAgent(
                agent_id="",
                event_bus=event_bus
            )
        
        with pytest.raises(ValueError, match="event_bus cannot be None"):
            AnomalyDetectionAgent(
                agent_id="test_agent",
                event_bus=None
            )


    async def test_retry_logic_with_event_publishing_failures(self, agent, event_bus):
        """Test retry logic when event publishing fails multiple times."""
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
        
        # Mock event bus to fail first 2 attempts, succeed on 3rd
        publish_call_count = 0
        def publish_side_effect(*args, **kwargs):
            nonlocal publish_call_count
            publish_call_count += 1
            if publish_call_count <= 2:
                raise Exception("Temporary failure")
            return None
        
        event_bus.publish = AsyncMock(side_effect=publish_side_effect)
        
        with patch.object(agent, '_ensemble_decision', return_value=(True, 0.8, "other_type")), \
             patch.object(agent.logger, 'warning') as mock_warning, \
             patch.object(agent.logger, 'info') as mock_info:
            
            await agent.process(event)
            
            # Verify retry attempts were made (should be called 3 times total)
            assert event_bus.publish.call_count == 3
        # Verify retry warnings were logged for first 2 failures
        warning_calls = [call[0][0] for call in mock_warning.call_args_list]
        retry_warnings = [call for call in warning_calls if "Publish attempt" in call and "failed" in call]
        assert len(retry_warnings) == 2
        
        # Verify info logs for publish attempts (should be 3 total)
        info_calls = [call[0][0] for call in mock_info.call_args_list]
        publish_attempt_logs = [call for call in info_calls if "Publishing AnomalyDetectedEvent (attempt" in call]
        assert len(publish_attempt_logs) == 3


    async def test_retry_logic_exhausted_retries(self, agent, event_bus):
        """Test behavior when all retry attempts are exhausted."""
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
        
        # Mock event bus to always fail
        event_bus.publish = AsyncMock(side_effect=Exception("Persistent failure"))
        
        with patch.object(agent, '_ensemble_decision', return_value=(True, 0.8, "other_type")), \
             patch.object(agent.logger, 'warning') as mock_warning, \
             patch.object(agent.logger, 'error') as mock_error:
            
            await agent.process(event)
            
            # Verify all retry attempts were made (3 attempts total)
            assert event_bus.publish.call_count == 3
                 # Verify retry warnings were logged
        warning_calls = [call[0][0] for call in mock_warning.call_args_list]
        retry_warnings = [call for call in warning_calls if "Publish attempt" in call and "failed" in call]
        assert len(retry_warnings) == 3  # All 3 attempts should log warnings
        
        # Verify final error was logged
        error_calls = [call[0][0] for call in mock_error.call_args_list]
        final_error = [call for call in error_calls if "Failed to publish AnomalyDetectedEvent after 3 attempts" in call]
        assert len(final_error) == 1


    async def test_graceful_degradation_with_isolation_forest_failure(self, agent):
        """Test graceful degradation when Isolation Forest fails."""
        reading = SensorReading(
            sensor_id="sensor_temp_001",
            value=25.0,
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
        
        # Mock Isolation Forest to raise exception
        with patch.object(agent.isolation_forest, 'predict', side_effect=Exception("IF failure")), \
             patch.object(agent.statistical_detector, 'detect', return_value=(True, 0.7, "statistical_anomaly")) as mock_stat, \
             patch.object(agent.logger, 'error') as mock_error, \
             patch.object(agent.logger, 'warning') as mock_warning:
            
            await agent.process(event)
            
            # Verify error was logged for IF failure
            error_calls = [call[0][0] for call in mock_error.call_args_list]
            if_errors = [call for call in error_calls if "Isolation Forest prediction failed" in call]
            assert len(if_errors) == 1
            
            # Verify statistical detector was still called
            mock_stat.assert_called_once()
            
            # Verify degradation warning was logged
            warning_calls = [call[0][0] for call in mock_warning.call_args_list]
            degradation_warnings = [call for call in warning_calls if "using statistical method only" in call]
            assert len(degradation_warnings) == 1


    async def test_graceful_degradation_with_statistical_detector_failure(self, agent):
        """Test graceful degradation when Statistical Detector fails."""
        reading = SensorReading(
            sensor_id="sensor_temp_001",
            value=25.0,
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
        
        # Mock Statistical Detector to raise exception
        with patch.object(agent.statistical_detector, 'detect', side_effect=Exception("Stat failure")), \
             patch.object(agent.isolation_forest, 'predict', return_value=np.array([-1])) as mock_if, \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([-0.2])), \
             patch.object(agent.logger, 'error') as mock_error, \
             patch.object(agent.logger, 'warning') as mock_warning:
            
            await agent.process(event)
            
            # Verify error was logged for statistical detector failure
            error_calls = [call[0][0] for call in mock_error.call_args_list]
            stat_errors = [call for call in error_calls if "Statistical detection failed" in call]
            assert len(stat_errors) == 1
            
            # Verify IF was still called
            mock_if.assert_called_once()
            
            # Verify degradation warning was logged
            warning_calls = [call[0][0] for call in mock_warning.call_args_list]
            degradation_warnings = [call for call in warning_calls if "using ML method only" in call]
            assert len(degradation_warnings) == 1


    async def test_correlation_id_passthrough(self, agent, event_bus):
        """Test that correlation_id is properly passed through to published events."""
        test_correlation_id = "test-correlation-12345"
        
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
            source_sensor_id=anomalous_reading.sensor_id,
            correlation_id=test_correlation_id
        )
        
        event_bus.publish = AsyncMock()
        
        with patch.object(agent, '_ensemble_decision', return_value=(True, 0.8, "other_type")):
            await agent.process(event)
            
            # Verify event was published with correct correlation_id
            event_bus.publish.assert_called_once()
            published_event = event_bus.publish.call_args[0][0]
            assert published_event.correlation_id == test_correlation_id


    async def test_isolation_forest_fitting_occurs_once_per_instance(self, agent):
        """Test that Isolation Forest fitting occurs only once per agent instance."""
        readings = []
        events = []
        
        # Create multiple sensor readings
        for i in range(5):
            reading = SensorReading(
                sensor_id="sensor_temp_001",
                value=20.0 + i,
                timestamp=datetime.utcnow(),
                sensor_type=SensorType.TEMPERATURE,
                unit="celsius",
                quality=1.0,
                correlation_id=uuid.uuid4(),
                metadata={}
            )
            readings.append(reading)
            events.append(DataProcessedEvent(
                processed_data=reading.dict(),
                original_event_id=uuid.uuid4(),
                source_sensor_id=reading.sensor_id
            ))
        
        # Ensure isolation forest is not fitted initially
        agent.isolation_forest_fitted = False
        
        with patch.object(agent.isolation_forest, 'fit') as mock_fit, \
             patch.object(agent.isolation_forest, 'predict', return_value=np.array([1])), \
             patch.object(agent.isolation_forest, 'decision_function', return_value=np.array([0.1])):
            
            # Process all events
            for event in events:
                await agent.process(event)
            
            # Verify fit was called only once
            assert mock_fit.call_count == 1
            assert agent.isolation_forest_fitted is True
