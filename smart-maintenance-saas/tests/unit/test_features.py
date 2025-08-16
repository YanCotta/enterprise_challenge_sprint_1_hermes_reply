"""
Unit tests for the feature engineering module.
"""

import pandas as pd
import pytest
import sys
import os

# Add the apps directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from apps.ml.features import SensorFeatureTransformer


def test_sensor_feature_transformer():
    """Test the refined SensorFeatureTransformer basic functionality."""
    # Create test data with required columns
    df = pd.DataFrame({
        'sensor_id': ['sensor-001'] * 10 + ['sensor-002'] * 10,
        'timestamp': pd.date_range('2025-01-01', periods=10, freq='T').tolist() +
                     pd.date_range('2025-01-01', periods=10, freq='T').tolist(),
        'value': list(range(10)) + list(range(5, 15)),
        'quality': [0.9 + (i * 0.001) for i in range(20)]
    })

    transformer = SensorFeatureTransformer(n_lags=3, scale_columns=['value', 'quality'])
    transformer.fit(df)
    transformed = transformer.transform(df)

    # Scaled columns created & originals removed
    assert 'value_scaled' in transformed.columns
    assert 'quality_scaled' in transformed.columns
    assert 'value' not in transformed.columns
    assert 'quality' not in transformed.columns

    # Lag features present
    for i in range(1, 4):
        assert f'value_lag_{i}' in transformed.columns

    # Scaled values between 0 and 1
    assert transformed['value_scaled'].between(0, 1).all()
    assert transformed['quality_scaled'].between(0, 1).all()

    # Feature names accessible
    names = transformer.get_feature_names_out()
    assert isinstance(names, list)
    assert 'value_scaled' in names


def test_sensor_feature_transformer_fit_transform():
    """Test fit_transform pipeline and scaling correctness."""
    df = pd.DataFrame({
        'sensor_id': ['sensor-001'] * 5,
        'timestamp': pd.date_range('2025-02-01', periods=5, freq='H'),
        'value': [10, 20, 30, 40, 50],
        'quality': [0.5, 0.6, 0.7, 0.8, 0.9]
    })

    transformer = SensorFeatureTransformer(n_lags=2, scale_columns=['value'])
    transformed = transformer.fit_transform(df)

    assert 'value_scaled' in transformed.columns
    assert 'value_lag_1' in transformed.columns
    assert 'value_lag_2' in transformed.columns

    # value_scaled should linearly map 10..50 to 0..1
    expected_scaled = [0.0, 0.25, 0.5, 0.75, 1.0]
    assert transformed['value_scaled'].tolist() == expected_scaled


def test_sensor_feature_transformer_invalid_input():
    """Ensure meaningful error when required columns are missing."""
    df_invalid = pd.DataFrame({
        'sensor_id': ['sensor-001'],
        'timestamp': [pd.Timestamp('2025-01-01')],
        'quality': [0.95]
    })

    transformer = SensorFeatureTransformer()
    with pytest.raises(ValueError, match="Missing required scale columns"):
        transformer.fit(df_invalid)


if __name__ == "__main__":
    # Run tests when script is executed directly
    test_sensor_feature_transformer()
    test_sensor_feature_transformer_fit_transform()
    print("All tests passed!")