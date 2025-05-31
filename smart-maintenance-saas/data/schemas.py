# This file will contain Pydantic schemas for data validation and serialization.
# For example, sensor data schemas, asset information schemas, etc.

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any # Ensure Any is imported
import uuid

from pydantic import BaseModel, Field, validator


# SensorType Enum (already in sensor_data_generator.py, ensure it's here)
class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    VIBRATION = "vibration"
    PRESSURE = "pressure"
    # Add more as needed

# SensorReading Pydantic Model (already in sensor_data_generator.py, ensure it's here and updated)
class SensorReadingCreate(BaseModel):
    """
    Schema for creating a new sensor reading. Used for initial validation of incoming data.
    All datetime fields are UTC.
    """
    sensor_id: str = Field(..., description="Unique sensor identifier")
    value: float = Field(..., description="The sensor reading value")
    timestamp: Optional[datetime] = Field(None, description="UTC timestamp of the reading")
    sensor_type: Optional[SensorType] = Field(None, description="Type of the sensor")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    quality: float = Field(default=1.0, ge=0, le=1, description="Data quality score")
    correlation_id: Optional[uuid.UUID] = Field(None, description="Correlation ID for tracking")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: str
        }

class SensorReading(SensorReadingCreate):
    """
    Schema for a complete sensor reading, including all enriched fields.
    Inherits from SensorReadingCreate and adds required fields that must be present
    after processing/enrichment.
    """
    sensor_type: SensorType  # Make required in final form
    unit: str  # Make required in final form
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the reading was ingested"
    )

    class Config:
        from_attributes = True  # For Pydantic v2 ORM mode
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: str
        }


class DataQuality(str, Enum):
    """Enum for data quality levels."""
    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"


class SensorReadingBase(BaseModel):
    """Base model for a single sensor reading."""
    sensor_id: str = Field(..., description="Unique identifier for the sensor.")
    sensor_type: SensorType = Field(..., description="Type of the sensor.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the reading (UTC).")
    value: Union[float, int, str, bool, Dict, List] = Field(..., description="The actual sensor value.")
    unit: Optional[str] = Field(None, description="Unit of measurement for the sensor value (e.g., °C, %, mm/s).")
    
    quality: DataQuality = Field(DataQuality.GOOD, description="Quality of the sensor reading.")
    sensor_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata for the reading.") # Changed 'any' to 'Any'

    @validator('timestamp', pre=True, always=True)
    def ensure_utc_timestamp(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace('Z', '+00:00'))
        if v.tzinfo is None:
            return v.replace(tzinfo=datetime.timezone.utc)
        return v.astimezone(datetime.timezone.utc)


# (SensorType, SensorReading, AnomalyAlert, MaintenanceTask should already be in this file)

# Note: The original SensorReading that inherited SensorReadingBase is now replaced by the one above.
# This SensorReadingBase and SensorReadingCreate might need adjustments
# if they were intended to be used with the new SensorReading model.
# For now, they are left as is, as per the focused nature of the subtask.

class AnomalyDetectionParameters(BaseModel):
    """Parameters for configuring anomaly detection for a sensor."""
    sensor_id: str
    method: str # e.g., "threshold", "z_score", "ewma"
    parameters: Dict[str, Any] # Changed 'any' to 'Any'


class AnomalyAlert(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    sensor_id: str
    anomaly_type: str  # e.g., "spike", "drift", "stuck_at_value"
    severity: int = Field(ge=1, le=5)  # 1 (low) to 5 (critical)
    confidence: float = Field(ge=0, le=1) # Confidence in the anomaly detection
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict) # e.g., {"current_value": 105.5, "baseline": 70.0}
    recommended_actions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "open"  # e.g., "open", "acknowledged", "resolved"

    class Config:
        orm_mode = True # or from_attributes = True for Pydantic v2
        use_enum_values = True


class MaintenanceTaskStatus(str, Enum):
    """Status of a maintenance task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# (SensorType, SensorReading, AnomalyAlert should already be here)

class MaintenanceTask(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    equipment_id: str  # Could be a sensor_id or a larger asset ID
    task_type: str  # e.g., "inspection", "repair", "replacement", "calibration"
    description: Optional[str] = None # Optional field for more details
    priority: int = Field(default=3, ge=1, le=5)  # 1 (highest) to 5 (lowest)
    status: str = "pending"  # e.g., "pending", "in_progress", "completed", "cancelled", "on_hold"
    estimated_duration_hours: Optional[float] = None
    actual_duration_hours: Optional[float] = None
    required_skills: List[str] = Field(default_factory=list) # e.g., ["electrical", "mechanical"]
    parts_needed: List[str] = Field(default_factory=list) # e.g., ["part_xyz_123", "filter_abc_789"]
    assigned_technician_id: Optional[str] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None # To be updated by the application logic

    class Config:
        orm_mode = True # or from_attributes = True for Pydantic v2
        use_enum_values = True


class AssetInformation(BaseModel):
    """Schema for asset information."""
    asset_id: str = Field(..., description="Unique identifier for the asset.")
    name: str = Field(..., description="Name of the asset.")
    asset_type: str = Field(..., description="Type of the asset (e.g., 'Pump', 'Motor', 'HVAC Unit').")
    location: Optional[str] = Field(None, description="Location of the asset.")
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the asset.")
    model_number: Optional[str] = Field(None, description="Model number of the asset.")
    installation_date: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    operational_status: str = Field("active", description="Operational status (e.g., 'active', 'inactive', 'under_maintenance').")
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Technical specifications.") # Changed 'any' to 'Any'
    
    class Config:
        orm_mode = True

# Example of a more complex schema that might be used for API responses or data aggregation
class SensorDataSummary(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    reading_count: int
    last_reading_timestamp: Optional[datetime]
    average_value: Optional[float] # Meaningful only for numeric types
    min_value: Optional[float] # Meaningful only for numeric types
    max_value: Optional[float] # Meaningful only for numeric types

    class Config:
        use_enum_values = True

# Further schemas can be added here as the application evolves, for example:
# - User schemas
# - Alert schemas
# - Predictive maintenance model input/output schemas
# - Configuration schemas for different system components

# Ensure all necessary imports are at the top
# (Pydantic, datetime, Enum, typing modules are already imported)

# Consider adding __all__ if you want to control what `from .schemas import *` imports
# __all__ = [
#     "SensorType",
#     "DataQuality",
#     "SensorReadingBase",
#     "SensorReadingCreate",
#     "SensorReading",
#     "AnomalyDetectionParameters",
#     "MaintenanceTaskStatus",
#     "MaintenanceTask",
#     "AssetInformation",
#     "SensorDataSummary",
# ]
