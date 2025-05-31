from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

class SensorReadingCreate(BaseModel):
    sensor_id: UUID
    value: float
    timestamp_utc: datetime
    correlation_id: Optional[UUID] = None
    # Ensure metadata is always present, defaulting to an empty dict
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SensorReading(BaseModel):
    sensor_id: UUID
    value: float
    timestamp_utc: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[UUID] = None
