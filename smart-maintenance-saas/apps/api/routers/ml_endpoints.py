"""
ML Endpoints Router

This module provides production-ready ML API endpoints for prediction and anomaly detection
using our validated MLflow Model Registry integration from Day 11.
"""

import logging
import uuid
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, status, Security
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import api_key_auth
from apps.ml.model_loader import load_model
from core.database.session import get_async_db
from data.schemas import AnomalyAlert, AnomalyType, SensorReading
from scipy.stats import ks_2samp

from core.database.crud.crud_sensor_reading import crud_sensor_reading

try:  # Resolve model versions when "auto" requested
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency already present in services
    MLFLOW_AVAILABLE = False
    mlflow = None
    MlflowClient = None

# SHAP for explainable AI
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting configuration
def get_api_key_identifier(request: Request):
    """Get rate limiting identifier from X-API-Key header, fallback to IP address."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    return get_remote_address(request)

# Initialize rate limiter for ML endpoints
limiter = Limiter(key_func=get_api_key_identifier)

ANOMALY_DEFAULT_FEATURE_ORDER = [
    "value_lag_1",
    "value_lag_2",
    "value_lag_3",
    "value_lag_4",
    "value_lag_5",
    "value_scaled",
    "quality_scaled",
]
ANOMALY_HISTORY_LOOKBACK = 12  # Fetch a modest history window per sensor for lag construction
ANOMALY_SCALE_BASELINES = {
    "value": {"min": 12.816, "max": 83.193},
    "quality": {"min": 0.0, "max": 1.0},
}


def _min_max_scale(value: float, lower: float, upper: float) -> float:
    """Safely scale a numeric value into [0, 1] range."""
    if upper <= lower:
        return 0.5
    scaled = (value - lower) / (upper - lower)
    return float(min(1.0, max(0.0, scaled)))


def _resolve_feature_order(
    feature_names: Optional[List[str]],
    model,
    expected_count: Optional[int],
) -> List[str]:
    """Resolve the feature ordering to feed the anomaly model."""
    if feature_names and isinstance(feature_names, list):
        if expected_count is None or len(feature_names) == expected_count:
            return feature_names

    model_feature_names = getattr(model, "feature_names_in_", None)
    if model_feature_names is not None:
        model_feature_list = list(model_feature_names)
        if expected_count is None or len(model_feature_list) == expected_count:
            return model_feature_list

    if expected_count:
        if expected_count <= len(ANOMALY_DEFAULT_FEATURE_ORDER):
            return ANOMALY_DEFAULT_FEATURE_ORDER[:expected_count]
        padding = [
            f"feature_{idx}" for idx in range(len(ANOMALY_DEFAULT_FEATURE_ORDER) + 1, expected_count + 1)
        ]
        return ANOMALY_DEFAULT_FEATURE_ORDER + padding

    return ANOMALY_DEFAULT_FEATURE_ORDER


async def _fetch_sensor_histories(
    db: AsyncSession,
    readings: List[SensorReading],
    history_limit: int = ANOMALY_HISTORY_LOOKBACK,
) -> Dict[str, List[SensorReading]]:
    """Retrieve recent sensor readings per sensor_id for feature engineering."""
    histories: Dict[str, List[SensorReading]] = {}
    for reading in readings:
        sensor_id = reading.sensor_id
        if not sensor_id or sensor_id in histories:
            continue
        try:
            raw_history = await crud_sensor_reading.get_sensor_readings_by_sensor_id(
                db,
                sensor_id=sensor_id,
                limit=history_limit,
            )
            histories[sensor_id] = [
                crud_sensor_reading.orm_to_pydantic(item) for item in raw_history
            ]
        except Exception as history_error:  # noqa: BLE001
            logger.warning(
                "Unable to load historical readings for sensor %s: %s",
                sensor_id,
                history_error,
            )
            histories[sensor_id] = []
    return histories


# ==============================================================================
# REQUEST/RESPONSE SCHEMAS
# ==============================================================================

class PredictionRequest(BaseModel):
    """Request schema for /predict endpoint"""
    
    model_name: str = Field(..., description="Name of the model in MLflow Registry")
    model_version: str = Field(default="auto", description="Version of the model (default: auto-resolve)")
    features: Dict[str, Any] = Field(..., description="Feature values for prediction")
    sensor_id: Optional[str] = Field(None, description="Optional sensor ID for tracking")
    explain: bool = Field(True, description="Whether to compute SHAP explainability (can add latency)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "ai4i_classifier_randomforest_baseline",
                "model_version": "2",
                "features": {
                    "Air_temperature_K": 298.1,
                    "Process_temperature_K": 308.6,
                    "Rotational_speed_rpm": 1551,
                    "Torque_Nm": 42.8,
                    "Tool_wear_min": 108
                },
                "sensor_id": "sensor_001"
            }
        }


class PredictionResponse(BaseModel):
    """Response schema for /predict endpoint"""
    
    prediction: Any = Field(..., description="Model prediction result")
    confidence: Optional[float] = Field(None, description="Prediction confidence score")
    model_info: Dict[str, str] = Field(..., description="Model metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Prediction timestamp")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request ID")
    shap_values: Optional[Dict[str, Any]] = Field(None, description="SHAP explainability values")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Feature importance scores")
    
    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class AnomalyDetectionRequest(BaseModel):
    """Request schema for /detect_anomaly endpoint"""
    
    sensor_readings: List[SensorReading] = Field(..., description="Sensor readings to analyze")
    model_name: str = Field(default="anomaly_detector_refined_v2", description="Anomaly detection model name")
    model_version: str = Field(default="auto", description="Model version (auto-resolve)")
    sensitivity: float = Field(default=0.5, ge=0.0, le=1.0, description="Detection sensitivity (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_readings": [
                    {
                        "sensor_id": "sensor_001",
                        "sensor_type": "temperature",
                        "value": 75.5,
                        "unit": "°C",
                        "timestamp": "2025-08-21T10:00:00Z",
                        "quality": 1.0
                    }
                ],
                "model_name": "anomaly_detector_refined_v2",
                "model_version": "latest",
                "sensitivity": 0.7
            }
        }


class AnomalyDetectionResponse(BaseModel):
    """Response schema for /detect_anomaly endpoint"""
    
    anomalies_detected: List[AnomalyAlert] = Field(..., description="Detected anomalies")
    total_readings_analyzed: int = Field(..., description="Total number of readings analyzed")
    anomaly_count: int = Field(..., description="Number of anomalies detected")
    model_info: Dict[str, str] = Field(..., description="Model metadata")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request ID")
    
    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class DriftCheckRequest(BaseModel):
    """Request schema for /check_drift endpoint.

    Compares recent window of sensor readings vs a preceding baseline window
    using a two-sample Kolmogorov–Smirnov test over the numeric `value` field.
    """

    sensor_id: str = Field(..., description="Sensor identifier to evaluate")
    window_minutes: int = Field(60, gt=0, le=24*60, description="Size (minutes) of the recent window")
    p_value_threshold: float = Field(0.05, gt=0, lt=1, description="P-value threshold below which drift is flagged")
    min_samples: int = Field(30, gt=5, le=10000, description="Minimum samples required in each window to run test")

    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "sensor_001",
                "window_minutes": 60,
                "p_value_threshold": 0.05,
                "min_samples": 30,
            }
        }


class DriftCheckResponse(BaseModel):
    """Response schema for /check_drift endpoint."""

    sensor_id: str
    recent_count: int
    baseline_count: int
    window_minutes: int
    ks_statistic: Optional[float]
    p_value: Optional[float]
    p_value_threshold: float
    drift_detected: bool
    insufficient_data: bool = False
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class ForecastPoint(BaseModel):
    """Single forecasted point returned to the caller."""

    timestamp: datetime = Field(..., description="Forecasted timestamp in UTC")
    predicted_value: float = Field(..., description="Model predicted value for the timestamp")
    lower_bound: Optional[float] = Field(None, description="Lower prediction interval bound if available")
    upper_bound: Optional[float] = Field(None, description="Upper prediction interval bound if available")


class ForecastResponse(BaseModel):
    """Forecast results generated for a sensor."""

    sensor_id: str
    model_name: str
    model_version: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    history_points: int
    horizon_steps: int
    cadence_minutes: int
    forecast: List[ForecastPoint]
    metrics: Optional[Dict[str, Any]] = None


class ForecastRequest(BaseModel):
    """Payload for generating forecasts for a sensor."""

    sensor_id: str = Field(..., description="Sensor identifier to forecast for")
    model_name: str = Field(..., description="Registered model name")
    model_version: str = Field(default="auto", description="Specific model version or 'auto' for latest")
    history_window: int = Field(default=288, ge=10, le=1000, description="Number of latest readings to use")
    horizon_steps: int = Field(default=12, ge=1, le=288, description="Number of future predictions to generate")
    cadence_minutes: Optional[int] = Field(None, description="Override cadence in minutes; defaults to sensor cadence")


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def compute_shap_explanation(model, feature_array: np.ndarray, feature_names: List[str] = None) -> Optional[Dict[str, Any]]:
    """
    Compute SHAP values for model explainability.
    
    Args:
        model: Trained model
        feature_array: Input features
        feature_names: List of feature names
        
    Returns:
        Dictionary with SHAP values and feature importance, or None if SHAP not available
    """
    if not SHAP_AVAILABLE:
        logger.warning("SHAP not available for explainability")
        return None
    
    try:
        # Check if model is tree-based (supports TreeExplainer)
        model_type = str(type(model)).lower()
        
        if any(tree_type in model_type for tree_type in ['forest', 'tree', 'lgb', 'xgb', 'catboost']):
            # Use TreeExplainer for tree-based models
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(feature_array)
            
            # Handle multi-class outputs
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # Use first class for simplicity
                
        else:
            # Use KernelExplainer for other models (slower but more general)
            # Create a small background dataset from the input
            background = np.zeros((min(10, feature_array.shape[0]), feature_array.shape[1]))
            explainer = shap.KernelExplainer(model.predict, background)
            shap_values = explainer.shap_values(feature_array)
        
        # Convert to feature importance dictionary
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(feature_array.shape[1])]
        
        # For single prediction, extract the first row
        if len(shap_values.shape) > 1:
            importance_values = shap_values[0]
        else:
            importance_values = shap_values
            
        feature_importance = {
            name: float(value) for name, value in zip(feature_names, importance_values)
        }
        
        # Convert SHAP values to dictionary format expected by Pydantic model
        if len(shap_values.shape) > 1:
            shap_values_dict = {
                name: float(value) for name, value in zip(feature_names, shap_values[0])
            }
        else:
            shap_values_dict = {
                name: float(value) for name, value in zip(feature_names, shap_values)
            }
        
        return {
            "shap_values": shap_values_dict,  # Return as dictionary instead of list
            "feature_importance": feature_importance,
            "explainer_type": explainer.__class__.__name__
        }
        
    except Exception as e:
        logger.warning(f"Failed to compute SHAP values: {e}")
        return None


def _resolve_model_version(model_name: str, requested_version: str) -> str:
    """Resolve model version when callers request 'auto' or 'latest'."""

    if requested_version and requested_version.lower() not in {"auto", "latest"}:
        return requested_version

    if not MLFLOW_AVAILABLE:
        logger.warning(
            "MLflow unavailable while resolving version for %s; defaulting to '1'",
            model_name,
        )
        return "1"

    client = MlflowClient()
    stage_preferences = [["Production"], ["Staging"], ["None"], None]
    for stages in stage_preferences:
        try:
            latest_versions = (
                client.get_latest_versions(model_name, stages=stages)
                if stages is not None
                else client.get_latest_versions(model_name)
            )
            if latest_versions:
                return latest_versions[0].version
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to resolve version for %s using stages %s: %s", model_name, stages, exc)
            continue

    try:
        all_versions = client.search_model_versions(f"name='{model_name}'")
        if all_versions:
            sorted_versions = sorted(all_versions, key=lambda mv: int(mv.version), reverse=True)
            return sorted_versions[0].version
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unable to enumerate versions for %s: %s", model_name, exc)

    return "1"


def prepare_features_for_prediction(features: Dict[str, Any], model_name: str) -> np.ndarray:
    """
    Prepare feature dictionary for model prediction.
    
    Args:
        features: Raw feature dictionary
        model_name: Name of the model (for model-specific preprocessing)
        
    Returns:
        Prepared feature array for model input
    """
    try:
        # Convert to DataFrame for consistent preprocessing
        df = pd.DataFrame([features])
        
        # Model-specific feature preparation
        if "ai4i" in model_name.lower():
            # AI4I dataset specific features
            expected_features = [
                "Air_temperature_K", "Process_temperature_K", 
                "Rotational_speed_rpm", "Torque_Nm", "Tool_wear_min"
            ]
            
            # Ensure all expected features are present
            missing_features = [f for f in expected_features if f not in df.columns]
            if missing_features:
                raise ValueError(f"Missing required features: {missing_features}")
                
            # Select and order features
            df = df[expected_features]
            
        elif "vibration" in model_name.lower():
            # Vibration analysis specific preprocessing
            # Add your vibration-specific feature preparation here
            pass
            
        return df.values
        
    except Exception as e:
        logger.error(f"Error preparing features for model {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feature preparation failed: {str(e)}"
        )


def analyze_sensor_readings_for_anomalies(
    readings: List[SensorReading],
    model,
    sensitivity: float,
    feature_names: Optional[List[str]] = None,
    sensor_histories: Optional[Dict[str, List[SensorReading]]] = None,
) -> List[AnomalyAlert]:
    """
    Analyze sensor readings for anomalies using the loaded model.

    Builds feature vectors that mirror the feature engineering used during training
    (lagged value windows and scaled value/quality columns).
    """
    sensor_histories = sensor_histories or {}
    anomalies: List[AnomalyAlert] = []
    expected_features = getattr(model, "n_features_in_", None)
    feature_order = _resolve_feature_order(feature_names, model, expected_features)

    try:
        for reading in readings:
            if reading.value is None:
                logger.debug("Skipping reading %s due to missing value", reading.sensor_id)
                continue

            sensor_id = reading.sensor_id or "unknown"
            history = sensor_histories.get(sensor_id, [])
            sorted_history = sorted(
                history,
                key=lambda item: item.timestamp or datetime.min,
            )

            # Gather prior values strictly before the current reading when timestamps allow.
            lag_candidates: List[float] = []
            for item in sorted_history:
                if item.value is None:
                    continue
                if reading.timestamp and item.timestamp and item.timestamp >= reading.timestamp:
                    continue
                lag_candidates.append(float(item.value))

            current_value = float(reading.value)
            if not lag_candidates:
                lag_candidates = [current_value]

            lag_values: List[float] = []
            for offset in range(1, 6):
                index = -offset
                if len(lag_candidates) >= offset:
                    lag_values.append(float(lag_candidates[index]))
                else:
                    lag_values.append(float(lag_candidates[0]))

            # Min-max scaling for value and quality using training baselines extended with live data.
            value_reference = lag_candidates + [current_value]
            value_lower = min([ANOMALY_SCALE_BASELINES["value"]["min"]] + value_reference)
            value_upper = max([ANOMALY_SCALE_BASELINES["value"]["max"]] + value_reference)
            value_scaled = _min_max_scale(current_value, value_lower, value_upper)

            quality_value = float(reading.quality) if reading.quality is not None else 0.5
            quality_reference = [quality_value]
            for item in sorted_history:
                if item.quality is not None:
                    quality_reference.append(float(item.quality))
            quality_lower = min([ANOMALY_SCALE_BASELINES["quality"]["min"]] + quality_reference)
            quality_upper = max([ANOMALY_SCALE_BASELINES["quality"]["max"]] + quality_reference)
            quality_scaled = _min_max_scale(quality_value, quality_lower, quality_upper)

            feature_payload: Dict[str, float] = {
                "value_scaled": value_scaled,
                "quality_scaled": quality_scaled,
            }
            for idx, name in enumerate(ANOMALY_DEFAULT_FEATURE_ORDER[:5]):
                feature_payload[name] = lag_values[idx]

            ordered_payload = {name: float(feature_payload.get(name, 0.0)) for name in feature_order}
            feature_df = pd.DataFrame([ordered_payload], columns=feature_order)
            feature_array = feature_df.to_numpy(dtype=float)

            prediction = model.predict(feature_df)
            prediction_array = np.asarray(prediction)
            prediction_value = prediction_array.flat[0] if prediction_array.size else prediction
            is_anomaly_label = bool(prediction_value == -1 or str(prediction_value).lower() == "anomaly")

            anomaly_score = None
            native_model = getattr(model, "_model_impl", None)
            if native_model is not None:
                if hasattr(native_model, "decision_function"):
                    try:
                        raw_decision = float(native_model.decision_function(feature_array)[0])
                        anomaly_score = 1.0 / (1.0 + math.exp(raw_decision))
                    except Exception as score_error:  # noqa: BLE001
                        logger.debug("decision_function failed for %s: %s", sensor_id, score_error)
                if anomaly_score is None and hasattr(native_model, "score_samples"):
                    try:
                        raw_score = float(native_model.score_samples(feature_array)[0])
                        anomaly_score = 1.0 / (1.0 + math.exp(-raw_score))
                    except Exception as score_error:  # noqa: BLE001
                        logger.debug("score_samples failed for %s: %s", sensor_id, score_error)

            if anomaly_score is None:
                anomaly_score = 1.0 if is_anomaly_label else 0.0

            is_anomaly = is_anomaly_label or anomaly_score >= sensitivity
            if not is_anomaly:
                continue

            severity = min(5, max(1, int(round(anomaly_score * 5))))
            anomaly = AnomalyAlert(
                sensor_id=sensor_id,
                anomaly_type=AnomalyType.ISOLATION_FOREST,
                severity=severity,
                confidence=anomaly_score,
                description=(
                    f"Isolation Forest detected anomaly (score={anomaly_score:.3f}, "
                    f"sensitivity={sensitivity:.2f})"
                ),
                evidence={
                    "sensor_value": current_value,
                    "sensor_unit": reading.unit,
                    "sensor_type": str(reading.sensor_type),
                    "quality_score": quality_value,
                    "feature_vector": ordered_payload,
                },
                recommended_actions=[
                    "Investigate sensor reading",
                    "Check sensor calibration",
                    "Review historical data for patterns",
                ],
            )
            anomalies.append(anomaly)

    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error analyzing sensor readings for anomalies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly analysis failed: {str(e)}",
        ) from e

    return anomalies


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@router.get("/models", tags=["ML Models"], dependencies=[Security(api_key_auth, scopes=["ml:predict"])])
async def list_registered_models():
    """List all registered models from the MLflow registry.
    
    Returns a list of models with their metadata including name, version, tags, and timestamps.
    This endpoint provides the data needed for the Model Metadata UI page.
    
    Returns:
        List of model dictionaries with keys: name, description, latest_version, 
        creation_timestamp, last_updated_timestamp, tags, version_tags, current_stage, run_id
    """
    try:
        from apps.ml.model_utils import get_all_registered_models
        
        # Check if MLflow is disabled
        import os
        if os.getenv("DISABLE_MLFLOW_MODEL_LOADING", "false").lower() in ("1", "true", "yes"):
            return {"models": [], "message": "MLflow model loading is disabled"}
        
        # Call the utility function (without Streamlit caching)
        models = get_all_registered_models()
        
        logger.info(f"Retrieved {len(models)} registered models")
        return {"models": models, "count": len(models)}
        
    except Exception as e:
        logger.error(f"Failed to list registered models: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to retrieve models from MLflow registry: {str(e)}"
        ) from e


@router.get("/models/{model_name}/versions", tags=["ML Models"], dependencies=[Security(api_key_auth, scopes=["ml:predict"])])
async def list_model_versions(model_name: str):
    """List available versions for a given model in the MLflow registry.

    Returns versions sorted descending (newest first). If the model name does not exist
    a 404 is raised.
    """
    try:
        import mlflow
        client = mlflow.tracking.MlflowClient()
        # Get *all* registered models then filter; or use search_model_versions
        all_versions = client.search_model_versions(f"name='{model_name}'")
        if not all_versions:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        versions = []
        for mv in all_versions:
            versions.append({
                "version": mv.version,
                "current_stage": getattr(mv, 'current_stage', None),
                "status": getattr(mv, 'status', None),
                "creation_timestamp": getattr(mv, 'creation_timestamp', None)
            })
        # Sort newest first by numeric version
        versions.sort(key=lambda v: int(v["version"]), reverse=True)
        return {"model_name": model_name, "versions": versions}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed listing versions for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {e}") from e


@router.get("/models/{model_name}/latest", tags=["ML Models"], dependencies=[Security(api_key_auth, scopes=["ml:predict"])])
async def get_latest_model_version(model_name: str):
    """Resolve the latest available version for a model.

    Strategy:
    1. Try MLflow client.get_latest_versions (stages None, Production, Staging in priority order)
    2. Fallback: list all versions and pick max numeric.
    """
    try:
        import mlflow
        client = mlflow.tracking.MlflowClient()
        # Attempt to get latest in preferred stage ordering
        stage_order = ["Production", "Staging", None, "None"]
        chosen = None
        for stage in stage_order:
            try:
                latest = client.get_latest_versions(model_name, stages=[stage] if stage else ["None"])  # MLflow expects ["None"] for unassigned
                if latest:
                    chosen = latest[0]
                    break
            except Exception:
                continue
        if not chosen:
            # Fallback: enumerate all versions
            all_versions = client.search_model_versions(f"name='{model_name}'")
            if not all_versions:
                raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
            chosen = sorted(all_versions, key=lambda mv: int(mv.version), reverse=True)[0]
        return {
            "model_name": model_name,
            "resolved_version": chosen.version,
            "current_stage": getattr(chosen, 'current_stage', None),
            "status": getattr(chosen, 'status', None)
        }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed resolving latest version for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve latest version: {e}") from e

@router.post("/predict", response_model=PredictionResponse, tags=["ML Prediction"], dependencies=[Security(api_key_auth, scopes=["ml:predict"])])
async def predict(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_async_db)
) -> PredictionResponse:
    """
    Generate predictions using trained models from MLflow Model Registry.
    
    This endpoint loads models from our validated MLflow infrastructure and 
    provides real-time predictions for maintenance scenarios.
    
    Features automatic model version resolution and flexible feature handling.
    """
    logger.info(f"Prediction request for model: {request.model_name} v{request.model_version}")
    
    try:
        # Step 1: Resolve model version automatically if needed
        resolved_version = request.model_version
        if request.model_version == "latest" or request.model_version == "auto":
            try:
                # Try to get the latest version from MLflow
                import mlflow
                client = mlflow.tracking.MlflowClient()
                latest_versions = client.get_latest_versions(request.model_name, stages=["None"])
                if latest_versions:
                    resolved_version = latest_versions[0].version
                    logger.info(f"Auto-resolved version for {request.model_name}: {resolved_version}")
                else:
                    # Fallback: try common version numbers
                    for version in ["4", "3", "2", "1"]:
                        try:
                            model, _ = load_model(request.model_name, version)
                            if model is not None:
                                resolved_version = version
                                logger.info(f"Fallback resolved version for {request.model_name}: {resolved_version}")
                                break
                        except:
                            continue
            except Exception as e:
                logger.warning(f"Auto-resolution failed, using original version: {e}")
        
        # Step 2: Load model with resolved version
        model, feature_names = load_model(request.model_name, resolved_version)

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{request.model_name}' version '{resolved_version}' not found in MLflow Registry"
            )

        # Step 3: Flexible feature handling - adapt features to model expectations
        prediction_input = None  # Initialize prediction_input variable
        
        try:
            # Try to prepare features normally first
            feature_array = prepare_features_for_prediction(request.features, request.model_name)
            
            # Check if the feature count matches model expectations
            prediction_input = feature_array.reshape(1, -1)
            
            # Try prediction to see if dimensions match
            prediction = model.predict(prediction_input)
            
        except Exception as feature_error:
            logger.warning(f"Standard feature preparation failed: {feature_error}")
            
            # Step 4: Flexible feature adaptation
            try:
                # Get model's expected feature count
                if hasattr(model, 'n_features_in_'):
                    expected_features = model.n_features_in_
                elif hasattr(model, 'feature_importances_'):
                    expected_features = len(model.feature_importances_)
                else:
                    # Try to infer from a test prediction
                    test_input = np.zeros((1, len(request.features)))
                    try:
                        model.predict(test_input)
                        expected_features = len(request.features)
                    except Exception as e:
                        # Extract expected feature count from error message
                        error_str = str(e)
                        if "expecting" in error_str and "features" in error_str:
                            import re
                            match = re.search(r'expecting (\d+) features', error_str)
                            if match:
                                expected_features = int(match.group(1))
                            else:
                                expected_features = 12  # Common default
                        else:
                            expected_features = 12
                
                logger.info(f"Model expects {expected_features} features, adapting input...")
                
                # Create feature vector of the right size
                feature_values = list(request.features.values())
                
                if len(feature_values) < expected_features:
                    # Pad with zeros or repeat last value
                    padding_needed = expected_features - len(feature_values)
                    if len(feature_values) > 0:
                        # Repeat the mean of existing features
                        mean_value = np.mean(feature_values)
                        feature_values.extend([mean_value] * padding_needed)
                    else:
                        # All zeros if no features provided
                        feature_values = [0.0] * expected_features
                elif len(feature_values) > expected_features:
                    # Truncate to expected size
                    feature_values = feature_values[:expected_features]
                
                # Create prediction input
                prediction_input = np.array(feature_values).reshape(1, -1)
                
                # Generate prediction
                prediction = model.predict(prediction_input)
                
                logger.info(f"Successfully adapted features from {len(request.features)} to {expected_features}")
                
            except Exception as adapt_error:
                logger.error(f"Feature adaptation failed: {adapt_error}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Feature adaptation failed",
                        "model_name": request.model_name,
                        "model_version": resolved_version,
                        "provided_features": len(request.features),
                        "adaptation_error": str(adapt_error),
                        "suggestion": "Try using a different model or check feature requirements"
                    }
                )
        
        # At this point we have a successful prediction
        # prediction_input contains the final feature array used
        
        # Extract confidence if available (model-dependent)
        confidence = None
        if hasattr(model, 'predict_proba'):
            try:
                proba = model.predict_proba(prediction_input)
                confidence = float(np.max(proba))
            except Exception as e:
                logger.warning(f"Could not extract confidence: {e}")
        
        # Compute SHAP explainability (optional)
        shap_explanation = None
        if request.explain:
            import time
            start_time = time.time()
            try:
                shap_explanation = compute_shap_explanation(model, prediction_input, feature_names)
                shap_duration = time.time() - start_time
                logger.info(f"SHAP computation completed in {shap_duration:.3f}s for model {request.model_name}")
                if shap_duration > 5.0:
                    logger.warning(f"SHAP computation exceeded 5s (took {shap_duration:.2f}s)")
            except Exception as shap_err:
                logger.warning(f"SHAP computation failed: {shap_err}")
        else:
            logger.info("Explainability skipped per request (explain=false)")
        
        # Prepare response
        response = PredictionResponse(
            prediction=prediction.tolist() if hasattr(prediction, 'tolist') else prediction,
            confidence=confidence,
            model_info={
                "model_name": request.model_name,
                "model_version": resolved_version,  # Use resolved version
                "loaded_from": "MLflow Model Registry",
                "feature_adaptation": f"Adapted {len(request.features)} input features"
            },
            shap_values=shap_explanation.get("shap_values") if shap_explanation else None,
            feature_importance=shap_explanation.get("feature_importance") if shap_explanation else None
        )
        
        logger.info(f"Prediction completed successfully for model: {request.model_name} v{resolved_version}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for model {request.model_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post(
    "/forecast",
    response_model=ForecastResponse,
    tags=["ML Prediction"],
    dependencies=[Security(api_key_auth, scopes=["ml:predict"])],
)
async def forecast_sensor(
    request: ForecastRequest,
    db: AsyncSession = Depends(get_async_db),
) -> ForecastResponse:
    """Generate time-series forecasts for a sensor using registered MLflow models."""

    history = await crud_sensor_reading.get_sensor_readings_by_sensor_id(
        db,
        sensor_id=request.sensor_id,
        limit=request.history_window,
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No readings found for sensor '{request.sensor_id}'",
        )

    history_sorted = sorted(
        [h for h in history if h.timestamp is not None],
        key=lambda item: item.timestamp,
    )

    if not history_sorted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor '{request.sensor_id}' does not have timestamped readings",
        )

    history_df = pd.DataFrame(
        {
            "timestamp": [item.timestamp.replace(tzinfo=None) if item.timestamp.tzinfo else item.timestamp for item in history_sorted],
            "value": [float(item.value) if item.value is not None else np.nan for item in history_sorted],
            "quality": [float(item.quality) if item.quality is not None else np.nan for item in history_sorted],
        }
    ).dropna(subset=["timestamp", "value"])

    if history_df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient data after cleaning to perform forecast",
        )

    cadence_minutes = request.cadence_minutes
    if cadence_minutes is None and len(history_df) >= 2:
        diffs = history_df["timestamp"].diff().dropna()
        if not diffs.empty:
            median_minutes = float(diffs.dt.total_seconds().median() / 60.0)
            if median_minutes > 0:
                cadence_minutes = max(1, int(round(median_minutes)))

    if cadence_minutes is None or cadence_minutes <= 0:
        cadence_minutes = 5  # sensible default for synthetic dataset cadence

    resolved_version = _resolve_model_version(request.model_name, request.model_version)
    model, _ = load_model(request.model_name, resolved_version)

    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{request.model_name}' version '{resolved_version}' not found",
        )

    last_timestamp = history_df["timestamp"].iloc[-1]
    future_index = pd.date_range(
        start=last_timestamp + pd.Timedelta(minutes=cadence_minutes),
        periods=request.horizon_steps,
        freq=f"{cadence_minutes}min",
    )

    future_payload = pd.DataFrame({"ds": future_index})

    try:
        forecast_raw = model.predict(future_payload)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Forecast prediction failed for %s v%s: %s",
            request.model_name,
            resolved_version,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast prediction failed: {exc}",
        ) from exc

    if isinstance(forecast_raw, pd.DataFrame):
        forecast_df = forecast_raw.copy()
    else:
        forecast_df = pd.DataFrame({"yhat": np.array(forecast_raw).reshape(-1)})
        forecast_df["ds"] = future_index[: len(forecast_df)]

    forecast_points: List[ForecastPoint] = []
    for _, row in forecast_df.head(request.horizon_steps).iterrows():
        raw_ts = row.get("ds") or row.get("timestamp")
        if pd.isna(raw_ts):
            continue
        ts = pd.to_datetime(raw_ts).to_pydatetime()
        if ts.tzinfo:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        predicted = row.get("yhat")
        if predicted is None or pd.isna(predicted):
            continue
        lower = row.get("yhat_lower")
        upper = row.get("yhat_upper")
        forecast_points.append(
            ForecastPoint(
                timestamp=ts,
                predicted_value=float(predicted),
                lower_bound=float(lower) if lower is not None and not pd.isna(lower) else None,
                upper_bound=float(upper) if upper is not None and not pd.isna(upper) else None,
            )
        )

    if not forecast_points:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Forecast model returned empty results",
        )

    metrics = {
        "history_start": history_df["timestamp"].iloc[0].isoformat(),
        "history_end": history_df["timestamp"].iloc[-1].isoformat(),
        "history_points": len(history_df),
        "cadence_minutes": cadence_minutes,
    }

    return ForecastResponse(
        sensor_id=request.sensor_id,
        model_name=request.model_name,
        model_version=resolved_version,
        history_points=len(history_df),
        horizon_steps=len(forecast_points),
        cadence_minutes=cadence_minutes,
        forecast=forecast_points,
        metrics=metrics,
    )


@router.post("/detect_anomaly", response_model=AnomalyDetectionResponse, tags=["ML Anomaly Detection"], dependencies=[Security(api_key_auth, scopes=["ml:anomaly"])])
async def detect_anomaly(
    request: AnomalyDetectionRequest,
    db: AsyncSession = Depends(get_async_db)
) -> AnomalyDetectionResponse:
    """
    Detect anomalies in sensor readings using trained anomaly detection models.
    
    This endpoint analyzes sensor data for unusual patterns and generates
    anomaly alerts with confidence scores and recommended actions.
    """
    logger.info(f"Anomaly detection request for {len(request.sensor_readings)} readings")
    
    try:
        # Load anomaly detection model from MLflow Registry
        model, feature_names = load_model(request.model_name, request.model_version)

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anomaly detection model '{request.model_name}' version '{request.model_version}' not found"
            )
        
        # Fetch sensor histories for feature enrichment
        sensor_histories = await _fetch_sensor_histories(db, request.sensor_readings, ANOMALY_HISTORY_LOOKBACK)

        # Analyze sensor readings for anomalies
        detected_anomalies = analyze_sensor_readings_for_anomalies(
            request.sensor_readings,
            model,
            request.sensitivity,
            feature_names=feature_names,
            sensor_histories=sensor_histories,
        )
        
        # Prepare response
        response = AnomalyDetectionResponse(
            anomalies_detected=detected_anomalies,
            total_readings_analyzed=len(request.sensor_readings),
            anomaly_count=len(detected_anomalies),
            model_info={
                "model_name": request.model_name,
                "model_version": str(request.model_version),
                "sensitivity": f"{request.sensitivity:.3f}",
                "loaded_from": "MLflow Model Registry"
            }
        )
        
        logger.info(f"Anomaly detection completed: {len(detected_anomalies)} anomalies found in {len(request.sensor_readings)} readings")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )


@router.post("/check_drift", response_model=DriftCheckResponse, tags=["ML Drift"], dependencies=[Security(api_key_auth, scopes=["ml:drift"])])
@limiter.limit("10/minute")
async def check_drift(
    request: Request,
    drift_request: DriftCheckRequest,
    db: AsyncSession = Depends(get_async_db)
) -> DriftCheckResponse:
    """Check for statistical drift in a sensor's readings.

    Implementation notes:
    - Recent window: now - window_minutes .. now
    - Baseline window: (recent_start - window_minutes) .. recent_start
    - Uses KS test (two-sided) on the numeric `value` distribution.
    - Flags drift when p-value < threshold.
    - Returns insufficient_data=True if either window lacks min_samples.
    - Optimized by leveraging composite index (sensor_id, timestamp DESC) via time bounded queries.
    """
    now = datetime.utcnow()
    recent_start = now - timedelta(minutes=drift_request.window_minutes)
    baseline_start = recent_start - timedelta(minutes=drift_request.window_minutes)
    baseline_end = recent_start

    try:
        # Fetch baseline readings
        baseline_readings = await crud_sensor_reading.get_sensor_readings_by_sensor_id(
            db,
            sensor_id=drift_request.sensor_id,
            start_time=baseline_start,
            end_time=baseline_end,
            limit=drift_request.min_samples * 5,  # heuristic buffer
        )
        # Fetch recent readings
        recent_readings = await crud_sensor_reading.get_sensor_readings_by_sensor_id(
            db,
            sensor_id=drift_request.sensor_id,
            start_time=recent_start,
            end_time=now,
            limit=drift_request.min_samples * 5,
        )

        baseline_values = [r.value for r in baseline_readings]
        recent_values = [r.value for r in recent_readings]

        insufficient = False
        ks_statistic = None
        p_value = None
        drift_detected = False
        notes = None

        if len(baseline_values) < drift_request.min_samples or len(recent_values) < drift_request.min_samples:
            insufficient = True
            notes = (
                f"Insufficient samples: baseline={len(baseline_values)}, recent={len(recent_values)}, "
                f"required={drift_request.min_samples}"
            )
        else:
            try:
                ks_res = ks_2samp(baseline_values, recent_values, alternative="two-sided", mode="auto")
                ks_statistic = float(ks_res.statistic)
                p_value = float(ks_res.pvalue)
                drift_detected = p_value < drift_request.p_value_threshold
            except Exception as stats_err:
                logger.error(f"Drift stats computation failed: {stats_err}")
                notes = f"Stats computation error: {stats_err}"

        return DriftCheckResponse(
            sensor_id=drift_request.sensor_id,
            recent_count=len(recent_values),
            baseline_count=len(baseline_values),
            window_minutes=drift_request.window_minutes,
            ks_statistic=ks_statistic,
            p_value=p_value,
            p_value_threshold=drift_request.p_value_threshold,
            drift_detected=drift_detected,
            insufficient_data=insufficient,
            notes=notes,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Drift check failed for sensor {drift_request.sensor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift check failed: {str(e)}"
        )


# ==============================================================================
# HEALTH CHECK ENDPOINT
# ==============================================================================

@router.get("/health", tags=["ML Health"])
async def ml_health_check():
    """
    Health check endpoint for ML services.
    
    Verifies connectivity to MLflow and basic model loading capability.
    """
    try:
        # Test MLflow connectivity by attempting to load a model that actually exists
        # Using version "4" (latest actual version) instead of "latest" string
        test_model, _ = load_model("anomaly_detector_refined_v2", "4")  # Use actual version number

        if test_model is not None:
            return {
                "status": "healthy",
                "mlflow_connection": "ok",
                "model_registry": "accessible",
                "test_model_loaded": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "mlflow_connection": "ok", 
                "model_registry": "models not loading",
                "test_model_loaded": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"ML health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }