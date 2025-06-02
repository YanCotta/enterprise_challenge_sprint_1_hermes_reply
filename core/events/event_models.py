from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid  # Added import for uuid
from pydantic import BaseModel, Field


class BaseEventModel(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # In a real scenario, more common fields would be here,
    # like user_id, source_ip, etc.


class AnomalyValidatedEvent(BaseEventModel):
    original_anomaly_alert_payload: Dict[str, Any]
    triggering_reading_payload: Dict[str, Any]
    validation_status: str
    final_confidence: float
    validation_reasons: List[str]
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    correlation_id: Optional[str] = None

    # Add event_type with a default value for this specific event
    event_type: str = "AnomalyValidated"

    # Optional: Add a simple method to convert to dict or for logging
    def to_dict(self):
        return self.dict()


class AnomalyDetectedEvent(BaseEventModel):
    # These are example fields. The actual fields would depend on what data
    # the anomaly detection system generates.
    # For the ValidationAgent, we expect 'anomaly_details' (parsable to AnomalyAlert)
    # and 'triggering_data' (parsable to SensorReading).
    anomaly_details: Dict[str, Any]  # Should contain data for AnomalyAlert
    triggering_data: Dict[str, Any]  # Should contain data for SensorReading
    source_system: str  # e.g., "PrimaryMonitoringSystem"
    correlation_id: Optional[str] = None

    event_type: str = "AnomalyDetected"

    def to_dict(self):
        return self.dict()


# Example Usage (not part of the class definition, just for illustration)
if __name__ == "__main__":
    # Example for AnomalyValidatedEvent
    dummy_validated_event = AnomalyValidatedEvent(
        original_anomaly_alert_payload={"data": "some_alert_payload"},
        triggering_reading_payload={"data": "some_reading_payload"},
        validation_status="CONFIRMED",
        final_confidence=0.95,
        validation_reasons=["Pattern matched", "Sensor data consistent"],
        agent_id="validation_agent_001",
        correlation_id="corr_abc123",
    )
    print("Validated Event Example:", dummy_validated_event.to_dict())

    # Example for AnomalyDetectedEvent
    dummy_detected_event = AnomalyDetectedEvent(
        anomaly_details={
            "confidence": 0.85,
            "anomaly_type": "spike",
            "severity": 4,
            "sensor_id": "sensor_123",
            "description": "Sudden spike detected",
        },
        triggering_data={
            "value": 120.5,
            "timestamp": "2023-01-01T12:00:00Z",
            "quality": 0.9,
            "sensor_type": "TEMPERATURE",
            "unit": "C",
        },
        source_system="TestSystem",
        correlation_id="corr_xyz789",
    )
    print("\nDetected Event Example:", dummy_detected_event.to_dict())
