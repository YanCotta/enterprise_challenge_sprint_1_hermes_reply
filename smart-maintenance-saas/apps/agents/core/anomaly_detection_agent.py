"""Anomaly detection agent for processing sensor data and detecting anomalies."""

import asyncio
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
import traceback

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from pydantic import ValidationError

from apps.agents.base_agent import AgentCapability, BaseAgent
from apps.ml.statistical_models import StatisticalAnomalyDetector
from core.events.event_bus import EventBus
from core.events.event_models import AnomalyDetectedEvent, DataProcessedEvent
from data.schemas import AnomalyAlert, SensorReading
from data.exceptions import (
    MLModelError, ConfigurationError, DataValidationException,
    AgentProcessingError, WorkflowError, EventPublishError, SmartMaintenanceBaseException
)


class AnomalyDetectionAgent(BaseAgent):
    """
    Agent responsible for detecting anomalies in processed sensor data using ML models.
    
    Uses both statistical methods and machine learning models (Isolation Forest)
    to identify unusual patterns in sensor readings.
    """

    def __init__(self, agent_id: str, event_bus: EventBus, specific_settings: Optional[dict] = None):
        """
        Initialize the AnomalyDetectionAgent.
        """
        if not agent_id or not agent_id.strip():
            # This is a programming error, ValueError is fine.
            raise ValueError("agent_id cannot be empty")
        if event_bus is None:
            raise ValueError("event_bus cannot be None")
            
        super().__init__(agent_id, event_bus)
        
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        settings = specific_settings or {}
        
        try:
            self.scaler = StandardScaler()
            if_params = settings.get('isolation_forest_params', {})
            default_if_params = {
                'contamination': 'auto', 'random_state': 42, 'n_estimators': 100,
                'max_samples': 'auto', 'max_features': 1.0
            }
            final_if_params = {**default_if_params, **if_params}
            self.isolation_forest = IsolationForest(**final_if_params)
            self.isolation_forest_fitted = False
            
            stat_config = settings.get('statistical_detector_config', {})
            self.statistical_detector = StatisticalAnomalyDetector(config=stat_config)
            
            self.default_historical_std = settings.get('default_historical_std', 0.1)
            if self.default_historical_std <= 0:
                raise ConfigurationError("default_historical_std must be positive")

        except ConfigurationError as ce: # Catch our specific config error first
            self.logger.error(f"Configuration error during AnomalyDetectionAgent init: {ce}", exc_info=True)
            raise # Re-raise as it's a startup issue
        except Exception as e:
            self.logger.error(f"Failed to initialize ML models or settings: {e}", exc_info=True)
            # Wrap generic exception as MLModelError or ConfigurationError depending on context
            # For this example, assuming it's more related to model setup if not ConfigurationError
            raise MLModelError(f"Failed to initialize ML models: {e}", original_exception=e) from e
        
        self.unknown_sensor_baselines: Dict[str, Dict[str, float]] = {}
        self.historical_data_store: Dict[str, Dict[str, float]] = {
            "sensor_temp_001": {"mean": 22.5, "std": 2.1},
            "sensor_vibr_001": {"mean": 0.05, "std": 0.02},
        }
        self._validate_historical_data() # Can raise ConfigurationError
        
        self.logger.info(
            f"AnomalyDetectionAgent initialized with ID: {self.agent_id}"
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
                 self.logger.warning(f"Zero standard deviation for sensor {sensor_id} in historical data.")


    async def register_capabilities(self) -> None:
        capability = AgentCapability(
            name="detect_anomalies",
            description="Detects anomalies in processed sensor data using ML models.",
            input_types=[DataProcessedEvent.__name__],
            output_types=[AnomalyDetectedEvent.__name__]
        )
        self.capabilities.append(capability)
        self.logger.debug(f"Agent {self.agent_id} registered capability: {capability.name}")

    async def start(self) -> None:
        await super().start()
        await self.event_bus.subscribe(DataProcessedEvent.__name__, self.process)
        self.logger.info(f"Agent {self.agent_id} subscribed to {DataProcessedEvent.__name__}.")

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
        self.logger.debug(f"Received event: {_event_id_for_log} with correlation_id: {getattr(event, 'correlation_id', 'N/A')}")

        if not isinstance(event, DataProcessedEvent):
            # This should ideally not happen if event bus and subscriptions are correct
            self.logger.error(f"Expected DataProcessedEvent, got {type(event)}. This is a programming error.")
            # Not raising custom error as it's more of an assertion/guard
            return
            
        try:
            if not event.processed_data or not isinstance(event.processed_data, dict):
                # Raise DataValidationException for bad input structure
                raise DataValidationException("Event contains empty or malformed processed_data.")

            try:
                reading = SensorReading(**event.processed_data)
            except ValidationError as ve:
                self.logger.error(f"Failed to parse sensor reading for event {_event_id_for_log}: {ve}", exc_info=True)
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
                f"at {reading.timestamp} (type: {reading.sensor_type})"
            )
            
            try:
                features = self._extract_features(reading)
                if features.size == 0:
                    # This could be an AgentProcessingError if feature extraction is critical and fails partially
                    self.logger.warning(f"No features extracted for sensor {reading.sensor_id}, skipping event {_event_id_for_log}")
                    return # Or raise AgentProcessingError if this is a hard failure
            except Exception as e: # Catch any unexpected error during feature extraction
                raise AgentProcessingError(
                    message=f"Feature extraction failed for sensor {reading.sensor_id} in event {_event_id_for_log}: {str(e)}",
                    original_exception=e
                ) from e

            # ML and Statistical processing will raise MLModelError if they fail internally
            ml_prediction, ml_score = await self._process_ml_models(features, reading)
            stat_is_anomaly, stat_confidence, stat_desc = self._process_statistical_method(reading)

            overall_is_anomaly, overall_confidence, overall_description = self._ensemble_decision(
                ml_prediction, ml_score, stat_is_anomaly, stat_confidence, stat_desc
            )
            
            self.logger.info(
                f"Final decision for {reading.sensor_id} (event {_event_id_for_log}): "
                f"anomaly={overall_is_anomaly}, confidence={overall_confidence:.4f}, "
                f"type='{overall_description}'"
            )
            
            if overall_is_anomaly:
                # _handle_anomaly_detected can raise WorkflowError or EventPublishError
                await self._handle_anomaly_detected(
                    reading, event, overall_confidence, overall_description, ml_score,
                    stat_is_anomaly, stat_confidence
                )
            else:
                self.logger.debug(f"No anomaly detected for sensor {reading.sensor_id} (event {_event_id_for_log})")
            
        except (DataValidationException, MLModelError, AgentProcessingError, WorkflowError, EventPublishError) as app_exc:
            # Re-raise application specific errors to be caught by BaseAgent.handle_event
            self.logger.error(f"Application error in AnomalyDetectionAgent.process for event {_event_id_for_log}: {app_exc}", exc_info=False) # exc_info=False as it's already in app_exc
            raise
        except Exception as e:
            # Wrap unexpected errors in AgentProcessingError
            self.logger.error(f"Generic unhandled error in AnomalyDetectionAgent.process for event {_event_id_for_log}: {e}", exc_info=True)
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

    async def _process_ml_models(self, features: np.ndarray, reading: SensorReading) -> Tuple[int, float]:
        """Process ML models. Raise MLModelError on failure."""
        try:
            scaled_features = self.scaler.fit_transform(features) # fit_transform might be an issue if only predicting one sample
            if not self.isolation_forest_fitted:
                self.logger.info(f"Fitting Isolation Forest model on initial data for sensor {reading.sensor_id}")
                self.isolation_forest.fit(scaled_features) # Should ideally be fit on a larger dataset, not single instances
                self.isolation_forest_fitted = True
            
            if_prediction = self.isolation_forest.predict(scaled_features)[0]
            if_score = self.isolation_forest.decision_function(scaled_features)[0]
            self.logger.info(
                f"Isolation Forest for {reading.sensor_id}: pred={if_prediction}, score={if_score:.4f}"
            )
            return int(if_prediction), float(if_score)
        except Exception as e:
            self.logger.error(f"ML model processing failed for {reading.sensor_id}: {e}", exc_info=True)
            raise MLModelError(
                message=f"Isolation Forest prediction failed for {reading.sensor_id}: {str(e)}",
                original_exception=e
            ) from e

    def _process_statistical_method(self, reading: SensorReading) -> Tuple[bool, float, str]:
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
                self.logger.info(f"First encounter for {sensor_id}, baseline: mean={hist_mean:.4f}, std={hist_std:.4f}")
            
            stat_is_anomaly, stat_confidence, stat_desc = self.statistical_detector.detect(
                reading.value, hist_mean, hist_std
            )
            self.logger.info(
                f"Statistical for {reading.sensor_id}: anom={stat_is_anomaly}, conf={stat_confidence:.4f}, desc='{stat_desc}'"
            )
            return stat_is_anomaly, stat_confidence, stat_desc
        except ValueError as ve: # Specific error from statistical_detector
            self.logger.error(f"Statistical detection validation error for {reading.sensor_id}: {ve}", exc_info=True)
            raise MLModelError(f"Statistical method validation error for {reading.sensor_id}: {str(ve)}", original_exception=ve) from ve
        except Exception as e:
            self.logger.error(f"Statistical processing failed for {reading.sensor_id}: {e}", exc_info=True)
            raise MLModelError(f"Statistical method failed for {reading.sensor_id}: {str(e)}", original_exception=e) from e

    async def _handle_anomaly_detected(
        self, reading: SensorReading, event: DataProcessedEvent,
        overall_confidence: float, overall_description: str, if_score: float,
        stat_is_anomaly: bool, stat_confidence: float
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
            
            await self._publish_anomaly_event(anomaly_detected_event) # Can raise EventPublishError

        except (DataValidationException, EventPublishError) as app_exc: # Catch specific ones first
            self.logger.error(f"Error in anomaly handling for event {_event_id_for_log}: {app_exc}", exc_info=False)
            raise
        except Exception as e: # Catch any other error during this handling phase
            self.logger.error(f"Generic error in _handle_anomaly_detected for event {_event_id_for_log}: {e}", exc_info=True)
            raise WorkflowError(
                message=f"Failed to handle detected anomaly for event {_event_id_for_log}: {str(e)}",
                original_exception=e
            ) from e

    async def _publish_anomaly_event(self, event: AnomalyDetectedEvent) -> None:
        """Publish anomaly event. Raise EventPublishError on failure after retries."""
        # This method now directly calls event_bus.publish. The event_bus.publish method
        # itself has retry and DLQ logic. So, this method might just need to call it once.
        # If event_bus.publish raises an error (e.g., EventPublishError after its retries),
        # it will propagate up.
        _event_id_for_log = getattr(event, 'event_id', 'N/A')
        try:
            self.logger.info(f"Publishing AnomalyDetectedEvent: {_event_id_for_log}")
            await self.event_bus.publish(event) # EventBus handles retries & DLQ
            self.logger.debug(f"Successfully initiated publishing of AnomalyDetectedEvent: {_event_id_for_log}")
        except Exception as e: # Assuming event_bus.publish could raise its own specific errors or a generic one
            self.logger.error(f"Publishing AnomalyDetectedEvent {_event_id_for_log} failed: {e}", exc_info=True)
            # Wrap it as EventPublishError, as the source of error is publishing.
            # This assumes event_bus.publish might not *always* raise EventPublishError itself.
            # If it does, this wrapping is redundant.
            raise EventPublishError(
                message=f"Failed to publish AnomalyDetectedEvent {_event_id_for_log} via event bus: {str(e)}",
                original_exception=e
            ) from e
    
    def _ensemble_decision(
        self, if_prediction: int, if_score: float,
        stat_is_anomaly: bool, stat_confidence: float, stat_desc: str
    ) -> Tuple[bool, float, str]:
        # This method's logic is mostly decision-making, less prone to external exceptions
        # unless there are numerical issues, which should be caught by the caller if severe.
        is_anomaly = (if_prediction == -1) or stat_is_anomaly
        if if_prediction == -1:
            normalized_score = max(-1.0, min(1.0, if_score))
            if_confidence = 0.5 + 0.5 * (1.0 - normalized_score) / 2.0
            if_confidence = max(0.5, min(1.0, if_confidence))
        else:
            if_confidence = 0.1
        
        final_confidence_score = 0.0
        if if_prediction == -1 and stat_is_anomaly:
            final_confidence_score = (0.6 * if_confidence + 0.4 * stat_confidence)
        elif if_prediction == -1:
            final_confidence_score = if_confidence * 0.8
        elif stat_is_anomaly:
            final_confidence_score = stat_confidence * 0.8
        
        final_confidence_score = max(0.0, min(1.0, final_confidence_score))
        
        final_anomaly_description = "normal"
        if if_prediction == -1 and stat_is_anomaly:
            final_anomaly_description = f"ensemble_anomaly_if_and_{stat_desc}"
        elif if_prediction == -1:
            final_anomaly_description = "isolation_forest_anomaly"
        elif stat_is_anomaly:
            final_anomaly_description = f"statistical_{stat_desc}"

        self.logger.debug(
            f"Ensemble: if_pred={if_prediction}, if_score={if_score:.4f}, if_conf={if_confidence:.4f}, "
            f"stat_anom={stat_is_anomaly}, stat_conf={stat_confidence:.4f} -> "
            f"final_anom={is_anomaly}, final_conf={final_confidence_score:.4f}, desc='{final_anomaly_description}'"
        )
        return is_anomaly, final_confidence_score, final_anomaly_description
