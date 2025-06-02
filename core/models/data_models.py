from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AnomalyAlert(BaseModel):
    sensor_id: str
    anomaly_type: str  # e.g., "spike", "statistical_threshold_breach", "model_drift"
    severity: int  # e.g., 1-5 (5 being highest)
    confidence: float  # Initial confidence from the detection system (0.0 to 1.0)
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None  # For any extra specific details
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator("confidence")
    def confidence_must_be_between_0_and_1(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

    @validator("severity")
    def severity_must_be_in_range(cls, v):
        if not (1 <= v <= 5):  # Assuming a 1-5 scale
            raise ValueError("Severity must be between 1 and 5")
        return v


class SensorReading(BaseModel):
    sensor_id: str
    timestamp: datetime
    value: Any  # Can be int, float, bool, str, etc.
    sensor_type: str  # e.g., "TEMPERATURE", "PRESSURE", "VIBRATION", "HUMIDITY"
    unit: Optional[str] = None  # e.g., "°C", "PSI", "mm/s"
    quality: float = 1.0  # Data quality score (0.0 to 1.0), default to perfect

    @validator("quality")
    def quality_must_be_between_0_and_1(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Quality must be between 0.0 and 1.0")
        return v


# Example Usage (not part of the class definition, just for illustration)
if __name__ == "__main__":
    try:
        alert_data = {
            "sensor_id": "temp_sensor_001",
            "anomaly_type": "spike_detected",
            "severity": 4,
            "confidence": 0.85,
            "description": "Unusual temperature spike observed.",
            "timestamp": datetime.now(),
        }
        anomaly_alert = AnomalyAlert(**alert_data)
        print("AnomalyAlert Example:")
        print(anomaly_alert.model_dump_json(indent=2))

        reading_data = {
            "sensor_id": "temp_sensor_001",
            "timestamp": datetime.now(),
            "value": 45.5,
            "sensor_type": "TEMPERATURE",
            "unit": "°C",
            "quality": 0.95,
        }
        sensor_reading = SensorReading(**reading_data)
        print("\nSensorReading Example:")
        print(sensor_reading.model_dump_json(indent=2))

        # Example of validation error
        # invalid_alert = AnomalyAlert(sensor_id="s1", anomaly_type="t", severity=6, confidence=1.1)
        # print(invalid_alert)
    except ValueError as e:
        print(f"\nError during Pydantic model creation: {e}")
