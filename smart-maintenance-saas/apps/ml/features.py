"""
Feature engineering module for Smart Maintenance SaaS.

This module provides shared feature engineering utilities for sensor data processing,
including scaling, lag feature generation, and other transformations needed for ML models.
"""

from typing import Optional, List
import pandas as pd
import numpy as np  # noqa
from sklearn.base import BaseEstimator, TransformerMixin  # noqa
from sklearn.preprocessing import MinMaxScaler  # noqa
import logging

logger = logging.getLogger(__name__)


class SensorFeatureTransformer(BaseEstimator, TransformerMixin):
    """
    Feature transformer for sensor data with scaling and lag feature generation.
    
    This transformer provides:
    - MinMaxScaler for value normalization to [0,1] range
    - Lag features for time series forecasting (1-5 lags per sensor)
    - Proper handling of missing values and sensor grouping
    
    Parameters:
    -----------
    lag_features : int, default=5
        Number of lag features to create for each sensor
    """
    
    def __init__(self, lag_features: int = 5):
        self.scaler = MinMaxScaler()
        self.lag_features = lag_features
        
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> 'SensorFeatureTransformer':
        """
        Fit the transformer on the training data.
        
        Parameters:
        -----------
        X : pd.DataFrame
            Input dataframe with columns: sensor_id, value
        y : pd.Series, optional
            Target values (not used)
            
        Returns:
        --------
        self : SensorFeatureTransformer
            Fitted transformer
        """
        # Validate input
        if 'value' not in X.columns:
            raise ValueError("Input dataframe must contain 'value' column")
        
        self.scaler.fit(X[['value']])
        logger.info(f"SensorFeatureTransformer fitted with {self.lag_features} lag features")
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input data by adding scaled values and lag features.
        
        Parameters:
        -----------
        X : pd.DataFrame
            Input dataframe with columns: sensor_id, value
            
        Returns:
        --------
        X_transformed : pd.DataFrame
            Transformed dataframe with additional features
        """
        X_scaled = X.copy()
        
        # Apply scaling
        X_scaled['value_scaled'] = self.scaler.transform(X[['value']])
        
        # Create lag features for each sensor
        for lag in range(1, self.lag_features + 1):
            X_scaled[f'value_lag_{lag}'] = X.groupby('sensor_id')['value'].shift(lag)
        
        # Fill NaN values with 0 for lag features
        lag_columns = [f'value_lag_{lag}' for lag in range(1, self.lag_features + 1)]
        X_scaled[lag_columns] = X_scaled[lag_columns].fillna(0)
        
        logger.info(f"Transformed {len(X)} samples with {len(X_scaled.columns)} features")
        return X_scaled
    
    def fit_transform(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        Fit the transformer and transform the data in one step.
        
        Parameters:
        -----------
        X : pd.DataFrame
            Input dataframe
        y : pd.Series, optional
            Target values (not used)
            
        Returns:
        --------
        X_transformed : pd.DataFrame
            Transformed dataframe
        """
        return self.fit(X, y).transform(X)