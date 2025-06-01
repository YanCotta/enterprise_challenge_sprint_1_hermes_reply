"""Unit tests for StatisticalAnomalyDetector."""
import math

import pytest

from apps.ml.statistical_models import StatisticalAnomalyDetector


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_normal_reading():
    """Test normal reading within 3-sigma."""
    detector = StatisticalAnomalyDetector()
    reading_value = 105.0
    historical_mean = 100.0
    historical_std = 5.0  # 3-sigma threshold is 15 (100 +/- 15)

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert not is_anomaly
    assert confidence_score == 0.0
    assert anomaly_type == "normal"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_anomalous_reading_above():
    """Test anomalous reading above 3-sigma threshold."""
    detector = StatisticalAnomalyDetector()
    reading_value = 120.0  # 120 is > 100 + 3*5 = 115
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    # deviation = 20, threshold = 15. confidence = 1 - (15/20) = 0.25. Capped to 0.5
    assert math.isclose(confidence_score, 0.5)
    assert anomaly_type == "statistical_threshold_breach"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_anomalous_reading_far_above():
    """Test anomalous reading significantly above 3-sigma threshold."""
    detector = StatisticalAnomalyDetector()
    reading_value = 150.0  # 150 is > 100 + 3*5 = 115
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    # deviation = 50, threshold = 15. confidence = 1 - (15/50) = 0.7
    assert math.isclose(confidence_score, 0.7)
    assert anomaly_type == "statistical_threshold_breach"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_anomalous_reading_below():
    """Test anomalous reading below 3-sigma threshold."""
    detector = StatisticalAnomalyDetector()
    reading_value = 80.0  # 80 is < 100 - 3*5 = 85
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    # deviation = 20, threshold = 15. confidence = 1 - (15/20) = 0.25. Capped to 0.5
    assert math.isclose(confidence_score, 0.5)
    assert anomaly_type == "statistical_threshold_breach"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_edge_case_std_zero_normal():
    """Test normal reading when historical_std is zero."""
    detector = StatisticalAnomalyDetector()
    reading_value = 100.0
    historical_mean = 100.0
    historical_std = 0.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert not is_anomaly
    assert confidence_score == 0.0
    assert anomaly_type == "normal_zero_std"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_edge_case_std_zero_anomaly():
    """Test anomalous reading when historical_std is zero."""
    detector = StatisticalAnomalyDetector()
    reading_value = 101.0
    historical_mean = 100.0
    historical_std = 0.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    assert confidence_score == 1.0
    assert anomaly_type == "statistical_threshold_breach_zero_std"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_reading_at_threshold():
    """Test reading exactly at the 3-sigma threshold (should be normal)."""
    detector = StatisticalAnomalyDetector()
    historical_mean = 100.0
    historical_std = 5.0
    reading_value = 115.0  # Exactly at 3*std threshold (100 + 3*5 = 115)

    # Value at threshold is not considered an anomaly (deviation > threshold)
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert not is_anomaly
    assert confidence_score == 0.0
    assert anomaly_type == "normal"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_reading_just_above_threshold():
    """Test reading just slightly above 3-sigma threshold."""
    detector = StatisticalAnomalyDetector()
    historical_mean = 100.0
    historical_std = 5.0
    reading_value = 115.001

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    # dev=15.001, thres=15. conf=1-(15/15.001) ~0.00006. Capped to 0.5
    assert math.isclose(confidence_score, 0.5)
    assert anomaly_type == "statistical_threshold_breach"
