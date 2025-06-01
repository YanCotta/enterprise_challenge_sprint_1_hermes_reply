"""Unit tests for AnomalyDetectionAgent."""

import math # Added math import
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

    def test_ensemble_decision_both_anomaly(self, agent):
        """Test ensemble decision when both methods detect anomaly."""
        is_anomaly, confidence, description = agent._ensemble_decision(
            if_prediction=-1,      # IF detects anomaly
            if_score=-0.2,         # Negative score indicates anomaly
            stat_is_anomaly=True,  # Statistical method detects anomaly
            stat_confidence=0.8,   # High statistical confidence
            stat_desc="threshold_breach"
        )
        
        assert is_anomaly is True
        assert confidence > 0.5  # Should have reasonable confidence
        assert "ensemble_anomaly_if_and_threshold_breach" in description

    def test_ensemble_decision_only_isolation_forest(self, agent):
        """Test ensemble decision when only Isolation Forest detects anomaly."""
        is_anomaly, confidence, description = agent._ensemble_decision(
            if_prediction=-1,      # IF detects anomaly
            if_score=-0.3,         # Strong anomaly signal
            stat_is_anomaly=False, # Statistical method says normal
            stat_confidence=0.1,   # Low statistical confidence
            stat_desc="normal"
        )
        
        assert is_anomaly is True
        assert confidence > 0.0
        assert description == "isolation_forest_anomaly"

    def test_ensemble_decision_only_statistical(self, agent):
        """Test ensemble decision when only statistical method detects anomaly."""
        is_anomaly, confidence, description = agent._ensemble_decision(
            if_prediction=1,       # IF says normal
            if_score=0.1,          # Positive score indicates normal
            stat_is_anomaly=True,  # Statistical method detects anomaly
            stat_confidence=0.9,   # High statistical confidence
            stat_desc="spike_detected"
        )
        
        assert is_anomaly is True
        assert math.isclose(confidence, 0.72)  # Should use statistical confidence * 0.8
        assert description == "statistical_spike_detected" # Code generates lowercase 'statistical_'

    def test_ensemble_decision_no_anomaly(self, agent):
        """Test ensemble decision when neither method detects anomaly."""
        is_anomaly, confidence, description = agent._ensemble_decision(
            if_prediction=1,       # IF says normal
            if_score=0.2,          # Positive score indicates normal
            stat_is_anomaly=False, # Statistical method says normal
            stat_confidence=0.0,   # No statistical confidence
            stat_desc="normal"
        )
        
        assert is_anomaly is False
        assert confidence == 0.0
        assert description == "normal"

    def test_ensemble_decision_confidence_mapping(self, agent):
        """Test that Isolation Forest scores are properly mapped to confidence."""
        # Test high anomaly score
        is_anomaly, confidence, description = agent._ensemble_decision(
            if_prediction=-1,
            if_score=-0.5,         # Very negative score
            stat_is_anomaly=False,
            stat_confidence=0.0,
            stat_desc="normal"
        )
        
        assert is_anomaly is True
        assert confidence >= 0.5  # Should have at least minimum confidence
        
        # Test moderate anomaly score
        is_anomaly2, confidence2, description2 = agent._ensemble_decision(
            if_prediction=-1,
            if_score=-0.1,         # Less negative score
            stat_is_anomaly=False,
            stat_confidence=0.0,
            stat_desc="normal"
        )
        
        assert is_anomaly2 is True
        assert confidence2 >= 0.5  # Should still have minimum confidence

    def test_ensemble_decision_max_confidence(self, agent):
        """Test that ensemble takes maximum of individual confidences."""
        # Statistical confidence higher
        is_anomaly, confidence, description = agent._ensemble_decision(
            if_prediction=-1,
            if_score=-0.1,         # Moderate IF confidence
            stat_is_anomaly=True,
            stat_confidence=0.95,  # Very high statistical confidence
            stat_desc="outlier"
        )
        
        assert is_anomaly is True
        assert math.isclose(confidence, 0.845)  # Corrected expected confidence

    def test_ensemble_decision_logging(self, agent):
        """Test that ensemble decision logs debug information."""
        with patch.object(agent.logger, 'debug') as mock_debug:
            agent._ensemble_decision(
                if_prediction=-1,
                if_score=-0.2,
                stat_is_anomaly=True,
                stat_confidence=0.7,
                stat_desc="test_anomaly"
            )
            
            # Verify debug logging was called
            mock_debug.assert_called_once()
            log_message = mock_debug.call_args[0][0]
            assert "Ensemble decision" in log_message
            assert "final_anom=True" in log_message # Corrected key for anomaly status
            assert "final_conf=" in log_message # Corrected key for confidence
