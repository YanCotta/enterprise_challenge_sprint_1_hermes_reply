import pytest
from datetime import datetime
import uuid

from data.schemas import (
    AnomalyAlert,
    AnomalyType,
    AnomalyStatus,
    MaintenanceTask,
    MaintenanceTaskStatus
)

class TestAnomalyAlertEnumUsage:

    def test_anomaly_alert_accepts_anomaly_type_enum(self):
        alert = AnomalyAlert(
            sensor_id="sensor1",
            anomaly_type=AnomalyType.SPIKE,
            severity=3,
            confidence=0.7,
            description="Test spike alert",
            # status will use default AnomalyStatus.OPEN
        )
        assert alert.anomaly_type == AnomalyType.SPIKE
        # With use_enum_values=True, the field value becomes a string
        assert alert.anomaly_type == "spike"

    def test_anomaly_alert_accepts_anomaly_type_string(self):
        alert = AnomalyAlert(
            sensor_id="sensor1",
            anomaly_type="drift", # String value
            severity=3,
            confidence=0.7,
            description="Test drift alert",
        )
        assert alert.anomaly_type == AnomalyType.DRIFT # Corrected assertion
        # With use_enum_values=True, the field value becomes a string
        assert alert.anomaly_type == "drift"

    def test_anomaly_alert_serialization_anomaly_type(self):
        alert = AnomalyAlert(
            sensor_id="sensor1",
            anomaly_type=AnomalyType.STUCK_AT_VALUE,
            severity=4,
            confidence=0.9,
            description="Test stuck alert",
        )
        dumped_alert = alert.model_dump()
        assert dumped_alert["anomaly_type"] == "stuck_at_value" # Enum.value

    def test_anomaly_alert_accepts_anomaly_status_enum(self):
        alert = AnomalyAlert(
            sensor_id="sensor2",
            anomaly_type=AnomalyType.UNKNOWN,
            severity=1,
            confidence=0.3,
            description="Test unknown alert",
            status=AnomalyStatus.ACKNOWLEDGED,
        )
        assert alert.status == AnomalyStatus.ACKNOWLEDGED
        # With use_enum_values=True, the field value becomes a string
        assert alert.status == "acknowledged"

    def test_anomaly_alert_accepts_anomaly_status_string(self):
        alert = AnomalyAlert(
            sensor_id="sensor2",
            anomaly_type="spike",
            severity=2,
            confidence=0.5,
            description="Test resolved alert",
            status="resolved", # String value
        )
        assert alert.status == AnomalyStatus.RESOLVED # Corrected assertion
        # With use_enum_values=True, the field value becomes a string
        assert alert.status == "resolved"

    def test_anomaly_alert_serialization_status(self):
        alert = AnomalyAlert(
            sensor_id="sensor3",
            anomaly_type=AnomalyType.DRIFT,
            severity=3,
            confidence=0.6,
            description="Test open alert",
            status=AnomalyStatus.OPEN, # Default, but explicit for test
        )
        dumped_alert = alert.model_dump()
        assert dumped_alert["status"] == "open" # Enum.value

    def test_anomaly_alert_invalid_anomaly_type_string(self):
        with pytest.raises(ValueError): # Pydantic v2 uses ValueError for enum validation
            AnomalyAlert(
                sensor_id="sensor_invalid",
                anomaly_type="non_existent_type", # Invalid string
                severity=1,
                confidence=0.1,
                description="Invalid type test"
            )

    def test_anomaly_alert_invalid_status_string(self):
        with pytest.raises(ValueError):
            AnomalyAlert(
                sensor_id="sensor_invalid_status",
                anomaly_type=AnomalyType.SPIKE,
                severity=1,
                confidence=0.1,
                description="Invalid status test",
                status="non_existent_status" # Invalid string
            )

class TestMaintenanceTaskEnumUsage:

    def test_maintenance_task_accepts_status_enum(self):
        task = MaintenanceTask(
            equipment_id="eq1",
            task_type="inspection",
            status=MaintenanceTaskStatus.IN_PROGRESS,
        )
        assert task.status == MaintenanceTaskStatus.IN_PROGRESS
        # With use_enum_values=True, the field value becomes a string
        assert task.status == "in_progress"

    def test_maintenance_task_accepts_status_string(self):
        task = MaintenanceTask(
            equipment_id="eq2",
            task_type="repair",
            status="completed", # String value
        )
        assert task.status == MaintenanceTaskStatus.COMPLETED # Corrected assertion
        # With use_enum_values=True, the field value becomes a string
        assert task.status == "completed"

    def test_maintenance_task_serialization_status(self):
        task = MaintenanceTask(
            equipment_id="eq3",
            task_type="replacement",
            status=MaintenanceTaskStatus.PENDING, # Default, but explicit
        )
        dumped_task = task.model_dump()
        assert dumped_task["status"] == "pending" # Enum.value

    def test_maintenance_task_default_status(self):
        task = MaintenanceTask(
            equipment_id="eq4",
            task_type="calibration",
        )
        assert task.status == MaintenanceTaskStatus.PENDING # Check default
        dumped_task = task.model_dump()
        assert dumped_task["status"] == "pending"

    def test_maintenance_task_invalid_status_string(self):
        with pytest.raises(ValueError):
            MaintenanceTask(
                equipment_id="eq_invalid",
                task_type="checkup",
                status="non_existent_status" # Invalid string
            )
pytest
