"""Anomaly detection agent for processing sensor data and detecting anomalies."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

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

    def __init__(self, agent_id: str, event_bus: EventBus, specific_settings: dict = None):
        """
        Initialize the AnomalyDetectionAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            event_bus: EventBus instance for event communication
            specific_settings: Optional dictionary of agent-specific settings
        """
        super().__init__(agent_id, event_bus)
        
        # Initialize ML models
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination='auto', 
            random_state=42, 
            n_estimators=100
        )
        self.isolation_forest_fitted = False
        
        # Initialize statistical detector
        self.statistical_detector = StatisticalAnomalyDetector()
        
        # Mock historical data store for statistical analysis
        # In production, this would come from a database
        self.historical_data_store: Dict[str, Dict[str, float]] = {
            "sensor_temp_001": {"mean": 22.5, "std": 2.1},
            "sensor_temp_002": {"mean": 24.8, "std": 1.8},
            "sensor_vibr_001": {"mean": 0.05, "std": 0.02},
            "sensor_vibr_002": {"mean": 0.03, "std": 0.015},
            "sensor_press_001": {"mean": 101.3, "std": 0.8},
            "sensor_press_002": {"mean": 98.7, "std": 1.2},
        }
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")

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
        """
        self.logger.debug(f"Received event: {event}")
        
        try:
            # Parse the processed_data back into a SensorReading model instance
            reading = SensorReading(**event.processed_data)
            
            # Log the processing
            self.logger.info(
                f"Processing sensor reading for {reading.sensor_id} with value {reading.value}"
            )
            
            # Extract features for ML models
            features = self._extract_features(reading)
            
            # Check if features extraction was successful
            if features.size == 0:
                self.logger.warning(
                    f"No features extracted for sensor {reading.sensor_id}, skipping processing"
                )
                return
            
            # Scale the features
            scaled_features = self.scaler.fit_transform(features)
            self.logger.debug(f"Scaled features: {scaled_features.flatten()}")
            
            # Isolation Forest Prediction
            if not self.isolation_forest_fitted:
                self.logger.info("Fitting Isolation Forest model on initial data")
                self.isolation_forest.fit(scaled_features)
                self.isolation_forest_fitted = True
                self.logger.debug("Isolation Forest model fitted successfully")
            
            # Make predictions with Isolation Forest
            if_prediction = self.isolation_forest.predict(scaled_features)[0]
            if_score = self.isolation_forest.decision_function(scaled_features)[0]
            
            self.logger.info(
                f"Isolation Forest prediction for {reading.sensor_id}: "
                f"prediction={if_prediction} ({'anomaly' if if_prediction == -1 else 'normal'}), "
                f"score={if_score:.4f}"
            )
            
            # Statistical Method Prediction
            sensor_id = reading.sensor_id
            if sensor_id in self.historical_data_store:
                hist_mean = self.historical_data_store[sensor_id]["mean"]
                hist_std = self.historical_data_store[sensor_id]["std"]
                
                self.logger.debug(
                    f"Using historical data for {sensor_id}: mean={hist_mean}, std={hist_std}"
                )
            else:
                # Use default values if sensor not in historical data
                hist_mean = reading.value
                hist_std = 0.1  # Small default standard deviation
                
                self.logger.warning(
                    f"No historical data found for sensor {sensor_id}, "
                    f"using defaults: mean={hist_mean}, std={hist_std}"
                )
              # Call statistical detector
            stat_is_anomaly, stat_confidence, stat_desc = self.statistical_detector.detect(
                reading.value, hist_mean, hist_std
            )
            
            self.logger.info(
                f"Statistical detection for {reading.sensor_id}: "
                f"is_anomaly={stat_is_anomaly}, confidence={stat_confidence:.4f}, "
                f"description='{stat_desc}'"
            )
              # Ensemble Decision
            overall_is_anomaly, overall_confidence, overall_description = self._ensemble_decision(
                if_prediction, if_score, stat_is_anomaly, stat_confidence, stat_desc
            )
            
            self.logger.info(
                f"Ensemble decision for {reading.sensor_id}: "
                f"is_anomaly={overall_is_anomaly}, confidence={overall_confidence:.4f}, "
                f"description='{overall_description}'"
            )
            
            # If anomaly detected, create alert and publish event
            if overall_is_anomaly:
                try:
                    # Map confidence to severity (1-5)
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
                    
                    # Create AnomalyAlert
                    anomaly_alert = AnomalyAlert(
                        sensor_id=reading.sensor_id,
                        anomaly_type=overall_description,
                        severity=severity,
                        confidence=overall_confidence,
                        description=(
                            f"Anomaly detected for sensor {reading.sensor_id}. "
                            f"Value: {reading.value}. IF score: {if_score:.2f}."
                        ),
                        evidence={
                            "raw_value": float(reading.value),
                            "if_score": float(if_score),
                            "stat_is_anomaly": stat_is_anomaly,
                            "stat_confidence": float(stat_confidence)
                        },
                        created_at=datetime.utcnow()
                    )
                    
                    # Map severity integer back to string for event
                    severity_map = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "very_low"}
                    severity_str = severity_map.get(severity, "medium")
                    
                    # Create AnomalyDetectedEvent
                    anomaly_detected_event = AnomalyDetectedEvent(
                        anomaly_details=anomaly_alert.model_dump(),
                        triggering_data=reading.model_dump(),
                        severity=severity_str,
                        correlation_id=event.correlation_id
                    )
                    
                    # Publish the event
                    self.logger.info(f"Publishing AnomalyDetectedEvent: {anomaly_detected_event}")
                    await self.event_bus.publish(AnomalyDetectedEvent.__name__, anomaly_detected_event)
                    
                except Exception as e:
                    self.logger.error(
                        f"Error creating or publishing anomaly alert for {reading.sensor_id}: {e}",
                        exc_info=True
                    )
            else:
                self.logger.debug(f"No anomaly detected for sensor {reading.sensor_id}")
            
            # Simulate some async work
            await asyncio.sleep(0.01)
            
        except Exception as e:
            self.logger.error(
                f"Error processing DataProcessedEvent: {e}", 
                exc_info=True
            )

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
        """
        # Determine overall anomaly status using OR logic
        is_anomaly = (if_prediction == -1) or stat_is_anomaly
        
        # Map Isolation Forest score to confidence (0.0 to 1.0)
        # Lower IF scores indicate higher anomaly confidence
        # Normalize score to 0-1 range where 1.0 = high confidence anomaly
        if if_prediction == -1:
            # Anomaly detected by IF - map negative scores to higher confidence
            if_confidence = min(1.0, max(0.5, 1.0 - (if_score + 0.5)))
        else:
            # Normal prediction by IF - low confidence for anomaly
            if_confidence = 0.0
        
        # Combine confidences - use maximum of individual confidences
        final_confidence_score = max(if_confidence, stat_confidence if stat_is_anomaly else 0.0)
        
        # Determine final anomaly description
        if if_prediction == -1 and stat_is_anomaly:
            final_anomaly_description = f"IF_Statistical_Anomaly_{stat_desc}"
        elif if_prediction == -1:
            final_anomaly_description = "IsolationForest_Anomaly"
        elif stat_is_anomaly:
            final_anomaly_description = f"Statistical_{stat_desc}"
        else:
            final_anomaly_description = "normal"
        
        self.logger.debug(
            f"Ensemble decision: is_anomaly={is_anomaly}, "
            f"confidence={final_confidence_score:.4f}, "
            f"description='{final_anomaly_description}'"
        )
        
        return is_anomaly, final_confidence_score, final_anomaly_description
