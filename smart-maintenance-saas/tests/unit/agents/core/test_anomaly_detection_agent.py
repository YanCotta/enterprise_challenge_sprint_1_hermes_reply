"""Unit tests for AnomalyDetectionAgent."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from core.events.event_bus import EventBus
from data.schemas import SensorReading, SensorType


class TestAnomalyDetectionAgent:
    """Unit tests for the AnomalyDetectionAgent."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock EventBus for testing."""
        return MagicMock(spec=EventBus)

    @pytest.fixture
    def agent(self, mock_event_bus):
        """Create an AnomalyDetectionAgent instance for testing."""
        return AnomalyDetectionAgent(
            agent_id="test_agent",
            event_bus=mock_event_bus
        )

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

    def test_extract_features_basic(self, agent, sample_sensor_reading):
        """Test that _extract_features returns proper format for basic sensor reading."""
        features = agent._extract_features(sample_sensor_reading)
        
        # Check return type and shape
        assert isinstance(features, np.ndarray)
        assert features.shape == (1, 1)  # 2D array with single feature
        assert features[0, 0] == sample_sensor_reading.value

    def test_extract_features_different_values(self, agent):
        """Test _extract_features with different sensor values."""
        test_values = [0.0, -10.5, 100.7, 999.99]
        
        for value in test_values:
            reading = SensorReading(
                sensor_id="test_sensor",
                value=value,
                timestamp=datetime.utcnow(),
                sensor_type=SensorType.TEMPERATURE,
                unit="celsius",
                quality=1.0,
                correlation_id=uuid.uuid4(),
                metadata={}
            )
            
            features = agent._extract_features(reading)
            
            assert isinstance(features, np.ndarray)
            assert features.shape == (1, 1)
            assert features[0, 0] == value

    def test_extract_features_logging(self, agent, sample_sensor_reading):
        """Test that _extract_features logs debug information."""
        with patch.object(agent.logger, 'debug') as mock_debug:
            features = agent._extract_features(sample_sensor_reading)
            
            # Verify debug logging was called
            mock_debug.assert_called_once()
            log_message = mock_debug.call_args[0][0]
            assert "Extracted features for sensor sensor_temp_001" in log_message
            assert str(sample_sensor_reading.value) in log_message

    def test_extract_features_with_extreme_values(self, agent):
        """Test _extract_features with extreme values."""
        extreme_values = [float('inf'), -float('inf'), 1e-10, 1e10]
        
        for value in extreme_values:
            if not np.isfinite(value):
                continue  # Skip infinite values for this test
                
            reading = SensorReading(
                sensor_id="extreme_sensor",
                value=value,
                timestamp=datetime.utcnow(),
                sensor_type=SensorType.PRESSURE,
                unit="pa",
                quality=1.0,
                correlation_id=uuid.uuid4(),
                metadata={}
            )
            
            features = agent._extract_features(reading)
            
            assert isinstance(features, np.ndarray)
            assert features.shape == (1, 1)
            assert features[0, 0] == value

    def test_extract_features_multiple_calls_consistency(self, agent, sample_sensor_reading):
        """Test that multiple calls to _extract_features return consistent results."""
        features1 = agent._extract_features(sample_sensor_reading)
        features2 = agent._extract_features(sample_sensor_reading)
        
        # Results should be identical
        np.testing.assert_array_equal(features1, features2)

    def test_extract_features_different_sensor_types(self, agent):
        """Test _extract_features with different sensor types."""
        sensor_configs = [
            {"type": SensorType.TEMPERATURE, "value": 22.5, "unit": "celsius"},
            {"type": SensorType.VIBRATION, "value": 0.05, "unit": "m/s2"},
            {"type": SensorType.PRESSURE, "value": 101.3, "unit": "kpa"},
        ]
        
        for config in sensor_configs:
            reading = SensorReading(
                sensor_id=f"sensor_{config['type']}_001",
                value=config["value"],
                timestamp=datetime.utcnow(),
                sensor_type=config["type"],
                unit=config["unit"],
                quality=1.0,
                correlation_id=uuid.uuid4(),
                metadata={}
            )
            
            features = agent._extract_features(reading)
            
            assert isinstance(features, np.ndarray)
            assert features.shape == (1, 1)
            assert features[0, 0] == config["value"]

    def test_extract_features_returns_sklearn_compatible_format(self, agent, sample_sensor_reading):
        """Test that _extract_features returns format compatible with sklearn."""
        features = agent._extract_features(sample_sensor_reading)
        
        # Should be 2D array (required by sklearn)
        assert len(features.shape) == 2
        assert features.shape[0] >= 1  # At least one sample
        assert features.shape[1] >= 1  # At least one feature
        
        # Should be numeric type compatible with sklearn
        assert np.issubdtype(features.dtype, np.number)
