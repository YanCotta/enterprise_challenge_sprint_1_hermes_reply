"""Anomaly detection agent for processing sensor data and detecting anomalies."""

import asyncio
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional, Union
import traceback

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from pydantic import ValidationError

from core.base_agent_abc import AgentCapability, BaseAgent
from apps.ml.statistical_models import StatisticalAnomalyDetector
from core.ml.model_loader import get_model_loader, load_model_for_sensor
from core.events.event_bus import EventBus
from core.events.event_models import AnomalyDetectedEvent, DataProcessedEvent
from data.schemas import AnomalyAlert, SensorReading, AnomalyType # Added AnomalyType
from data.exceptions import (
    MLModelError, ConfigurationError, DataValidationException,
    AgentProcessingError, WorkflowError, EventPublishError, SmartMaintenanceBaseException
)


class AnomalyDetectionAgent(BaseAgent):
    """
    Agent responsible for detecting anomalies in processed sensor data using ML models.
    
    Uses both statistical methods and machine learning models (Isolation Forest)
    to identify unusual patterns in sensor readings.

    Resilience Features:
    - Graceful Degradation: If the primary ML models (e.g., Isolation Forest) fail to
      load or predict, the agent can fall back to simpler statistical anomaly detection
      methods or issue a warning, ensuring partial functionality.
    - Event Publishing Retries: Implements a retry mechanism when publishing anomaly
      events to the event bus, enhancing the reliability of critical notifications.
    """

    def __init__(self, agent_id: str, event_bus: EventBus, specific_settings: Optional[dict] = None):
        """
        Initialize the AnomalyDetectionAgent with serverless model loading.
        """
        if not agent_id or not agent_id.strip():
            # This is a programming error, ValueError is fine.
            raise ValueError("agent_id cannot be empty")
        if event_bus is None:
            raise ValueError("event_bus cannot be None")
            
        super().__init__(agent_id, event_bus)
        
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
        # Create proper settings object for test compatibility
        from types import SimpleNamespace
        settings_dict = specific_settings or {}
        
        # Initialize the serverless model loader
        try:
            # Get model loader configuration from settings
            loader_config = settings_dict.get('model_loader_config', {})
            self.model_loader = get_model_loader(**loader_config)
            self.use_serverless_models = settings_dict.get('use_serverless_models', True)
            
            # Create settings object with attributes for test compatibility
            self.settings = SimpleNamespace(
                use_serverless_models=self.use_serverless_models,
                serverless_mode_enabled=settings_dict.get('serverless_mode_enabled', True)
            )
            
            # Add any additional settings from settings_dict that aren't already set
            for key, value in settings_dict.items():
                if not hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            self.logger.info(f"Model loader initialized with serverless mode: {self.use_serverless_models}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize model loader: {e}")
            raise ConfigurationError(f"Model loader initialization failed: {e}") from e
        
        # Fallback models for graceful degradation (only if serverless disabled)
        try:
            if not self.use_serverless_models:
                self.scaler = StandardScaler()
                if_params = self.settings.get('isolation_forest_params', {})
                default_if_params = {
                    'contamination': 'auto', 'random_state': 42, 'n_estimators': 100,
                    'max_samples': 'auto', 'max_features': 1.0
                }
                final_if_params = {**default_if_params, **if_params}
                self.isolation_forest = IsolationForest(**final_if_params)
                self.isolation_forest_fitted = False # Flag to indicate if the model has been fitted
            else:
                # Serverless mode - no local models needed
                self.scaler = None
                self.isolation_forest = None
                self.isolation_forest_fitted = False
            
            # Initialize statistical detector, which can also be a fallback
            stat_config = self.settings.get('statistical_detector_config', {})
            self.statistical_detector = StatisticalAnomalyDetector(config=stat_config)
            
            # Configuration for default standard deviation for unknown sensors
            self.default_historical_std = self.settings.get('default_historical_std', 0.1)
            if self.default_historical_std <= 0:
                # This is a configuration error that prevents proper fallback for new sensors.
                raise ConfigurationError("default_historical_std must be positive")

        except ConfigurationError as ce: # Catch our specific config error first
            self.logger.error(f"Configuration error during AnomalyDetectionAgent init: {ce}", exc_info=True)
            raise # Re-raise as it's a startup issue, critical for agent function
        except ValueError as ve: # Parameter validation errors from model constructors
            self.logger.error(f"Parameter validation error during AnomalyDetectionAgent init: {ve}", exc_info=True)
            raise # Re-raise, likely critical
        except Exception as e:
            self.logger.error(f"Failed to initialize ML models or critical settings: {e}", exc_info=True)
            # This error implies a significant issue with model setup.
            # While the process method has fallback logic, core model initialization failure is severe.
            raise MLModelError(f"Failed to initialize core ML models: {e}", original_exception=e) from e
        
        self.unknown_sensor_baselines: Dict[str, Dict[str, float]] = {}
        self.historical_data_store: Dict[str, Dict[str, float]] = {
            "sensor_temp_001": {"mean": 22.5, "std": 2.1},
            "sensor_vibr_001": {"mean": 0.05, "std": 0.02},
            "sensor_press_001": {"mean": 101.3, "std": 1.5},
        }
        self._validate_historical_data() # Can raise ConfigurationError
        
        self.logger.info(
            f"AnomalyDetectionAgent initialized with ID: {self.agent_id}, serverless: {self.use_serverless_models}",
            extra={"correlation_id": "N/A"} # Correlation ID not available at init
        )

    def _validate_historical_data(self) -> None:
        """Validate the historical data store for consistency."""
        for sensor_id, data in self.historical_data_store.items():
            if not isinstance(data, dict) or 'mean' not in data or 'std' not in data:
                raise ConfigurationError(f"Historical data for {sensor_id} must be a dict with 'mean' and 'std'")
            if not isinstance(data['mean'], (int, float)) or not isinstance(data['std'], (int, float)):
                raise ConfigurationError(f"Mean and std for {sensor_id} must be numeric")
            if data['std'] < 0: # std == 0 might be valid in some edge cases, but negative is not
                raise ConfigurationError(f"Standard deviation for {sensor_id} cannot be negative")
            if data['std'] == 0:
                 self.logger.warning(
                     f"Zero standard deviation for sensor {sensor_id} in historical data.",
                     extra={"correlation_id": "N/A"} # Correlation ID not available at this point
                 )


    async def register_capabilities(self) -> None:
        capability = AgentCapability(
            name="detect_anomalies",
            description="Detects anomalies in processed sensor data using ML models.",
            input_types=[DataProcessedEvent.__name__],
            output_types=[AnomalyDetectedEvent.__name__]
        )
        self.capabilities.append(capability)
        self.logger.debug(
            f"Agent {self.agent_id} registered capability: {capability.name}",
            extra={"correlation_id": "N/A"} # Correlation ID not available at this point
        )

    async def start(self) -> None:
        await super().start()
        await self.event_bus.subscribe(DataProcessedEvent.__name__, self.process)
        self.logger.info(
            f"Agent {self.agent_id} subscribed to {DataProcessedEvent.__name__}.",
            extra={"correlation_id": "N/A"} # Correlation ID not available at this point
        )

    def _extract_features(self, reading: SensorReading) -> np.ndarray:
        # This method is simple; if it grew complex, it could raise AgentProcessingError.
        return np.array([[reading.value]])

    async def process(self, event: DataProcessedEvent) -> None:
        """
        Process a DataProcessedEvent to detect anomalies.
        This method is called by the BaseAgent's handle_event, so errors raised here
        will be caught by BaseAgent.handle_event's try-except blocks.
        """
        _event_id_for_log = getattr(event, 'event_id', 'N/A')
        correlation_id = getattr(event, 'correlation_id', "N/A") # Extract correlation_id for logging

        self.logger.debug(
            f"Received event: {_event_id_for_log} with correlation_id: {correlation_id}",
            extra={"correlation_id": correlation_id}
        )

        if not isinstance(event, DataProcessedEvent):
            # This should ideally not happen if event bus and subscriptions are correct
            self.logger.error(
                f"Expected DataProcessedEvent, got {type(event)}. This is a programming error.",
                extra={"correlation_id": correlation_id}
            )
            # Not raising custom error as it's more of an assertion/guard
            return
            
        try:
            if not event.processed_data or not isinstance(event.processed_data, dict):
                # Raise DataValidationException for bad input structure
                raise DataValidationException("Event contains empty or malformed processed_data.")

            try:
                reading = SensorReading(**event.processed_data)
            except ValidationError as ve:
                self.logger.error(
                    f"Failed to parse sensor reading for event {_event_id_for_log}: {ve}",
                    exc_info=True,
                    extra={"correlation_id": correlation_id}
                )
                raise DataValidationException(
                    message=f"Invalid sensor data payload for event {_event_id_for_log}: {ve}",
                    errors=ve.errors(),
                    original_exception=ve
                ) from ve

            if not self._validate_sensor_reading(reading): # Raises DataValidationException
                # _validate_sensor_reading now raises, so this path might not be taken if it raises first.
                # Defensive return if it were to return bool false.
                return

            self.logger.info(
                f"Processing sensor reading: {reading.sensor_id}={reading.value} "
                f"at {reading.timestamp} (type: {reading.sensor_type})",
                extra={"correlation_id": correlation_id}
            )
            
            try:
                features = self._extract_features(reading)
                if features.size == 0:
                    # This could be an AgentProcessingError if feature extraction is critical and fails partially
                    self.logger.warning(
                        f"No features extracted for sensor {reading.sensor_id}, skipping event {_event_id_for_log}",
                        extra={"correlation_id": correlation_id}
                    )
                    return # Or raise AgentProcessingError if this is a hard failure
            except Exception as e: # Catch any unexpected error during feature extraction
                raise AgentProcessingError(
                    message=f"Feature extraction failed for sensor {reading.sensor_id} in event {_event_id_for_log}: {str(e)}",
                    original_exception=e
                ) from e

            # ML and Statistical processing with graceful degradation
            ml_prediction, ml_score = None, None
            stat_is_anomaly, stat_confidence, stat_desc = None, None, None
            ml_failed = False
            stat_failed = False
            
            # Try ML models first
            try:
                ml_prediction, ml_score = await self._process_ml_models(features, reading, correlation_id=correlation_id)
            except MLModelError as e:
                self.logger.error(
                    f"Isolation Forest prediction failed for {reading.sensor_id}: {e.original_exception}",
                    extra={"correlation_id": correlation_id}
                )
                ml_prediction, ml_score = 1, 0.0  # Default to "no anomaly" for ML
                ml_failed = True
            
            # Try statistical method
            try:
                stat_is_anomaly, stat_confidence, stat_desc = self._process_statistical_method(reading, correlation_id=correlation_id)
            except MLModelError as e:
                self.logger.error(
                    f"Statistical detection failed for {reading.sensor_id}: {e.original_exception}",
                    extra={"correlation_id": correlation_id}
                )
                stat_is_anomaly, stat_confidence, stat_desc = False, 0.0, "statistical_failure"
                stat_failed = True
                
            # Log graceful degradation warnings
            if ml_failed and not stat_failed:
                self.logger.warning(
                    f"ML models failed for {reading.sensor_id}, using statistical method only",
                    extra={"correlation_id": correlation_id}
                )
            elif stat_failed and not ml_failed:
                self.logger.warning(
                    f"Statistical method failed for {reading.sensor_id}, using ML method only",
                    extra={"correlation_id": correlation_id}
                )
            elif ml_failed and stat_failed:
                self.logger.error(
                    f"Both ML and statistical methods failed for {reading.sensor_id}, cannot proceed",
                    extra={"correlation_id": correlation_id}
                )
                raise MLModelError(f"All anomaly detection methods failed for {reading.sensor_id}")

            overall_is_anomaly, overall_confidence, overall_description = self._ensemble_decision(
                ml_prediction, ml_score, stat_is_anomaly, stat_confidence, stat_desc, correlation_id=correlation_id
            )
            
            self.logger.info(
                f"Final decision for {reading.sensor_id} (event {_event_id_for_log}): "
                f"anomaly={overall_is_anomaly}, confidence={overall_confidence:.4f}, "
                f"type='{overall_description}'",
                extra={"correlation_id": correlation_id}
            )
            
            if overall_is_anomaly:
                # _handle_anomaly_detected can raise WorkflowError or EventPublishError
                await self._handle_anomaly_detected(
                    reading, event, overall_confidence, overall_description, ml_score,
                    stat_is_anomaly, stat_confidence, correlation_id=correlation_id
                )
            else:
                self.logger.debug(
                    f"No anomaly detected for sensor {reading.sensor_id} (event {_event_id_for_log})",
                    extra={"correlation_id": correlation_id}
                )
            
        except (DataValidationException, MLModelError, AgentProcessingError, WorkflowError) as app_exc:
            # Re-raise application specific errors to be caught by BaseAgent.handle_event
            # Note: EventPublishError is handled gracefully in _handle_anomaly_detected, not re-raised here
            self.logger.error(
                f"Application error in AnomalyDetectionAgent.process for event {_event_id_for_log}: {app_exc}",
                exc_info=False, # exc_info=False as it's already in app_exc
                extra={"correlation_id": correlation_id}
            )
            raise
        except Exception as e:
            # Wrap unexpected errors in AgentProcessingError
            self.logger.error(
                f"Generic unhandled error in AnomalyDetectionAgent.process for event {_event_id_for_log}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise AgentProcessingError(
                message=f"Generic unhandled error processing event {_event_id_for_log}: {str(e)}",
                original_exception=e
            ) from e


    def _validate_sensor_reading(self, reading: SensorReading) -> bool:
        """Validate sensor reading. Raise DataValidationException if invalid."""
        if not reading.sensor_id or not reading.sensor_id.strip():
            raise DataValidationException("Sensor reading has empty sensor_id")
        if not isinstance(reading.value, (int, float)) or not math.isfinite(reading.value):
            raise DataValidationException(f"Sensor value '{reading.value}' is not a finite number for sensor {reading.sensor_id}")
        return True

    async def _process_ml_models(self, features: np.ndarray, reading: SensorReading, correlation_id: Optional[str] = None) -> Tuple[int, float]:
        """
        Process ML models using serverless model loading or fallback models.
        
        This method now supports two modes:
        1. Serverless mode: Dynamically loads pre-trained models from MLflow/S3
        2. Fallback mode: Uses local IsolationForest for graceful degradation
        
        Raise MLModelError on failure.
        """
        if self.use_serverless_models:
            return await self._process_serverless_ml_models(features, reading, correlation_id)
        else:
            return await self._process_fallback_ml_models(features, reading, correlation_id)
    
    async def _process_serverless_ml_models(self, features: np.ndarray, reading: SensorReading, correlation_id: Optional[str] = None) -> Tuple[int, float]:
        """
        Process ML models using serverless model loading from MLflow/S3.
        
        Args:
            features: Extracted features from sensor reading
            reading: Original sensor reading
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (prediction, score) where prediction: -1=anomaly, 1=normal
            
        Raises:
            MLModelError: If model loading or prediction fails
        """
        try:
            # Load the best model for this sensor type
            self.logger.info(
                f"Loading serverless model for sensor {reading.sensor_id} (type: {getattr(reading, 'sensor_type', 'unknown')})",
                extra={"correlation_id": correlation_id}
            )
            
            model, preprocessor = await self.model_loader.load_model_for_sensor(reading)
            
            # Prepare features for prediction
            processed_features = features
            if preprocessor is not None:
                try:
                    # Apply preprocessing if available
                    processed_features = preprocessor.transform(features.reshape(1, -1))
                    self.logger.debug(
                        f"Applied preprocessing for {reading.sensor_id}: {features.shape} -> {processed_features.shape}",
                        extra={"correlation_id": correlation_id}
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Preprocessing failed for {reading.sensor_id}, using raw features: {e}",
                        extra={"correlation_id": correlation_id}
                    )
                    processed_features = features.reshape(1, -1)
            else:
                processed_features = features.reshape(1, -1)
            
            # Make prediction using the loaded model
            try:
                # Try different prediction methods based on model type
                prediction_result = await self._predict_with_model(model, processed_features, reading, correlation_id)
                prediction, score = prediction_result
                
                self.logger.info(
                    f"Serverless ML prediction for {reading.sensor_id}: pred={prediction}, score={score:.4f}",
                    extra={"correlation_id": correlation_id}
                )
                
                return int(prediction), float(score)
                
            except Exception as e:
                raise MLModelError(
                    f"Prediction failed for {reading.sensor_id} using serverless model: {str(e)}",
                    original_exception=e
                ) from e
                
        except MLModelError:
            raise  # Re-raise MLModelError as-is
        except Exception as e:
            self.logger.error(
                f"Serverless ML processing failed for {reading.sensor_id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise MLModelError(
                f"Serverless ML processing failed for {reading.sensor_id}: {str(e)}",
                original_exception=e
            ) from e
    
    async def _predict_with_model(self, model: Any, features: np.ndarray, reading: SensorReading, correlation_id: Optional[str] = None) -> Tuple[int, float]:
        """
        Make prediction with a loaded model, handling different model types and interfaces.
        
        Args:
            model: Loaded MLflow model
            features: Processed features for prediction
            reading: Original sensor reading
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (prediction, score) where prediction: -1=anomaly, 1=normal
        """
        try:
            # Check if model has predict method (most common)
            if hasattr(model, 'predict'):
                prediction = model.predict(features)[0]
                
                # Try to get anomaly score if available
                score = 0.0
                if hasattr(model, 'decision_function'):
                    score = model.decision_function(features)[0]
                elif hasattr(model, 'score_samples'):
                    score = model.score_samples(features)[0]
                elif hasattr(model, 'predict_proba'):
                    # For classification models, use probability as score
                    proba = model.predict_proba(features)[0]
                    if len(proba) == 2:  # Binary classification
                        score = proba[1] - proba[0]  # Difference between anomaly and normal
                    else:
                        score = max(proba) - 0.5  # Confidence relative to 50%
                
                self.logger.debug(
                    f"Model prediction for {reading.sensor_id}: raw_pred={prediction}, score={score}",
                    extra={"correlation_id": correlation_id}
                )
                
                # Normalize prediction to standard format (-1=anomaly, 1=normal)
                if isinstance(prediction, (int, float)):
                    # For IsolationForest-style outputs (-1, 1)
                    normalized_prediction = -1 if prediction < 0 else 1
                elif isinstance(prediction, bool):
                    # For boolean outputs
                    normalized_prediction = -1 if prediction else 1
                elif isinstance(prediction, str):
                    # For string outputs
                    normalized_prediction = -1 if prediction.lower() in ['anomaly', 'abnormal', 'true', '1'] else 1
                else:
                    # Default fallback
                    normalized_prediction = 1
                
                return normalized_prediction, score
                
            # Fallback for MLflow pyfunc models
            elif hasattr(model, '_model_impl'):
                # Try to access the underlying model
                underlying_model = model._model_impl
                if hasattr(underlying_model, 'predict'):
                    return await self._predict_with_model(underlying_model, features, reading, correlation_id)
            
            # If no suitable prediction method found
            raise MLModelError(f"Model does not have a suitable prediction method")
            
        except Exception as e:
            self.logger.error(
                f"Prediction error for {reading.sensor_id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise MLModelError(f"Model prediction failed: {str(e)}", original_exception=e) from e
    
    async def _process_fallback_ml_models(self, features: np.ndarray, reading: SensorReading, correlation_id: Optional[str] = None) -> Tuple[int, float]:
        """
        Process ML models using the original local IsolationForest approach.
        This is the fallback method when serverless models are disabled or unavailable.
        
        Raise MLModelError on failure.
        """
        try:
            if not self.isolation_forest or not self.scaler:
                raise MLModelError("Fallback models not properly initialized")
                
            scaled_features = self.scaler.fit_transform(features) # fit_transform might be an issue if only predicting one sample
            if not self.isolation_forest_fitted:
                self.logger.info(
                    f"Fitting Isolation Forest model on initial data for sensor {reading.sensor_id}",
                    extra={"correlation_id": correlation_id}
                )
                self.isolation_forest.fit(scaled_features) # Should ideally be fit on a larger dataset, not single instances
                self.isolation_forest_fitted = True
            
            if_prediction = self.isolation_forest.predict(scaled_features)[0]
            if_score = self.isolation_forest.decision_function(scaled_features)[0]
            self.logger.info(
                f"Fallback Isolation Forest for {reading.sensor_id}: pred={if_prediction}, score={if_score:.4f}",
                extra={"correlation_id": correlation_id}
            )
            return int(if_prediction), float(if_score)
        except Exception as e:
            self.logger.error(
                f"Fallback ML model processing failed for {reading.sensor_id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise MLModelError(
                message=f"Fallback Isolation Forest prediction failed for {reading.sensor_id}: {str(e)}",
                original_exception=e
            ) from e

    def _process_statistical_method(self, reading: SensorReading, correlation_id: Optional[str] = None) -> Tuple[bool, float, str]:
        """Process statistical method. Raise MLModelError on failure (as it's part of the 'model')."""
        try:
            sensor_id = reading.sensor_id
            if sensor_id in self.historical_data_store:
                hist_data = self.historical_data_store[sensor_id]
                hist_mean, hist_std = hist_data["mean"], hist_data["std"]
            elif sensor_id in self.unknown_sensor_baselines:
                baseline_data = self.unknown_sensor_baselines[sensor_id]
                hist_mean, hist_std = baseline_data["mean"], baseline_data["std"]
            else:
                hist_mean, hist_std = reading.value, self.default_historical_std
                self.unknown_sensor_baselines[sensor_id] = {"mean": hist_mean, "std": hist_std}
                self.logger.info(
                    f"First encounter for {sensor_id}, baseline: mean={hist_mean:.4f}, std={hist_std:.4f}",
                    extra={"correlation_id": correlation_id}
                )
            
            stat_is_anomaly, stat_confidence, stat_desc = self.statistical_detector.detect(
                reading.value, hist_mean, hist_std
            )
            self.logger.info(
                f"Statistical for {reading.sensor_id}: anom={stat_is_anomaly}, conf={stat_confidence:.4f}, desc='{stat_desc}'",
                extra={"correlation_id": correlation_id}
            )
            return stat_is_anomaly, stat_confidence, stat_desc
        except ValueError as ve: # Specific error from statistical_detector
            self.logger.error(
                f"Statistical detection validation error for {reading.sensor_id}: {ve}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise MLModelError(f"Statistical method validation error for {reading.sensor_id}: {str(ve)}", original_exception=ve) from ve
        except Exception as e:
            self.logger.error(
                f"Statistical processing failed for {reading.sensor_id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise MLModelError(f"Statistical method failed for {reading.sensor_id}: {str(e)}", original_exception=e) from e

    async def _handle_anomaly_detected(
        self, reading: SensorReading, event: DataProcessedEvent,
        overall_confidence: float, overall_description: str, if_score: float,
        stat_is_anomaly: bool, stat_confidence: float, correlation_id: Optional[str] = None
    ) -> None:
        """Handle anomaly detection. Raise WorkflowError or EventPublishError on failure."""
        _event_id_for_log = getattr(event, 'event_id', 'N/A')
        try:
            severity = 1
            if overall_confidence > 0.8: severity = 5
            elif overall_confidence > 0.6: severity = 4
            elif overall_confidence > 0.4: severity = 3
            elif overall_confidence > 0.2: severity = 2
            
            evidence = {
                "raw_value": float(reading.value), "if_score": float(if_score),
                "stat_is_anomaly": bool(stat_is_anomaly), "stat_confidence": float(stat_confidence),
                "sensor_type": str(reading.sensor_type or "unknown"),
                "timestamp": reading.timestamp.isoformat() if reading.timestamp else None,
                "processing_agent": self.agent_id
            }
            
            try:
                anomaly_alert = AnomalyAlert(
                    sensor_id=reading.sensor_id, anomaly_type=overall_description, severity=severity,
                    confidence=overall_confidence,
                    description=f"Anomaly: {reading.sensor_id} ({reading.sensor_type}). Value: {reading.value:.4f}.",
                    evidence=evidence, created_at=datetime.utcnow()
                )
            except ValidationError as ve:
                raise DataValidationException( # Or WorkflowError if this is considered part of a workflow step
                    message=f"Failed to create AnomalyAlert for event {_event_id_for_log}: {ve}",
                    errors=ve.errors(), original_exception=ve
                ) from ve

            severity_map = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "very_low"}
            anomaly_detected_event = AnomalyDetectedEvent(
                anomaly_details=anomaly_alert.model_dump(), triggering_data=reading.model_dump(),
                severity=severity_map.get(severity, "medium"), correlation_id=event.correlation_id
            )
            
            try:
                await self._publish_anomaly_event(anomaly_detected_event, correlation_id=correlation_id) # Can raise EventPublishError
            except EventPublishError as epe:
                # For event publishing errors, log but don't propagate - allow graceful degradation
                self.logger.error(
                    f"Failed to create or publish AnomalyDetectedEvent for {_event_id_for_log}: {epe}",
                    exc_info=False,
                    extra={"correlation_id": correlation_id}
                )
                # Don't raise - continue gracefully

        except (DataValidationException) as app_exc: # Catch specific ones first (removed EventPublishError since we handle it above)
            self.logger.error(
                f"Error in anomaly handling for event {_event_id_for_log}: {app_exc}",
                exc_info=False,
                extra={"correlation_id": correlation_id}
            )
            raise
        except Exception as e: # Catch any other error during this handling phase
            self.logger.error(
                f"Generic error in _handle_anomaly_detected for event {_event_id_for_log}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise WorkflowError(
                message=f"Failed to handle detected anomaly for event {_event_id_for_log}: {str(e)}",
                original_exception=e
            ) from e

    async def _publish_anomaly_event(self, event: AnomalyDetectedEvent, correlation_id: Optional[str] = None) -> None:
        """
        Publish an AnomalyDetectedEvent to the event bus with a retry mechanism.

        This enhances reliability by attempting to resend the event in case of
        transient failures during publishing.
        """
        import asyncio
        
        _event_id_for_log = getattr(event, 'event_id', 'N/A')
        # Configuration for retry mechanism
        max_retries = 3  # Total number of attempts (1 initial + 2 retries)
        retry_delay = 0.1  # Delay in seconds between retries (e.g., 100ms)
        # A more sophisticated strategy might use exponential backoff.
        
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Publishing AnomalyDetectedEvent (attempt {attempt + 1}/{max_retries}) for {_event_id_for_log}",
                    extra={"correlation_id": correlation_id}
                )
                await self.event_bus.publish(event)
                self.logger.debug(
                    f"Successfully published AnomalyDetectedEvent: {_event_id_for_log}",
                    extra={"correlation_id": correlation_id}
                )
                return # Successfully published, exit the loop
            except Exception as e:
                self.logger.warning(
                    f"Publish attempt {attempt + 1}/{max_retries} failed for AnomalyDetectedEvent {_event_id_for_log}: {e}",
                    extra={"correlation_id": correlation_id}
                )
                if attempt < max_retries - 1:
                    # If not the last attempt, wait before retrying
                    await asyncio.sleep(retry_delay)
                else:
                    # Last attempt failed, log error and raise EventPublishError
                    self.logger.error(
                        f"Failed to publish AnomalyDetectedEvent after {max_retries} attempts for {_event_id_for_log}: {e}",
                        extra={"correlation_id": correlation_id}
                    )
                    # This error will be caught by the calling method (_handle_anomaly_detected)
                    # which then decides whether to allow graceful degradation or propagate further.
                    raise EventPublishError(
                        message=f"Failed to publish AnomalyDetectedEvent {_event_id_for_log} via event bus after {max_retries} attempts: {e}",
                        original_exception=e
                    ) from e

    def _calculate_ensemble_metrics(
        self, if_prediction: int, if_score: float,
        stat_is_anomaly: bool, stat_confidence: float, stat_desc: str
    ) -> Tuple[bool, float, Union[AnomalyType, str]]:
        """
        Calculates the overall anomaly status, confidence, and description based on
        Isolation Forest (IF) and statistical method outputs.

        Args:
            if_prediction: Prediction from Isolation Forest (-1 for anomaly, 1 for normal).
            if_score: Anomaly score from Isolation Forest.
            stat_is_anomaly: Boolean indicating if statistical method found an anomaly.
            stat_confidence: Confidence score from the statistical method.
            stat_desc: Description from the statistical method (e.g., "z_score_violation").

        Returns:
            A tuple containing:
                - bool: True if an overall anomaly is detected, False otherwise.
                - float: The final confidence score (0.0 to 1.0).
                - Union[AnomalyType, str]: The final anomaly description, using AnomalyType enum
                  where possible, or "normal" if no anomaly.
        """
        is_anomaly = (if_prediction == -1) or stat_is_anomaly
        if if_prediction == -1:
            # Normalize IF score: typical scores are <=0 for anomalies.
            # We want higher confidence for scores further from 0.
            # A simple approach: 0.5 base + adjustment. More negative scores -> higher confidence.
            # This normalization depends on the typical range of if_score for anomalies.
            # Assuming if_score for anomalies is often between -0.5 and 0.
            # And for normal points, it's > 0.
            # Let's try to map it to [0.5, 1.0] for anomalies.
            normalized_score = max(-1.0, min(0.0, if_score)) # Cap score for safety
            if_confidence = 0.5 + (abs(normalized_score) * 0.5) # e.g. if_score -0.2 -> 0.5 + 0.1 = 0.6; if_score -0.5 -> 0.5 + 0.25 = 0.75
            if_confidence = max(0.5, min(1.0, if_confidence)) # Ensure it's within a sensible range for anomaly confidence
        else: # Not an IF anomaly
            if_confidence = 0.1 # Low confidence if IF doesn't flag it

        final_confidence_score = 0.0
        if if_prediction == -1 and stat_is_anomaly: # Both agree
            final_confidence_score = (0.6 * if_confidence + 0.4 * stat_confidence)
        elif if_prediction == -1: # Only IF anomaly
            final_confidence_score = if_confidence * 0.8
        elif stat_is_anomaly: # Only statistical anomaly
            final_confidence_score = stat_confidence * 0.8
        
        final_confidence_score = max(0.0, min(1.0, final_confidence_score)) # Clamp to [0,1]

        final_anomaly_description: Union[AnomalyType, str] = AnomalyType.UNKNOWN
        if not is_anomaly:
            final_anomaly_description = "normal"
        elif if_prediction == -1 and stat_is_anomaly:
            if "z_score" in stat_desc:
                final_anomaly_description = AnomalyType.ENSEMBLE_IF_STATISTICAL
            elif "threshold" in stat_desc:
                final_anomaly_description = AnomalyType.ENSEMBLE_IF_STATISTICAL
            else:
                final_anomaly_description = AnomalyType.ENSEMBLE_IF_STATISTICAL
        elif if_prediction == -1:
            final_anomaly_description = AnomalyType.ISOLATION_FOREST
        elif stat_is_anomaly:
            if "z_score" in stat_desc:
                final_anomaly_description = AnomalyType.STATISTICAL_Z_SCORE
            elif "threshold" in stat_desc:
                final_anomaly_description = AnomalyType.STATISTICAL_THRESHOLD
            else:
                final_anomaly_description = AnomalyType.UNKNOWN

        return is_anomaly, final_confidence_score, final_anomaly_description

    def _ensemble_decision(
        self, if_prediction: int, if_score: float,
        stat_is_anomaly: bool, stat_confidence: float, stat_desc: str, correlation_id: Optional[str] = None
    ) -> Tuple[bool, float, Union[AnomalyType, str]]:
        """
        Determines overall anomaly status by combining Isolation Forest and statistical results.
        Logs the ensemble decision details.
        """
        is_anomaly, final_confidence_score, final_anomaly_description = self._calculate_ensemble_metrics(
            if_prediction, if_score, stat_is_anomaly, stat_confidence, stat_desc
        )

        # Determine IF confidence for logging, even if not used directly in final_confidence_score when stat_is_anomaly is false
        if if_prediction == -1:
            normalized_score = max(-1.0, min(0.0, if_score))
            log_if_confidence = 0.5 + (abs(normalized_score) * 0.5)
            log_if_confidence = max(0.5, min(1.0, log_if_confidence))
        else:
            log_if_confidence = 0.1

        self.logger.debug(
            f"Ensemble: if_pred={if_prediction}, if_score={if_score:.4f}, if_conf={log_if_confidence:.4f}, "
            f"stat_anom={stat_is_anomaly}, stat_conf={stat_confidence:.4f} -> "
            f"final_anom={is_anomaly}, final_conf={final_confidence_score:.4f}, desc='{final_anomaly_description}'",
            extra={"correlation_id": correlation_id}
        )
        return is_anomaly, final_confidence_score, final_anomaly_description

    async def get_model_stats(self) -> Dict[str, Any]:
        """
        Get model loading and usage statistics.
        
        Returns:
            Dictionary containing model loader statistics and agent metrics
        """
        stats = {
            'agent_id': self.agent_id,
            'serverless_mode': self.use_serverless_models,
            'fallback_fitted': getattr(self, 'isolation_forest_fitted', False)
        }
        
        if self.use_serverless_models and self.model_loader:
            loader_stats = self.model_loader.get_stats()
            stats.update({
                'model_loader': loader_stats,
                'cache_efficiency': f"{loader_stats.get('cache_hit_rate', 0):.1f}%"
            })
        
        return stats
    
    async def clear_model_cache(self) -> None:
        """Clear the model cache to force reloading of models."""
        if self.use_serverless_models and self.model_loader:
            self.model_loader.clear_cache()
            self.logger.info("Model cache cleared")
    
    async def list_available_models(self, sensor_type: Optional[str] = None) -> List[str]:
        """
        List available models for the given sensor type.
        
        Args:
            sensor_type: Optional sensor type filter
            
        Returns:
            List of available model names
        """
        if self.use_serverless_models and self.model_loader:
            return await self.model_loader.list_available_models(sensor_type)
        else:
            return ['isolation_forest_fallback']

    async def detect_anomaly(self, sensor_reading: SensorReading) -> Optional[AnomalyAlert]:
        """
        Public method to detect anomalies in a sensor reading.
        
        This method provides a direct interface for anomaly detection testing
        and can be used independently of the event-driven workflow.
        
        Args:
            sensor_reading: The sensor reading to analyze
            
        Returns:
            AnomalyAlert if an anomaly is detected, None otherwise
        """
        try:
            correlation_id = f"direct_detection_{sensor_reading.sensor_id}_{int(datetime.utcnow().timestamp())}"
            
            # Create features for ML models 
            features = np.array([[
                sensor_reading.value,
                sensor_reading.quality,
                hash(sensor_reading.sensor_id) % 1000,  # Sensor hash feature
                1.0 if sensor_reading.unit else 0.0,    # Has unit feature
            ]])
            
            # Process with ML models to get anomaly prediction
            is_anomaly, confidence = await self._process_ml_models(features, sensor_reading, correlation_id)
            
            if is_anomaly:
                # Create anomaly alert
                anomaly_alert = AnomalyAlert(
                    sensor_id=sensor_reading.sensor_id,
                    anomaly_type="isolation_forest_anomaly",  # Valid enum value
                    severity=min(5, max(1, int(confidence * 5) + 1)),  # Convert confidence to severity 1-5
                    confidence=confidence,
                    description=f"Anomaly detected in {sensor_reading.sensor_type} sensor with confidence {confidence:.2f}",
                    evidence={
                        "sensor_value": sensor_reading.value,
                        "sensor_unit": sensor_reading.unit,
                        "quality_score": sensor_reading.quality,
                        "detection_method": "serverless_ml" if self.use_serverless_models else "fallback_ml"
                    },
                    recommended_actions=[
                        "Investigate sensor reading",
                        "Check equipment status",
                        "Verify sensor calibration"
                    ]
                )
                
                self.logger.info(
                    f"Anomaly detected via direct detection: {sensor_reading.sensor_id} "
                    f"confidence={confidence:.2f}",
                    extra={"correlation_id": correlation_id}
                )
                
                return anomaly_alert
            else:
                self.logger.debug(
                    f"No anomaly detected via direct detection: {sensor_reading.sensor_id} "
                    f"confidence={confidence:.2f}",
                    extra={"correlation_id": correlation_id}
                )
                return None
                
        except Exception as e:
            self.logger.error(
                f"Error in direct anomaly detection for {sensor_reading.sensor_id}: {e}",
                exc_info=True
            )
            return None
