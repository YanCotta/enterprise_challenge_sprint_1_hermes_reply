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
            
            # Simulate some async work
            await asyncio.sleep(0.01)
            
            # TODO: In the next step, we'll add actual anomaly detection logic here
            # For now, just log that we received and parsed the data successfully
            self.logger.debug(
                f"Successfully parsed sensor reading: "
                f"ID={reading.sensor_id}, Value={reading.value}, "
                f"Type={reading.sensor_type}, Timestamp={reading.timestamp}"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error processing DataProcessedEvent: {e}", 
                exc_info=True
            )
