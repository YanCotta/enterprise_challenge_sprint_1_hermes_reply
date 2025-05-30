import json
import random
import time
from datetime import datetime, timedelta
from enum import Enum

class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    VIBRATION = "vibration"
    PRESSURE = "pressure"

from pydantic import BaseModel, Field

class SensorReading(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor identifier")
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    quality: float = Field(ge=0, le=1, description="Data quality score", default=1.0)
    metadata: dict = Field(default_factory=dict)

import numpy as np
from typing import List

class SensorDataGenerator:
    def __init__(self, sensor_id: str, sensor_type: SensorType):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.baseline = self._get_baseline_values_for_type()

    def _get_baseline_values_for_type(self) -> dict:
        if self.sensor_type == SensorType.TEMPERATURE:
            return {"value": 25.0, "unit": "°C", "noise_std": 0.5, "anomaly_factor_spike": 2.0, "anomaly_factor_drift": 0.3}
        elif self.sensor_type == SensorType.VIBRATION:
            return {"value": 0.1, "unit": "g", "noise_std": 0.02, "anomaly_factor_spike": 5.0, "anomaly_factor_drift": 0.5}
        elif self.sensor_type == SensorType.PRESSURE:
            return {"value": 1012.0, "unit": "hPa", "noise_std": 2.0, "anomaly_factor_spike": 1.5, "anomaly_factor_drift": 0.1}
        # Add other sensor types
        return {"value": 10.0, "unit": "units", "noise_std": 0.1, "anomaly_factor_spike": 3.0, "anomaly_factor_drift": 0.4}

    def generate_reading(self, anomaly: bool = False, anomaly_type: str = "spike") -> SensorReading:
        base_value = self.baseline["value"]
        noise = np.random.normal(0, self.baseline["noise_std"])
        current_value = base_value + noise
        quality_score = random.uniform(0.95, 1.0)
        metadata = {"generation_mode": "normal"}

        if anomaly:
            quality_score = random.uniform(0.6, 0.85)
            metadata["generation_mode"] = f"anomaly_{anomaly_type}"
            if anomaly_type == "spike":
                current_value *= (1 + random.uniform(0.5, 1.0) * self.baseline["anomaly_factor_spike"]) # More pronounced spike
            elif anomaly_type == "drift":
                current_value += self.baseline["value"] * self.baseline["anomaly_factor_drift"] * (1 if random.random() > 0.5 else -1)
            elif anomaly_type == "stuck_at_value":
                current_value = base_value * random.uniform(0.8, 1.2) # Stuck near baseline
            elif anomaly_type == "stuck_at_zero":
                current_value = 0.0
            # Add more anomaly types

        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=round(current_value, 3),
            unit=self.baseline["unit"],
            timestamp=datetime.utcnow(),
            quality=round(quality_score, 2),
            metadata=metadata
        )

# Configuration
NUM_SENSORS = 5
DATA_INTERVAL_SECONDS = 10  # Interval in seconds between data points
SIMULATION_DURATION_HOURS = 1  # Duration of the simulation in hours

# Sensor types and their normal operating ranges
SENSOR_CONFIG = {
    "temperature": {"min": 20, "max": 30, "unit": "°C"},
    "vibration": {"min": 0, "max": 5, "unit": "mm/s"},
    "pressure": {"min": 100, "max": 120, "unit": "PSI"},
    "humidity": {"min": 40, "max": 60, "unit": "%"},
    "voltage": {"min": 220, "max": 240, "unit": "V"}
}

def generate_sensor_data(sensor_id, sensor_type, timestamp):
    """Generates a single sensor data point."""
    config = SENSOR_CONFIG[sensor_type]
    value = random.uniform(config["min"], config["max"])

    # Introduce occasional anomalies (e.g., 1% chance)
    if random.random() < 0.01:
        value *= random.uniform(0.5, 1.5)  # Deviate significantly

    return {
        "timestamp": timestamp.isoformat(),
        "sensor_id": f"{sensor_type}-{sensor_id}",
        "value": round(value, 2),
        "unit": config["unit"]
    }

def main():
    """Main function to generate and print sensor data."""
    print("Starting sensor data generation...")
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=SIMULATION_DURATION_HOURS)

    sensor_types = list(SENSOR_CONFIG.keys())

    try:
        while datetime.now() < end_time:
            current_time = datetime.now()
            for i in range(NUM_SENSORS):
                sensor_type = random.choice(sensor_types)
                data_point = generate_sensor_data(i + 1, sensor_type, current_time)
                print(json.dumps(data_point))

            time.sleep(DATA_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nData generation stopped by user.")
    finally:
        print("Sensor data generation finished.")

if __name__ == "__main__":
    main()
