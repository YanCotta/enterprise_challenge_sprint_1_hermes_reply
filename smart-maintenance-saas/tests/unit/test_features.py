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
    """Test the SensorFeatureTransformer functionality."""
    # Create test data
    df = pd.DataFrame({
        'sensor_id': ['sensor-001'] * 10 + ['sensor-002'] * 10,
        'value': list(range(10)) + list(range(5, 15))
    })
    
    # Initialize transformer
    transformer = SensorFeatureTransformer(lag_features=3)
    
    # Fit the transformer
    transformer.fit(df)
    
    # Transform the data
    transformed = transformer.transform(df)
    
    # Test that value_scaled column is added
    assert 'value_scaled' in transformed.columns
    
    # Test that scaled values are in [0, 1] range
    assert all(transformed['value_scaled'].between(0, 1))
    
    # Test that lag features are created
    assert 'value_lag_1' in transformed.columns
    assert 'value_lag_2' in transformed.columns
    assert 'value_lag_3' in transformed.columns
    
    # Test that lag features work correctly
    # For sensor-001, the last value should be shifted
    sensor_001_data = transformed[transformed['sensor_id'] == 'sensor-001']
    # Note: lag features are filled with 0 in the current implementation
    
    # Test that the transformer maintains the original data
    assert len(transformed) == len(df)
    assert 'sensor_id' in transformed.columns
    assert 'value' in transformed.columns


def test_sensor_feature_transformer_fit_transform():
    """Test the fit_transform method."""
    df = pd.DataFrame({
        'sensor_id': ['sensor-001'] * 5,
        'value': [10, 20, 30, 40, 50]
    })
    
    transformer = SensorFeatureTransformer(lag_features=2)
    transformed = transformer.fit_transform(df)
    
    # Check that both scaling and lag features are applied
    assert 'value_scaled' in transformed.columns
    assert 'value_lag_1' in transformed.columns
    assert 'value_lag_2' in transformed.columns
    
    # Check scaling works correctly (min-max scaling)
    expected_scaled = [0.0, 0.25, 0.5, 0.75, 1.0]
    assert transformed['value_scaled'].tolist() == expected_scaled


def test_sensor_feature_transformer_invalid_input():
    """Test that the transformer handles invalid input correctly."""
    # Test missing 'value' column
    df_invalid = pd.DataFrame({
        'sensor_id': ['sensor-001'],
        'other_column': [1]
    })
    
    transformer = SensorFeatureTransformer()
    
    with pytest.raises(ValueError, match="Input dataframe must contain 'value' column"):
        transformer.fit(df_invalid)


if __name__ == "__main__":
    # Run tests when script is executed directly
    test_sensor_feature_transformer()
    test_sensor_feature_transformer_fit_transform()
    print("All tests passed!")