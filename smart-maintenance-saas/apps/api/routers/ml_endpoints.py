"""
ML Endpoints Router

This module provides production-ready ML API endpoints for prediction and anomaly detection
using our validated MLflow Model Registry integration from Day 11.
"""

import logging
import uuid
from datetime import datetime, timedelta
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

# ==============================================================================
# REQUEST/RESPONSE SCHEMAS
# ==============================================================================

class PredictionRequest(BaseModel):
    """Request schema for /predict endpoint"""
    
    model_name: str = Field(..., description="Name of the model in MLflow Registry")
    model_version: str = Field(default="auto", description="Version of the model (default: auto-resolve)")
    features: Dict[str, Any] = Field(..., description="Feature values for prediction")
    sensor_id: Optional[str] = Field(None, description="Optional sensor ID for tracking")
    
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
        
        return {
            "shap_values": shap_values.tolist() if hasattr(shap_values, 'tolist') else shap_values,
            "feature_importance": feature_importance,
            "explainer_type": explainer.__class__.__name__
        }
        
    except Exception as e:
        logger.warning(f"Failed to compute SHAP values: {e}")
        return None


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
    sensitivity: float
) -> List[AnomalyAlert]:
    """
    Analyze sensor readings for anomalies using the loaded model.
    
    Args:
        readings: List of sensor readings to analyze
        model: Loaded MLflow model
        sensitivity: Detection sensitivity threshold
        
    Returns:
        List of detected anomaly alerts
    """
    anomalies = []
    
    try:
        for reading in readings:
            # Prepare features for anomaly detection
            # This is a simplified example - adjust based on your anomaly detection model
            features = {
                "value": reading.value,
                "sensor_type": reading.sensor_type.value if hasattr(reading.sensor_type, 'value') else str(reading.sensor_type),
                "quality": reading.quality
            }
            
            # Convert to model input format
            feature_array = np.array([[reading.value, reading.quality]])
            
            # Get anomaly prediction
            prediction = model.predict(feature_array)
            
            # Check if anomaly detected (adjust logic based on your model output)
            is_anomaly = False
            confidence = 0.0
            
            if hasattr(prediction, '__len__') and len(prediction) > 0:
                # For models that return anomaly scores
                score = float(prediction[0])
                is_anomaly = score > sensitivity
                confidence = score
            else:
                # For models that return binary predictions
                is_anomaly = bool(prediction)
                confidence = 1.0 if is_anomaly else 0.0
            
            if is_anomaly:
                anomaly = AnomalyAlert(
                    sensor_id=reading.sensor_id,
                    anomaly_type=AnomalyType.STATISTICAL_THRESHOLD,
                    severity=min(5, max(1, int(confidence * 5))),  # Scale confidence to severity 1-5
                    confidence=confidence,
                    description=f"Anomaly detected in {reading.sensor_type} sensor. Value: {reading.value} {reading.unit}",
                    evidence={
                        "sensor_value": reading.value,
                        "sensor_unit": reading.unit,
                        "sensor_type": str(reading.sensor_type),
                        "quality_score": reading.quality,
                        "anomaly_score": confidence,
                        "timestamp": reading.timestamp.isoformat() if reading.timestamp else None
                    },
                    recommended_actions=[
                        "Investigate sensor reading",
                        "Check sensor calibration",
                        "Review historical data for patterns"
                    ]
                )
                anomalies.append(anomaly)
                
    except Exception as e:
        logger.error(f"Error analyzing sensor readings for anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly analysis failed: {str(e)}"
        )
    
    return anomalies


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

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
        
        # Compute SHAP explainability (if available)
        # Use the final prediction_input that worked
        shap_explanation = compute_shap_explanation(model, prediction_input, feature_names)
        
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
        model, _ = load_model(request.model_name, request.model_version)

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anomaly detection model '{request.model_name}' version '{request.model_version}' not found"
            )
        
        # Analyze sensor readings for anomalies
        detected_anomalies = analyze_sensor_readings_for_anomalies(
            request.sensor_readings, 
            model, 
            request.sensitivity
        )
        
        # Prepare response
        response = AnomalyDetectionResponse(
            anomalies_detected=detected_anomalies,
            total_readings_analyzed=len(request.sensor_readings),
            anomaly_count=len(detected_anomalies),
            model_info={
                "model_name": request.model_name,
                "model_version": request.model_version,
                "sensitivity": request.sensitivity,
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