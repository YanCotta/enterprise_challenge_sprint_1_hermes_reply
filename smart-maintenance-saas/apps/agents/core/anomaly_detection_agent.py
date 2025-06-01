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


class AnomalyDetectionAgent(BaseAgent):
    """
    Agent responsible for detecting anomalies in processed sensor data using ML models.
    
    Uses both statistical methods and machine learning models (Isolation Forest)
    to identify unusual patterns in sensor readings.
    """

    def __init__(self, agent_id: str, event_bus: EventBus, specific_settings: Optional[dict] = None):
        """
        Initialize the AnomalyDetectionAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            event_bus: EventBus instance for event communication
            specific_settings: Optional dictionary of agent-specific settings
                Supported keys:
                - isolation_forest_params: Dict of IsolationForest parameters
                - statistical_detector_config: Dict of StatisticalAnomalyDetector config
                - default_historical_std: Default std for unknown sensors (default: 0.1)
        
        Raises:
            ValueError: If agent_id is empty or event_bus is None
        """
        if not agent_id or not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        if event_bus is None:
            raise ValueError("event_bus cannot be None")
            
        super().__init__(agent_id, event_bus)
        
        # Process specific settings
        settings = specific_settings or {}
        
        # Initialize ML models with better parameter validation
        try:
            self.scaler = StandardScaler()
            
            # Configurable Isolation Forest parameters
            if_params = settings.get('isolation_forest_params', {})
            default_if_params = {
                'contamination': 'auto',
                'random_state': 42,
                'n_estimators': 100,
                'max_samples': 'auto',
                'max_features': 1.0
            }
            # Merge user params with defaults
            final_if_params = {**default_if_params, **if_params}
            
            self.isolation_forest = IsolationForest(**final_if_params)
            self.isolation_forest_fitted = False
            
            # Initialize statistical detector with configuration
            stat_config = settings.get('statistical_detector_config', {})
            self.statistical_detector = StatisticalAnomalyDetector(config=stat_config)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ML models: {e}")
            raise
        
        # Configuration for unknown sensors
        self.default_historical_std = settings.get('default_historical_std', 0.1)
        if self.default_historical_std <= 0:
            raise ValueError("default_historical_std must be positive")
        
        self.unknown_sensor_baselines: Dict[str, Dict[str, float]] = {} # For caching first reading of unknown sensors

        # Enhanced historical data store with validation
        self.historical_data_store: Dict[str, Dict[str, float]] = {
            "sensor_temp_001": {"mean": 22.5, "std": 2.1},
            "sensor_temp_002": {"mean": 24.8, "std": 1.8},
            "sensor_vibr_001": {"mean": 0.05, "std": 0.02},
            "sensor_vibr_002": {"mean": 0.03, "std": 0.015},
            "sensor_press_001": {"mean": 101.3, "std": 0.8},
            "sensor_press_002": {"mean": 98.7, "std": 1.2},
        }
        
        # Validate historical data
        self._validate_historical_data()
        
        # Initialize logger with structured context
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        self.logger.info(
            f"AnomalyDetectionAgent initialized with ID: {self.agent_id}, "
            f"IF params: {final_if_params}, "
            f"Historical sensors: {len(self.historical_data_store)}"
        )

    def _validate_historical_data(self) -> None:
        """Validate the historical data store for consistency."""
        for sensor_id, data in self.historical_data_store.items():
            if not isinstance(data, dict):
                raise ValueError(f"Historical data for {sensor_id} must be a dictionary")
            if 'mean' not in data or 'std' not in data:
                raise ValueError(f"Historical data for {sensor_id} must contain 'mean' and 'std'")
            if not isinstance(data['mean'], (int, float)) or not isinstance(data['std'], (int, float)):
                raise ValueError(f"Mean and std for {sensor_id} must be numeric")
            if data['std'] < 0:
                raise ValueError(f"Standard deviation for {sensor_id} cannot be negative")
            # Log warning for suspicious data
            if data['std'] == 0:
                self.logger.warning(f"Zero standard deviation for sensor {sensor_id}")

    async def register_capabilities(self) -> None:
        """Register the agent's capabilities."""
        capability = AgentCapability(
            name="detect_anomalies",
            description="Detects anomalies in processed sensor data using ML models.",
            input_types=[DataProcessedEvent.__name__],
            output_types=[AnomalyDetectedEvent.__name__]
        )
        self.capabilities.append(capability)
        self.logger.debug(f"Agent {self.agent_id} registered capability: {capability.name}")

    async def start(self) -> None:
        """Start the agent and subscribe to relevant events."""
        await super().start()
        
        # Subscribe to DataProcessedEvent
        await self.event_bus.subscribe(
            DataProcessedEvent.__name__,
            self.process
        )
        self.logger.info(f"Agent {self.agent_id} subscribed to {DataProcessedEvent.__name__}.")

    def _extract_features(self, reading: SensorReading) -> np.ndarray:
        """
        Extract features from a sensor reading for ML model input.
        
        Args:
            reading: SensorReading object to extract features from
            
        Returns:
            2D NumPy array suitable for scikit-learn models
        """
        # For now, just use the reading value as a single feature
        features = np.array([[reading.value]])
        
        self.logger.debug(
            f"Extracted features for sensor {reading.sensor_id}: {features.flatten()}"
        )
        
        return features

    async def process(self, event: DataProcessedEvent) -> None:
        """
        Process a DataProcessedEvent to detect anomalies.
        
        Args:
            event: DataProcessedEvent containing processed sensor data
            
        Raises:
            ValidationError: If event data is malformed
            ValueError: If sensor data is invalid
        """
        if not isinstance(event, DataProcessedEvent):
            self.logger.error(f"Expected DataProcessedEvent, got {type(event)}")
            return
            
        self.logger.debug(f"Received event: {event.event_id} with correlation_id: {event.correlation_id}")
        
        try:
            # Robust data parsing with comprehensive error handling
            if not event.processed_data:
                self.logger.warning("Event contains empty processed_data, skipping")
                return
                
            if not isinstance(event.processed_data, dict):
                self.logger.error(f"processed_data must be a dictionary, got {type(event.processed_data)}")
                return
            
            # Parse with Pydantic validation
            try:
                reading = SensorReading(**event.processed_data)
            except ValidationError as e:
                self.logger.error(f"Failed to parse sensor reading: {e}")
                # Log the problematic data for debugging
                self.logger.debug(f"Problematic data: {event.processed_data}")
                return
            except Exception as e:
                self.logger.error(f"Unexpected error parsing sensor reading: {e}")
                return
            
            # Validate sensor reading data
            if not self._validate_sensor_reading(reading):
                return
            
            self.logger.info(
                f"Processing sensor reading: {reading.sensor_id}={reading.value} "
                f"at {reading.timestamp} (type: {reading.sensor_type})"
            )
            
            # Extract and validate features
            try:
                features = self._extract_features(reading)
                if features.size == 0:
                    self.logger.warning(f"No features extracted for sensor {reading.sensor_id}, skipping")
                    return
            except Exception as e:
                self.logger.error(f"Feature extraction failed for {reading.sensor_id}: {e}")
                return
            
            # ML Model Processing with enhanced error handling
            try:
                ml_results = await self._process_ml_models(features, reading)
                if ml_results is None:
                    return
                    
                if_prediction, if_score = ml_results
            except Exception as e:
                self.logger.error(f"ML model processing failed for {reading.sensor_id}: {e}", exc_info=True)
                return
            
            # Statistical Method Processing
            try:
                stat_results = self._process_statistical_method(reading)
                if stat_results is None:
                    return
                    
                stat_is_anomaly, stat_confidence, stat_desc = stat_results
            except Exception as e:
                self.logger.error(f"Statistical processing failed for {reading.sensor_id}: {e}", exc_info=True)
                return
            
            # Ensemble Decision
            try:
                overall_is_anomaly, overall_confidence, overall_description = self._ensemble_decision(
                    if_prediction, if_score, stat_is_anomaly, stat_confidence, stat_desc
                )
            except Exception as e:
                self.logger.error(f"Ensemble decision failed for {reading.sensor_id}: {e}", exc_info=True)
                return
            
            self.logger.info(
                f"Final decision for {reading.sensor_id}: "
                f"anomaly={overall_is_anomaly}, confidence={overall_confidence:.4f}, "
                f"type='{overall_description}'"
            )
            
            # Handle anomaly detection results
            if overall_is_anomaly:
                await self._handle_anomaly_detected(
                    reading, event, overall_confidence, overall_description, if_score, 
                    stat_is_anomaly, stat_confidence
                )
            else:
                self.logger.debug(f"No anomaly detected for sensor {reading.sensor_id}")
            
            # Simulate async processing delay
            await asyncio.sleep(0.01)
            
        except Exception as e:
            self.logger.error(
                f"Unexpected error processing DataProcessedEvent {event.event_id}: {e}",
                exc_info=True
            )

    def _validate_sensor_reading(self, reading: SensorReading) -> bool:
        """Validate sensor reading for processing."""
        if not reading.sensor_id or not reading.sensor_id.strip():
            self.logger.error("Sensor reading has empty sensor_id")
            return False
            
        if not isinstance(reading.value, (int, float)):
            self.logger.error(f"Sensor value must be numeric, got {type(reading.value)}")
            return False
            
        if not math.isfinite(reading.value):
            self.logger.error(f"Sensor value is not finite: {reading.value}")
            return False
            
        return True

    async def _process_ml_models(self, features: np.ndarray, reading: SensorReading) -> Optional[Tuple[int, float]]:
        """Process ML models and return predictions."""
        try:
            # Scale the features with error handling
            try:
                scaled_features = self.scaler.fit_transform(features)
                self.logger.debug(f"Scaled features for {reading.sensor_id}: {scaled_features.flatten()}")
            except Exception as e:
                self.logger.error(f"Feature scaling failed: {e}")
                return None
            
            # Isolation Forest Processing
            if not self.isolation_forest_fitted:
                try:
                    self.logger.info("Fitting Isolation Forest model on initial data")
                    self.isolation_forest.fit(scaled_features)
                    self.isolation_forest_fitted = True
                    self.logger.debug("Isolation Forest model fitted successfully")
                except Exception as e:
                    self.logger.error(f"Failed to fit Isolation Forest: {e}")
                    return None
            
            # Make predictions with comprehensive error handling
            try:
                if_prediction = self.isolation_forest.predict(scaled_features)[0]
                if_score = self.isolation_forest.decision_function(scaled_features)[0]
                
                self.logger.info(
                    f"Isolation Forest results for {reading.sensor_id}: "
                    f"prediction={if_prediction} ({'anomaly' if if_prediction == -1 else 'normal'}), "
                    f"score={if_score:.4f}"
                )
                
                return if_prediction, if_score
                
            except Exception as e:
                self.logger.error(f"Isolation Forest prediction failed: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"ML model processing error: {e}")
            return None

    def _process_statistical_method(self, reading: SensorReading) -> Optional[Tuple[bool, float, str]]:
        """Process statistical method and return results."""
        try:
            sensor_id = reading.sensor_id
            
            # Get historical data with improved fallback logic
            if sensor_id in self.historical_data_store:
                hist_data = self.historical_data_store[sensor_id]
                hist_mean = hist_data["mean"]
                hist_std = hist_data["std"]
                
                self.logger.debug(
                    f"Using historical_data_store for {sensor_id}: "
                    f"mean={hist_mean:.4f}, std={hist_std:.4f}"
                )
            elif sensor_id in self.unknown_sensor_baselines:
                baseline_data = self.unknown_sensor_baselines[sensor_id]
                hist_mean = baseline_data["mean"]
                hist_std = baseline_data["std"]
                self.logger.debug(
                    f"Using cached unknown_sensor_baseline for {sensor_id}: "
                    f"mean={hist_mean:.4f}, std={hist_std:.4f}"
                )
            else:
                # First encounter for this unknown sensor
                hist_mean = reading.value  # Use current value as baseline for the first time
                hist_std = self.default_historical_std
                self.unknown_sensor_baselines[sensor_id] = {"mean": hist_mean, "std": hist_std}
                self.logger.info( # Changed from warning to info for first encounter
                    f"First encounter for unknown sensor {sensor_id}, establishing baseline: "
                    f"mean={hist_mean:.4f}, std={hist_std:.4f}"
                )
            
            # Call statistical detector with error handling
            try:
                stat_is_anomaly, stat_confidence, stat_desc = self.statistical_detector.detect(
                    reading.value, hist_mean, hist_std
                )
                
                self.logger.info(
                    f"Statistical detection for {reading.sensor_id}: "
                    f"anomaly={stat_is_anomaly}, confidence={stat_confidence:.4f}, "
                    f"description='{stat_desc}'"
                )
                
                return stat_is_anomaly, stat_confidence, stat_desc
                
            except ValueError as e:
                self.logger.error(f"Statistical detection validation error for {sensor_id}: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Statistical detection failed for {sensor_id}: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Statistical method processing error: {e}")
            return None

    async def _handle_anomaly_detected(
        self, 
        reading: SensorReading, 
        event: DataProcessedEvent,
        overall_confidence: float,
        overall_description: str,
        if_score: float,
        stat_is_anomaly: bool,
        stat_confidence: float
    ) -> None:
        """Handle anomaly detection by creating and publishing alerts."""
        try:
            # Enhanced severity mapping with validation
            if overall_confidence > 0.8:
                severity = 5  # Critical
            elif overall_confidence > 0.6:
                severity = 4  # High
            elif overall_confidence > 0.4:
                severity = 3  # Medium
            elif overall_confidence > 0.2:
                severity = 2  # Low
            else:
                severity = 1  # Very Low
            
            # Create comprehensive evidence dictionary with type safety
            evidence = {
                "raw_value": float(reading.value),
                "if_score": float(if_score),
                "stat_is_anomaly": bool(stat_is_anomaly),
                "stat_confidence": float(stat_confidence),
                "sensor_type": str(reading.sensor_type) if reading.sensor_type else "unknown",
                "timestamp": reading.timestamp.isoformat() if reading.timestamp else None,
                "processing_agent": self.agent_id
            }
            
            # Create AnomalyAlert with comprehensive validation
            try:
                anomaly_alert = AnomalyAlert(
                    sensor_id=reading.sensor_id,
                    anomaly_type=overall_description,
                    severity=severity,
                    confidence=overall_confidence,
                    description=(
                        f"Anomaly detected for sensor {reading.sensor_id} "
                        f"(type: {reading.sensor_type}). "
                        f"Value: {reading.value:.4f}. "
                        f"IF score: {if_score:.4f}. "
                        f"Confidence: {overall_confidence:.4f}"
                    ),
                    evidence=evidence,
                    created_at=datetime.utcnow()
                )
            except ValidationError as e:
                self.logger.error(f"Failed to create AnomalyAlert: {e}")
                return
            except Exception as e:
                self.logger.error(f"Unexpected error creating AnomalyAlert: {e}")
                return
            
            # Create AnomalyDetectedEvent with improved error handling
            try:
                severity_map = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "very_low"}
                severity_str = severity_map.get(severity, "medium")
                
                anomaly_detected_event = AnomalyDetectedEvent(
                    anomaly_details=anomaly_alert.model_dump(),
                    triggering_data=reading.model_dump(),
                    severity=severity_str,
                    correlation_id=event.correlation_id
                )
                
                # Publish with retry logic
                await self._publish_anomaly_event(anomaly_detected_event)
                
            except Exception as e:
                self.logger.error(f"Failed to create or publish AnomalyDetectedEvent: {e}", exc_info=True)
                
        except Exception as e:
            self.logger.error(f"Error in anomaly handling: {e}", exc_info=True)

    async def _publish_anomaly_event(self, event: AnomalyDetectedEvent) -> None:
        """Publish anomaly event with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Publishing AnomalyDetectedEvent (attempt {attempt + 1}): {event.event_id}")
                await self.event_bus.publish(event) # Corrected call
                self.logger.debug(f"Successfully published AnomalyDetectedEvent: {event.event_id}")
                return
            except Exception as e:
                self.logger.warning(f"Publish attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to publish after {max_retries} attempts: {e}")
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
    
    def _ensemble_decision(
        self,
        if_prediction: int,
        if_score: float,
        stat_is_anomaly: bool,
        stat_confidence: float,
        stat_desc: str
    ) -> Tuple[bool, float, str]:
        """
        Make ensemble decision based on Isolation Forest and statistical predictions.
        
        Args:
            if_prediction: Isolation Forest prediction (-1 for anomaly, 1 for normal)
            if_score: Isolation Forest decision function score (lower = more anomalous)
            stat_is_anomaly: Statistical method anomaly flag
            stat_confidence: Statistical method confidence score
            stat_desc: Statistical method anomaly description
            
        Returns:
            Tuple of (is_anomaly, final_confidence_score, final_anomaly_description)
            
        Note:
            Uses OR logic for anomaly detection (if either method detects anomaly)
            and weighted confidence combination based on method reliability.
        """
        # Validate inputs
        if if_prediction not in [-1, 1]:
            self.logger.warning(f"Unexpected IF prediction value: {if_prediction}, treating as normal")
            if_prediction = 1
            
        if not (0 <= stat_confidence <= 1):
            self.logger.warning(f"Statistical confidence out of range: {stat_confidence}, clamping")
            stat_confidence = max(0.0, min(1.0, stat_confidence))
        
        # Determine overall anomaly status using OR logic
        # Either method detecting an anomaly triggers overall anomaly detection
        is_anomaly = (if_prediction == -1) or stat_is_anomaly
        
        # Enhanced Isolation Forest score mapping with better numerical stability
        if if_prediction == -1:
            # Anomaly detected by IF
            # IF scores are typically in range [-1, 1] with lower values being more anomalous
            # Map to confidence score where lower IF scores = higher confidence
            # Use a sigmoid-like transformation for smoother mapping
            normalized_score = max(-1.0, min(1.0, if_score))  # Clamp to expected range
            if_confidence = 0.5 + 0.5 * (1.0 - normalized_score) / 2.0  # Maps [-1,1] to [0.5,1.0]
            if_confidence = max(0.5, min(1.0, if_confidence))  # Ensure bounds
        else:
            # Normal prediction by IF - very low confidence for anomaly
            if_confidence = 0.1  # Small but non-zero to allow for ensemble effects
        
        # Intelligent confidence combination
        if if_prediction == -1 and stat_is_anomaly:
            # Both methods agree on anomaly - high confidence with weighted average
            # Weight based on individual confidences and method reliability
            if_weight = 0.6  # Slight preference for ML method
            stat_weight = 0.4
            final_confidence_score = (
                if_weight * if_confidence + stat_weight * stat_confidence
            )
        elif if_prediction == -1:
            # Only IF detects anomaly
            final_confidence_score = if_confidence * 0.8  # Reduce confidence slightly
        elif stat_is_anomaly:
            # Only statistical method detects anomaly
            final_confidence_score = stat_confidence * 0.8  # Reduce confidence slightly
        else:
            # Neither method detects anomaly
            final_confidence_score = 0.0
        
        # Ensure final confidence is within valid range
        final_confidence_score = max(0.0, min(1.0, final_confidence_score))
        
        # Create comprehensive anomaly description
        if if_prediction == -1 and stat_is_anomaly:
            final_anomaly_description = f"ensemble_anomaly_if_and_{stat_desc}"
        elif if_prediction == -1:
            final_anomaly_description = "isolation_forest_anomaly"
        elif stat_is_anomaly:
            final_anomaly_description = f"statistical_{stat_desc}"
        else:
            final_anomaly_description = "normal"
        
        self.logger.debug(
            f"Ensemble decision details: "
            f"if_pred={if_prediction}, if_score={if_score:.4f}, if_conf={if_confidence:.4f}, "
            f"stat_anom={stat_is_anomaly}, stat_conf={stat_confidence:.4f}, "
            f"final_anom={is_anomaly}, final_conf={final_confidence_score:.4f}, "
            f"desc='{final_anomaly_description}'"
        )
        
        return is_anomaly, final_confidence_score, final_anomaly_description
