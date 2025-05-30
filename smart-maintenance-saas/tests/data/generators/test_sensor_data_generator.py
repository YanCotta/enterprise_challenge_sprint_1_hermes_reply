import pytest
from datetime import datetime
from smart_maintenance_saas.data.generators.sensor_data_generator import SensorDataGenerator, SensorType, SensorReading

# Test normal data generation
def test_generate_normal_reading_temperature():
    generator = SensorDataGenerator(sensor_id="temp_sensor_1", sensor_type=SensorType.TEMPERATURE)
    reading = generator.generate_reading()
    assert isinstance(reading, SensorReading)
    assert reading.sensor_id == "temp_sensor_1"
    assert reading.sensor_type == SensorType.TEMPERATURE
    assert reading.unit == "°C"
    assert 20 < reading.value < 30  # Assuming baseline is 25 +/- noise and variation
    assert 0.95 <= reading.quality <= 1.0
    assert reading.metadata["generation_mode"] == "normal"
    assert isinstance(reading.timestamp, datetime)

def test_generate_normal_reading_vibration():
    generator = SensorDataGenerator(sensor_id="vib_sensor_1", sensor_type=SensorType.VIBRATION)
    reading = generator.generate_reading()
    assert isinstance(reading, SensorReading)
    assert reading.sensor_id == "vib_sensor_1"
    assert reading.sensor_type == SensorType.VIBRATION
    assert reading.unit == "g"
    assert 0.0 < reading.value < 0.2 # Assuming baseline is 0.1 +/- noise and variation
    assert 0.95 <= reading.quality <= 1.0
    assert reading.metadata["generation_mode"] == "normal"

def test_generate_normal_reading_pressure():
    generator = SensorDataGenerator(sensor_id="pressure_sensor_1", sensor_type=SensorType.PRESSURE)
    reading = generator.generate_reading()
    assert isinstance(reading, SensorReading)
    assert reading.sensor_id == "pressure_sensor_1"
    assert reading.sensor_type == SensorType.PRESSURE
    assert reading.unit == "hPa"
    assert 1000 < reading.value < 1020 # Assuming baseline is 1012 +/- noise and variation
    assert 0.95 <= reading.quality <= 1.0
    assert reading.metadata["generation_mode"] == "normal"

# Test anomalous data generation
def test_generate_anomaly_spike():
    generator = SensorDataGenerator(sensor_id="temp_sensor_anomaly", sensor_type=SensorType.TEMPERATURE)
    reading = generator.generate_reading(anomaly=True, anomaly_type="spike")
    assert isinstance(reading, SensorReading)
    assert reading.sensor_id == "temp_sensor_anomaly"
    assert reading.sensor_type == SensorType.TEMPERATURE
    # Spike value should be significantly different from baseline (25°C)
    # Default anomaly_factor_spike for TEMPERATURE is 2.0. Spike is base * (1 + random(0.5,1)*factor)
    # Lower bound: 25 * (1 + 0.5 * 2.0) = 25 * 2 = 50
    # Upper bound: 25 * (1 + 1.0 * 2.0) = 25 * 3 = 75
    # Adding some buffer for noise around baseline before spike

    assert not (5 <= reading.value <= 45) # Check if it's a significant spike
=======
    assert reading.value > 45 or reading.value < 5 # Check if it's a significant spike

    assert 0.6 <= reading.quality <= 0.85
    assert reading.metadata["generation_mode"] == "anomaly_spike"

def test_generate_anomaly_drift():
    generator = SensorDataGenerator(sensor_id="temp_sensor_drift", sensor_type=SensorType.TEMPERATURE)
    reading = generator.generate_reading(anomaly=True, anomaly_type="drift")
    assert isinstance(reading, SensorReading)
    # Drift: current_value += baseline_value * drift_factor * (+/-1)
    # Baseline for temp: 25. Drift factor: 0.3. Change: 25 * 0.3 = 7.5
    # Expected: 25 +/- 7.5 = 17.5 or 32.5 (plus initial noise)
    assert abs(reading.value - generator.baseline["value"]) > (generator.baseline["value"] * generator.baseline["anomaly_factor_drift"] * 0.9) # check if drift is significant
    assert 0.6 <= reading.quality <= 0.85
    assert reading.metadata["generation_mode"] == "anomaly_drift"

def test_generate_anomaly_stuck_at_value():
    generator = SensorDataGenerator(sensor_id="vib_sensor_stuck", sensor_type=SensorType.VIBRATION)
    base_value = generator.baseline["value"]
    reading1 = generator.generate_reading(anomaly=True, anomaly_type="stuck_at_value")
    # Stuck at value should be near baseline * random(0.8, 1.2)
    # For vibration (0.1g), stuck value should be between 0.08g and 0.12g
    assert base_value * 0.7 < reading1.value < base_value * 1.3
    assert 0.6 <= reading1.quality <= 0.85
    assert reading1.metadata["generation_mode"] == "anomaly_stuck_at_value"
    
    # Generate another reading to ensure it's stuck near the *same* kind of value (though not identical due to randomization in stuck logic)
    reading2 = generator.generate_reading(anomaly=True, anomaly_type="stuck_at_value")
    assert base_value * 0.7 < reading2.value < base_value * 1.3


def test_generate_anomaly_stuck_at_zero():
    generator = SensorDataGenerator(sensor_id="pressure_sensor_zero", sensor_type=SensorType.PRESSURE)
    reading = generator.generate_reading(anomaly=True, anomaly_type="stuck_at_zero")
    assert isinstance(reading, SensorReading)
    assert reading.value == 0.0
    assert 0.6 <= reading.quality <= 0.85
    assert reading.metadata["generation_mode"] == "anomaly_stuck_at_zero"

# Test rounding
def test_rounding():
    generator = SensorDataGenerator(sensor_id="test_round", sensor_type=SensorType.TEMPERATURE)
    # Mock np.random.normal to control noise precisely for value testing
    # Mock random.uniform for quality score
    
    # This is a bit more involved to test perfectly due to internal randomness.
    # A simpler check is to ensure the output string representation has the correct number of decimals.
    reading_normal = generator.generate_reading()
    assert len(str(reading_normal.value).split('.')[-1]) <= 3
    assert len(str(reading_normal.quality).split('.')[-1]) <= 2

    reading_anomaly = generator.generate_reading(anomaly=True, anomaly_type="spike")
    assert len(str(reading_anomaly.value).split('.')[-1]) <= 3
    assert len(str(reading_anomaly.quality).split('.')[-1]) <= 2
