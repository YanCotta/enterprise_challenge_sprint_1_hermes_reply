"""Integration tests for AnomalyDetectionAgent."""

import asyncio
import logging
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from core.events.event_bus import EventBus
from core.events.event_models import DataProcessedEvent
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
            assert any("Processing sensor reading for sensor_temp_001" in call for call in info_calls)

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
            assert "Error processing DataProcessedEvent" in error_call

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
            assert any("Isolation Forest prediction" in call for call in info_calls)
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
            assert "No historical data found for sensor unknown_sensor_999" in warning_message
            
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
            assert "No features extracted" in warning_message
            assert "skipping processing" in warning_message

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
            isolation_log = next((call for call in info_calls if "Isolation Forest prediction" in call), None)
            assert isolation_log is not None
            assert "prediction=-1" in isolation_log
            assert "anomaly" in isolation_log
            assert "score=-0.1500" in isolation_log
            
            # Check that statistical results are logged
            statistical_log = next((call for call in info_calls if "Statistical detection" in call), None)
            assert statistical_log is not None
            assert "is_anomaly=True" in statistical_log
            assert "confidence=0.9000" in statistical_log
            assert "statistical_threshold_breach" in statistical_log
