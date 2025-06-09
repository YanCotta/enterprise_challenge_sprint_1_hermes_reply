import pytest
from unittest.mock import Mock, patch
import uuid # For correlation_id testing

from smart_maintenance_saas.apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from smart_maintenance_saas.data.schemas import AnomalyType, SensorReading
from smart_maintenance_saas.core.events.event_models import DataProcessedEvent


# Mock EventBus for agent initialization
@pytest.fixture
def mock_event_bus():
    return Mock()

@pytest.fixture
def anomaly_detection_agent(mock_event_bus):
    # Provide minimal specific_settings if necessary for initialization
    # For _calculate_ensemble_metrics, specific_settings might not be directly needed
    # but the agent constructor requires it.
    agent = AnomalyDetectionAgent(agent_id="test_anomaly_agent", event_bus=mock_event_bus, specific_settings={
        'statistical_detector_config': {}, # Default empty config
        'default_historical_std': 0.1
    })
    return agent

class TestAnomalyDetectionAgentCalculateEnsembleMetrics:

    def test_both_anomaly_z_score(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=-1, if_score=-0.2,  # Anomaly from IF
            stat_is_anomaly=True, stat_confidence=0.8, stat_desc="z_score_violation"
        )
        assert is_anomaly is True
        assert 0.5 < confidence <= 1.0 # Combined confidence
        # Expected: (0.6 * (0.5 + abs(-0.2)*0.5) + 0.4 * 0.8) = (0.6 * 0.6 + 0.32) = 0.36 + 0.32 = 0.68
        assert abs(confidence - 0.68) < 0.001
        assert desc == AnomalyType.ENSEMBLE_IF_STATISTICAL

    def test_both_anomaly_threshold(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=-1, if_score=-0.1,
            stat_is_anomaly=True, stat_confidence=0.7, stat_desc="threshold_violation"
        )
        assert is_anomaly is True
        # Expected: (0.6 * (0.5 + abs(-0.1)*0.5) + 0.4 * 0.7) = (0.6 * 0.55 + 0.28) = 0.33 + 0.28 = 0.61
        assert abs(confidence - 0.61) < 0.001
        assert desc == AnomalyType.ENSEMBLE_IF_STATISTICAL

    def test_both_anomaly_other_stat(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=-1, if_score=-0.1,
            stat_is_anomaly=True, stat_confidence=0.7, stat_desc="other_violation"
        )
        assert is_anomaly is True
        assert abs(confidence - 0.61) < 0.001 # Same confidence as above
        assert desc == AnomalyType.ENSEMBLE_IF_STATISTICAL # Falls back to general ensemble

    def test_if_only_anomaly(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=-1, if_score=-0.3,
            stat_is_anomaly=False, stat_confidence=0.2, stat_desc="normal"
        )
        assert is_anomaly is True
        # Expected: (0.5 + abs(-0.3)*0.5) * 0.8 = (0.5 + 0.15) * 0.8 = 0.65 * 0.8 = 0.52
        assert abs(confidence - 0.52) < 0.001
        assert desc == AnomalyType.ISOLATION_FOREST

    def test_stat_only_anomaly_z_score(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=1, if_score=0.1, # Normal from IF
            stat_is_anomaly=True, stat_confidence=0.9, stat_desc="z_score_violation"
        )
        assert is_anomaly is True
        # Expected: 0.9 * 0.8 = 0.72
        assert abs(confidence - 0.72) < 0.001
        assert desc == AnomalyType.STATISTICAL_Z_SCORE

    def test_stat_only_anomaly_threshold(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=1, if_score=0.2,
            stat_is_anomaly=True, stat_confidence=0.75, stat_desc="threshold_violation"
        )
        assert is_anomaly is True
        # Expected: 0.75 * 0.8 = 0.6
        assert abs(confidence - 0.6) < 0.001
        assert desc == AnomalyType.STATISTICAL_THRESHOLD

    def test_stat_only_anomaly_unknown_desc(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=1, if_score=0.2,
            stat_is_anomaly=True, stat_confidence=0.75, stat_desc="some_other_stat_finding"
        )
        assert is_anomaly is True
        assert abs(confidence - 0.6) < 0.001
        assert desc == AnomalyType.UNKNOWN # As per current logic

    def test_no_anomaly(self, anomaly_detection_agent):
        is_anomaly, confidence, desc = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=1, if_score=0.5, # Normal from IF
            stat_is_anomaly=False, stat_confidence=0.1, stat_desc="normal"
        )
        assert is_anomaly is False
        assert confidence == 0.0 # Based on current logic where final_confidence_score is initialized to 0.0
        assert desc == "normal"

    def test_if_score_normalization_edge_cases(self, anomaly_detection_agent):
        # if_score at max anomaly (-1.0 for normalization cap)
        _, confidence_max_neg_if, _ = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=-1, if_score=-1.0, stat_is_anomaly=False, stat_confidence=0.1, stat_desc="normal"
        )
        # Expected if_confidence: (0.5 + abs(-1.0)*0.5) = 1.0. Then 1.0 * 0.8 = 0.8
        assert abs(confidence_max_neg_if - 0.8) < 0.001

        # if_score close to 0 but still anomaly
        _, confidence_min_neg_if, _ = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=-1, if_score=-0.01, stat_is_anomaly=False, stat_confidence=0.1, stat_desc="normal"
        )
        # Expected if_confidence: (0.5 + abs(-0.01)*0.5) = 0.505. Then 0.505 * 0.8 = 0.404
        assert abs(confidence_min_neg_if - 0.404) < 0.001

        # if_score at 0 (should be treated as anomaly by prediction, but score shows no confidence)
        _, confidence_zero_if, _ = anomaly_detection_agent._calculate_ensemble_metrics(
            if_prediction=-1, if_score=0.0, stat_is_anomaly=False, stat_confidence=0.1, stat_desc="normal"
        )
        # Expected if_confidence: (0.5 + abs(0.0)*0.5) = 0.5. Then 0.5 * 0.8 = 0.4
        assert abs(confidence_zero_if - 0.4) < 0.001

# More tests will be added for logging correlation_id
# and potentially for the process method if needed.
# For now, focusing on the refactored method.

# Test for correlation_id in logging
@patch.object(AnomalyDetectionAgent, '_process_ml_models', return_value=(1, 0.1)) # Mock to prevent actual ML processing
@patch.object(AnomalyDetectionAgent, '_process_statistical_method', return_value=(False, 0.1, "normal"))
@patch.object(AnomalyDetectionAgent, '_handle_anomaly_detected') # We are not testing this part here
@patch('smart_maintenance_saas.apps.agents.core.anomaly_detection_agent.logging') # Path to logging used in anomaly_detection_agent
async def test_process_logging_with_correlation_id(
    mock_logging,
    mock_handle_anomaly,
    mock_process_stat,
    mock_process_ml,
    anomaly_detection_agent # use the fixture
):
    mock_logger = Mock()
    mock_logging.getLogger.return_value = mock_logger

    # Re-initialize agent with the mocked logger if it's set up in __init__
    # For this test, we assume the logger is obtained fresh or can be influenced by the patch
    # Or, more simply, ensure the agent instance uses the logger patched at the module level.
    # The fixture `anomaly_detection_agent` will use the patched logging if patch is active before its creation.
    # However, since the agent is created by a fixture *before* this test function's patches might apply
    # to its specific instance logger, we might need to re-assign or re-initialize.
    # A simpler way: the class `AnomalyDetectionAgent` is patched, so any instance will use the mocked getLogger.

    agent_instance = anomaly_detection_agent # Get the instance from the fixture

    # If agent's self.logger is set at init, re-patching getLogger won't change agent_instance.logger
    # So, we can directly mock agent_instance.logger if it was set.
    # For this structure, where getLogger is called at the module level of the agent file,
    # the patch on 'smart_maintenance_saas.apps.agents.core.anomaly_detection_agent.logging' is correct.
    # The agent's self.logger will be the one from mock_logging.getLogger.

    correlation_id = str(uuid.uuid4())
    event_data = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2023-10-26T10:00:00Z",
        "correlation_id": correlation_id,
        "processed_data": {
            "sensor_id": "sensor123",
            "value": 100.0,
            "timestamp": "2023-10-26T10:00:00Z", # SensorReading needs this
            "sensor_type": "temperature", # SensorReading needs this
            "unit": "C" # SensorReading needs this
        }
    }
    event = DataProcessedEvent(**event_data)

    # Setup scaler and isolation_forest_fitted attributes that are accessed in process
    agent_instance.scaler = Mock()
    agent_instance.scaler.fit_transform = Mock(return_value=([[100.0]]))
    agent_instance.isolation_forest_fitted = True # Assume fitted for this test path


    await agent_instance.process(event)

    # Check if logger.debug (first log call in process) was called with correlation_id
    # This depends on the exact logging calls in `process`
    # Example: Check the first call to logger.debug
    found_log_with_correlation_id = False
    for call_args in mock_logger.debug.call_args_list:
        if call_args[1].get('extra') == {"correlation_id": correlation_id}:
            found_log_with_correlation_id = True
            break
    assert found_log_with_correlation_id, "logger.debug was not called with correct correlation_id in extra"

    # Also check logger.info for the "Final decision" log
    found_final_decision_log = False
    for call_args in mock_logger.info.call_args_list:
         if "Final decision for sensor123" in call_args[0][0] and \
            call_args[1].get('extra') == {"correlation_id": correlation_id}:
            found_final_decision_log = True
            break
    assert found_final_decision_log, "Final decision log was not called with correct correlation_id"

    # If an anomaly was detected and _handle_anomaly_detected was called,
    # we'd also check logs from there if they are direct calls from AnomalyDetectionAgent.
    # In this case, mock_handle_anomaly is used, so we don't check its internal logs here.

    # The process method also logs errors. A separate test could be made for error paths.
    # For now, this covers a non-error path.
pytest
