import pytest
from pydantic import ValidationError
from datetime import datetime
from typing import Dict, Any

# Adjust the import path based on the actual location of DataValidator
# Assuming 'smart-maintenance-saas' is the root for Python's perspective in tests
from data.processors.data_validator import DataValidator
from data.schemas import SensorReadingCreate, SensorType # Make sure SensorType is imported

class TestDataValidator:
    def setup_method(self):
        self.validator = DataValidator()

    def test_validate_success_basic(self):
        raw_data = {
            "sensor_id": "sensor-001",
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "C"
        }
        result = self.validator.validate(raw_data)
        assert isinstance(result, SensorReadingCreate)
        assert result.sensor_id == raw_data["sensor_id"]
        assert result.value == raw_data["value"]
        assert result.sensor_type == SensorType.TEMPERATURE
        assert result.unit == raw_data["unit"]
        assert result.quality == 1.0 # Default value
        assert result.timestamp is None # Default if not provided
        assert result.sensor_metadata == {} # Default value

    def test_validate_success_all_fields(self):
        now = datetime.utcnow()
        raw_data = {
            "sensor_id": "sensor-002",
            "sensor_type": SensorType.VIBRATION.value,
            "value": 12.5,
            "unit": "mm/s",
            "timestamp": now.isoformat(),
            "quality": 0.95,
            "sensor_metadata": {"location": "pump-A"}
        }
        result = self.validator.validate(raw_data)
        assert isinstance(result, SensorReadingCreate)
        assert result.sensor_id == raw_data["sensor_id"]
        assert result.value == raw_data["value"]
        assert result.sensor_type == SensorType.VIBRATION
        assert result.unit == raw_data["unit"]

        assert result.timestamp is not None
        assert result.timestamp.year == now.year
        assert result.timestamp.month == now.month
        assert result.timestamp.day == now.day
        assert result.timestamp.hour == now.hour
        assert result.timestamp.minute == now.minute

        assert result.quality == raw_data["quality"]
        assert result.sensor_metadata == raw_data["sensor_metadata"]

    def test_validate_success_quality_boundaries(self):
        raw_data_min_quality = {
            "sensor_id": "sensor-q1",
            "sensor_type": "temperature",
            "value": 20.0,
            "unit": "C",
            "quality": 0.0
        }
        result_min = self.validator.validate(raw_data_min_quality)
        assert result_min.quality == 0.0

        raw_data_max_quality = {
            "sensor_id": "sensor-q2",
            "sensor_type": "temperature",
            "value": 21.0,
            "unit": "C",
            "quality": 1.0
        }
        result_max = self.validator.validate(raw_data_max_quality)
        assert result_max.quality == 1.0

    def test_validate_failure_missing_required_field(self):
        raw_data = {
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "C"
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(raw_data)
        assert "sensor_id" in str(exc_info.value).lower()
        assert "field required" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()


    def test_validate_failure_incorrect_type_for_value(self):
        raw_data = {
            "sensor_id": "sensor-003",
            "sensor_type": "pressure",
            "value": "not-a-float",
            "unit": "Pa"
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(raw_data)
        assert "value" in str(exc_info.value).lower()

    def test_validate_failure_incorrect_type_for_sensor_id(self):
        raw_data = {
            "sensor_id": 12345,
            "sensor_type": "pressure",
            "value": 10.0,
            "unit": "Pa"
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(raw_data)
        assert "sensor_id" in str(exc_info.value).lower()

    def test_validate_failure_invalid_enum_value_for_sensor_type(self):
        raw_data = {
            "sensor_id": "sensor-004",
            "sensor_type": "unknown_type",
            "value": 10.0,
            "unit": "X"
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(raw_data)
        assert "sensor_type" in str(exc_info.value).lower()

    def test_validate_failure_out_of_range_quality_too_high(self):
        raw_data = {
            "sensor_id": "sensor-005",
            "sensor_type": "temperature",
            "value": 30.0,
            "unit": "C",
            "quality": 1.5
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(raw_data)
        assert "quality" in str(exc_info.value).lower()

    def test_validate_failure_out_of_range_quality_too_low(self):
        raw_data = {
            "sensor_id": "sensor-006",
            "sensor_type": "temperature",
            "value": 30.0,
            "unit": "C",
            "quality": -0.5
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(raw_data)
        assert "quality" in str(exc_info.value).lower()
