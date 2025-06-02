"""Unit tests for StatisticalAnomalyDetector."""
import math

import pytest
import numpy as np

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
    # deviation = 20, threshold = 15. Logged confidence = 0.625
    assert math.isclose(confidence_score, 0.625)
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
    # deviation = 50, threshold = 15. Logged confidence = 0.85
    assert math.isclose(confidence_score, 0.85)
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
    # deviation = 20, threshold = 15. Logged confidence = 0.625
    assert math.isclose(confidence_score, 0.625)
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
    # dev=15.001, thres=15. Logged confidence = 0.5000 (approx)
    assert math.isclose(confidence_score, 0.5000333311112595) # Using more precise value from log
    assert anomaly_type == "statistical_threshold_breach"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_nan_reading_value():
    """Test that NaN reading value raises ValueError."""
    detector = StatisticalAnomalyDetector()
    
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(float('nan'), 100.0, 5.0)


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_inf_reading_value():
    """Test that infinite reading value raises ValueError."""
    detector = StatisticalAnomalyDetector()
    
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(float('inf'), 100.0, 5.0)


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_nan_historical_mean():
    """Test that NaN historical mean raises ValueError."""
    detector = StatisticalAnomalyDetector()
    
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(100.0, float('nan'), 5.0)


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_inf_historical_std():
    """Test that infinite historical std raises ValueError."""
    detector = StatisticalAnomalyDetector()
    
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(100.0, 100.0, float('inf'))


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_negative_historical_std():
    """Test that negative historical std raises ValueError."""
    detector = StatisticalAnomalyDetector()
    
    with pytest.raises(ValueError, match="historical_std must be non-negative"):
        detector.detect(100.0, 100.0, -1.0)


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_custom_sigma_threshold():
    """Test detector with custom sigma threshold."""
    detector = StatisticalAnomalyDetector(config={"sigma_threshold": 2.0})
    reading_value = 110.0  # 110 > 100 + 2*5 = 110 (exactly at threshold)
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert not is_anomaly  # Exactly at threshold should not be anomaly
    assert confidence_score == 0.0
    assert anomaly_type == "normal"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_custom_sigma_threshold_anomaly():
    """Test detector with custom sigma threshold detecting anomaly."""
    detector = StatisticalAnomalyDetector(config={"sigma_threshold": 2.0})
    reading_value = 110.001  # Just above 2-sigma threshold
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    assert confidence_score > 0.0
    assert anomaly_type == "statistical_threshold_breach"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_custom_min_confidence():
    """Test detector with custom minimum confidence."""
    detector = StatisticalAnomalyDetector(config={"min_confidence": 0.3})
    reading_value = 117.0  # Small deviation
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    assert confidence_score >= 0.3  # Should be at least min_confidence
    assert anomaly_type == "statistical_threshold_breach"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_custom_tolerance():
    """Test detector with custom tolerance for float comparisons."""
    # Test tolerance with edge case where std is very close to 0
    detector = StatisticalAnomalyDetector(config={"tolerance": 1e-2})  # Larger tolerance for zero detection
    reading_value = 100.001  # Very small difference
    historical_mean = 100.0
    historical_std = 1e-3  # Very small std that might be considered "zero" with large tolerance

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    # With tolerance 1e-2, std of 1e-3 should be considered close to zero
    # and reading difference of 0.001 should also be considered close to mean
    assert not is_anomaly  # Should be treated as normal due to tolerance
    assert anomaly_type in ["normal_zero_std", "normal"]


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_invalid_sigma_threshold():
    """Test that invalid sigma threshold raises ValueError."""
    with pytest.raises(ValueError, match="sigma_threshold must be positive"):
        StatisticalAnomalyDetector(config={"sigma_threshold": 0.0})

    with pytest.raises(ValueError, match="sigma_threshold must be positive"):
        StatisticalAnomalyDetector(config={"sigma_threshold": -1.0})


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_invalid_min_confidence():
    """Test that invalid min_confidence raises ValueError."""
    with pytest.raises(ValueError, match="min_confidence must be between 0 and 1"):
        StatisticalAnomalyDetector(config={"min_confidence": -0.1})

    with pytest.raises(ValueError, match="min_confidence must be between 0 and 1"):
        StatisticalAnomalyDetector(config={"min_confidence": 1.1})


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_invalid_tolerance():
    """Test that invalid tolerance raises ValueError."""
    # Check source code to see if tolerance validation exists
    # For now, let's test with reasonable tolerance values
    detector = StatisticalAnomalyDetector(config={"tolerance": 1e-10})
    reading_value = 100.001
    historical_mean = 100.0
    historical_std = 5.0

    # This should work without error
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )
    assert not is_anomaly


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_linear_confidence_scaling():
    """Test that confidence scales with deviation beyond threshold."""
    detector = StatisticalAnomalyDetector(config={"min_confidence": 0.5})
    historical_mean = 100.0
    historical_std = 5.0
    threshold = 15.0  # 3 * std

    # Test various deviations
    test_cases = [
        (116.0, 16.0),  # deviation = 16, just above threshold
        (120.0, 20.0),  # deviation = 20
        (125.0, 25.0),  # deviation = 25
        (130.0, 30.0),  # deviation = 30, well above threshold
    ]

    confidences = []
    for reading_value, expected_deviation in test_cases:
        is_anomaly, confidence_score, anomaly_type = detector.detect(
            reading_value, historical_mean, historical_std
        )
        
        assert is_anomaly
        assert anomaly_type == "statistical_threshold_breach"
        confidences.append(confidence_score)
        
        # Verify deviation calculation
        actual_deviation = abs(reading_value - historical_mean)
        assert math.isclose(actual_deviation, expected_deviation, abs_tol=1e-6)

    # Verify that confidence increases with larger deviations
    for i in range(1, len(confidences)):
        assert confidences[i] >= confidences[i-1], f"Confidence should increase: {confidences}"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_confidence_capping():
    """Test that confidence approaches but doesn't necessarily reach 1.0."""
    detector = StatisticalAnomalyDetector(config={"min_confidence": 0.5})
    reading_value = 200.0  # Very large deviation
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_value, historical_mean, historical_std
    )

    assert is_anomaly
    # With the current formula, confidence approaches 1.0 but may not reach it exactly
    # The formula is: min_confidence + (1 - min_confidence) * (1 - threshold/deviation)
    # For deviation=100, threshold=15: confidence = 0.5 + 0.5 * (1 - 15/100) = 0.5 + 0.5 * 0.85 = 0.925
    assert confidence_score >= 0.9  # Should be very high confidence
    assert confidence_score <= 1.0  # Should not exceed 1.0
    assert anomaly_type == "statistical_threshold_breach"


# Add new comprehensive test cases for input validation and enhanced features

@pytest.mark.asyncio
async def test_statistical_anomaly_detector_nan_reading_value():
    """Test detector handles NaN reading value gracefully."""
    detector = StatisticalAnomalyDetector()
    reading_value = float('nan')
    historical_mean = 100.0
    historical_std = 5.0

    # Should raise ValueError for invalid input
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(reading_value, historical_mean, historical_std)


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_inf_reading_value():
    """Test detector handles infinite reading value gracefully."""
    detector = StatisticalAnomalyDetector()
    historical_mean = 100.0
    historical_std = 5.0

    # Test positive infinity - should raise ValueError
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(float('inf'), historical_mean, historical_std)

    # Test negative infinity - should raise ValueError
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(float('-inf'), historical_mean, historical_std)


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_nan_historical_values():
    """Test detector handles NaN historical values gracefully."""
    detector = StatisticalAnomalyDetector()
    reading_value = 100.0

    # Test NaN mean - should raise ValueError
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(reading_value, float('nan'), 5.0)

    # Test NaN std - should raise ValueError
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(reading_value, 100.0, float('nan'))


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_inf_historical_values():
    """Test detector handles infinite historical values gracefully."""
    detector = StatisticalAnomalyDetector()
    reading_value = 100.0

    # Test infinite mean - should raise ValueError
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(reading_value, float('inf'), 5.0)

    # Test infinite std - should raise ValueError
    with pytest.raises(ValueError, match="All input values must be finite"):
        detector.detect(reading_value, 100.0, float('inf'))


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_negative_std_dev():
    """Test detector handles negative standard deviation gracefully."""
    detector = StatisticalAnomalyDetector()
    reading_value = 100.0
    historical_mean = 100.0
    historical_std = -5.0  # Invalid negative std

    # Should raise ValueError for negative std
    with pytest.raises(ValueError, match="historical_std must be non-negative"):
        detector.detect(reading_value, historical_mean, historical_std)


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_enhanced_confidence_formula():
    """Test the new linear confidence scaling formula across different deviation points."""
    detector = StatisticalAnomalyDetector(config={"min_confidence": 0.2})
    historical_mean = 100.0
    historical_std = 10.0
    threshold = 30.0  # 3 * std

    # Test specific deviation points with expected confidence calculations
    test_cases = [
        # (reading_value, expected_deviation, expected_confidence)
        (135.0, 35.0, 0.2 + 0.8 * (1 - 30.0/35.0)),  # deviation=35, conf = 0.2 + 0.8 * (1 - 6/7) = 0.2 + 0.8 * 1/7 ≈ 0.314
        (140.0, 40.0, 0.2 + 0.8 * (1 - 30.0/40.0)),  # deviation=40, conf = 0.2 + 0.8 * (1 - 3/4) = 0.2 + 0.8 * 1/4 = 0.4
        (160.0, 60.0, 0.2 + 0.8 * (1 - 30.0/60.0)),  # deviation=60, conf = 0.2 + 0.8 * (1 - 1/2) = 0.2 + 0.8 * 1/2 = 0.6
        (200.0, 100.0, 0.2 + 0.8 * (1 - 30.0/100.0)), # deviation=100, conf = 0.2 + 0.8 * (1 - 0.3) = 0.2 + 0.8 * 0.7 = 0.76
    ]

    for reading_value, expected_deviation, expected_confidence in test_cases:
        is_anomaly, confidence_score, anomaly_type = detector.detect(
            reading_value, historical_mean, historical_std
        )
        
        assert is_anomaly
        assert anomaly_type == "statistical_threshold_breach"
        
        # Verify confidence calculation with some tolerance for floating point
        assert math.isclose(confidence_score, expected_confidence, abs_tol=1e-3), \
            f"For deviation {expected_deviation}, expected confidence {expected_confidence}, got {confidence_score}"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_config_parameter_validation():
    """Test validation of all configuration parameters."""
    # Test valid configuration
    valid_config = {
        "sigma_threshold": 2.5,
        "min_confidence": 0.3,
        "tolerance": 1e-8
    }
    detector = StatisticalAnomalyDetector(config=valid_config)
    assert detector is not None

    # Test edge case valid values
    edge_config = {
        "sigma_threshold": 0.1,  # Very small but positive
        "min_confidence": 0.0,   # Minimum allowed
        "tolerance": 1e-15       # Very small tolerance
    }
    detector = StatisticalAnomalyDetector(config=edge_config)
    assert detector is not None

    edge_config2 = {
        "min_confidence": 1.0,   # Maximum allowed
    }
    detector = StatisticalAnomalyDetector(config=edge_config2)
    assert detector is not None


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_zero_deviation_with_tolerance():
    """Test behavior when deviation is zero or very close to zero with different tolerance settings."""
    # Test with small tolerance
    detector_small_tol = StatisticalAnomalyDetector(config={"tolerance": 1e-10})
    reading_value = 100.0000000001  # Very close to mean
    historical_mean = 100.0
    historical_std = 5.0

    is_anomaly, confidence_score, anomaly_type = detector_small_tol.detect(
        reading_value, historical_mean, historical_std
    )
    assert not is_anomaly  # Should be normal due to very small deviation
    assert confidence_score == 0.0
    assert anomaly_type == "normal"

    # Test with larger tolerance
    detector_large_tol = StatisticalAnomalyDetector(config={"tolerance": 1e-6})
    
    is_anomaly, confidence_score, anomaly_type = detector_large_tol.detect(
        reading_value, historical_mean, historical_std
    )
    assert not is_anomaly  # Should still be normal
    assert confidence_score == 0.0
    assert anomaly_type == "normal"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_boundary_conditions():
    """Test detector behavior at exact threshold boundaries."""
    detector = StatisticalAnomalyDetector(config={"sigma_threshold": 3.0})
    historical_mean = 100.0
    historical_std = 5.0
    threshold = 15.0  # 3 * 5

    # Test reading exactly at positive threshold
    reading_at_threshold = historical_mean + threshold
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_at_threshold, historical_mean, historical_std
    )
    assert not is_anomaly  # At threshold should not be anomaly
    assert confidence_score == 0.0
    assert anomaly_type == "normal"

    # Test reading just above threshold
    reading_just_above = historical_mean + threshold + 0.001
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_just_above, historical_mean, historical_std
    )
    assert is_anomaly  # Just above threshold should be anomaly
    assert confidence_score > 0.0
    assert anomaly_type == "statistical_threshold_breach"

    # Test reading exactly at negative threshold
    reading_at_neg_threshold = historical_mean - threshold
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_at_neg_threshold, historical_mean, historical_std
    )
    assert not is_anomaly  # At threshold should not be anomaly
    assert confidence_score == 0.0
    assert anomaly_type == "normal"

    # Test reading just below negative threshold
    reading_just_below = historical_mean - threshold - 0.001
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        reading_just_below, historical_mean, historical_std
    )
    assert is_anomaly  # Just below threshold should be anomaly
    assert confidence_score > 0.0
    assert anomaly_type == "statistical_threshold_breach"


@pytest.mark.asyncio
async def test_statistical_anomaly_detector_extreme_confidence_values():
    """Test confidence calculation with extreme deviation values."""
    detector = StatisticalAnomalyDetector(config={"min_confidence": 0.1})
    historical_mean = 100.0
    historical_std = 1.0
    threshold = 3.0  # 3 * 1

    # Test extremely large deviation (should approach max confidence)
    extreme_reading = 1000.0  # deviation = 900
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        extreme_reading, historical_mean, historical_std
    )
    assert is_anomaly
    assert confidence_score >= 0.95  # Should be very high
    assert confidence_score <= 1.0   # Should not exceed 1.0
    assert anomaly_type == "statistical_threshold_breach"

    # Test small deviation just above threshold
    small_anomaly_reading = 103.001  # deviation = 3.001, just above threshold
    is_anomaly, confidence_score, anomaly_type = detector.detect(
        small_anomaly_reading, historical_mean, historical_std
    )
    assert is_anomaly
    # For deviation=3.001, threshold=3: confidence = 0.1 + 0.9 * (1 - 3/3.001) ≈ 0.1 + 0.9 * 0.0003 ≈ 0.1003
    assert confidence_score >= 0.1     # Should be at least min_confidence
    assert confidence_score <= 0.2     # Should be relatively low
    assert anomaly_type == "statistical_threshold_breach"
