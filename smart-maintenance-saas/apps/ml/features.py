"""Feature engineering utilities for sensor anomaly detection pipeline."""

import logging
from typing import List, Optional

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


class SensorFeatureTransformer(BaseEstimator, TransformerMixin):
    """Custom transformer for sensor data.

    Responsibilities:
    - Generate lag features per sensor_id for the primary numeric signal 'value'.
    - Perform *smart padding* for initial lag-induced NaNs using forward-fill then back-fill within each sensor group.
    - Selectively scale designated numeric columns (e.g., value, quality) with MinMaxScaler.
    - Remove original (unscaled) columns that were scaled to avoid redundancy.
    - Return a purely numeric feature matrix ready for model ingestion.

    Parameters
    ----------
    n_lags : int, default=5
        Number of lag features (value_lag_1 .. value_lag_n).
    scale_columns : list[str] or None, default None -> ['value', 'quality']
        Which columns to scale (each produces a corresponding <col>_scaled column). Originals are dropped.
    """

    def __init__(self, n_lags: int = 5, scale_columns: Optional[List[str]] = None):
        self.n_lags = n_lags
        self.scale_columns = scale_columns if scale_columns else ["value", "quality"]
        self.scaler = MinMaxScaler()
        self._feature_names: List[str] = []

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):  # type: ignore[override]
        missing = set(self.scale_columns) - set(X.columns)
        if missing:
            raise ValueError(f"Missing required scale columns: {missing}")
        if self.scale_columns:
            self.scaler.fit(X[self.scale_columns])
            logger.info("Fitted MinMaxScaler on columns: %s", self.scale_columns)
        return self

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
        required = {"sensor_id", "timestamp", "value"}
        missing = required - set(X.columns)
        if missing:
            raise ValueError(f"Input DataFrame missing required columns: {missing}")

        df = X.copy()
        # Ensure timestamp is datetime for ordering
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        if df["timestamp"].isna().any():
            raise ValueError("Timestamp conversion resulted in NaT values; check source data.")

        # Sort for deterministic lag computation
        df = df.sort_values(["sensor_id", "timestamp"])  # stable ordering

        # Lag feature generation
        logger.info("Creating %d lag features for 'value' column", self.n_lags)
        for i in range(1, self.n_lags + 1):
            df[f"value_lag_{i}"] = df.groupby("sensor_id", sort=False)["value"].shift(i)

        # Smart padding: forward fill then back fill inside each sensor group
        df = (
            df.groupby("sensor_id", group_keys=False)
            .apply(lambda g: g.ffill().bfill())
            .reset_index(drop=True)
        )

        # Selective scaling
        if self.scale_columns:
            logger.info("Scaling columns with MinMaxScaler: %s", self.scale_columns)
            scaled_array = self.scaler.transform(df[self.scale_columns])
            scaled_cols = [f"{col}_scaled" for col in self.scale_columns]
            scaled_df = pd.DataFrame(scaled_array, columns=scaled_cols, index=df.index)
            # Drop originals to avoid redundancy
            df = pd.concat([df.drop(columns=self.scale_columns), scaled_df], axis=1)

        # Keep only numeric features for the model
        numeric_df = df.select_dtypes(include=["number"]).copy()
        self._feature_names = numeric_df.columns.tolist()
        logger.info("Final feature set size: %d", len(self._feature_names))
        return numeric_df

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def fit_transform(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> pd.DataFrame:  # type: ignore[override]
        return self.fit(X, y).transform(X)

    def get_feature_names_out(self, input_features=None):  # sklearn compatibility
        return self._feature_names