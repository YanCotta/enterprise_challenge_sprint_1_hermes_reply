import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import func  # for server_default=func.now()
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from core.database.base import Base


class SensorReadingORM(Base):
    __tablename__ = "sensor_readings"

    # TimescaleDB hypertable requires composite primary key (timestamp, sensor_id)
    # The id column exists with auto-increment sequence but is NOT the primary key
    # This aligns with the actual database schema created by TimescaleDB migrations
    id = Column(Integer, autoincrement=True, nullable=False, index=True)
    sensor_id = Column(String(255), index=True, nullable=False)
    sensor_type = Column(
        String(50), nullable=False
    )  # Consider Enum type if DB supports / desired
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    timestamp = Column(
        DateTime(timezone=True), nullable=False, index=True
    )
    quality = Column(Float, default=1.0)
    sensor_metadata = Column(
        JSONB, nullable=True
    )  # Renamed from 'metadata' to avoid conflicts

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # TimescaleDB hypertable configuration - composite primary key required
    # This matches the actual database schema: PRIMARY KEY (timestamp, sensor_id)
    __table_args__ = (
        PrimaryKeyConstraint('timestamp', 'sensor_id', name='sensor_readings_pkey'),
        Index('ix_sensor_readings_sensor_id_timestamp', 'sensor_id', 'timestamp'),
    )

    # We'll handle creating the hypertable in Alembic migrations instead of using SQLAlchemy
    # Manual TimescaleDB: Run `SELECT create_hypertable('sensor_readings', 'timestamp');`
    #
    # Example of composite index (uncomment if needed):
    # __table_args__ = (
    #     Index('ix_sensor_readings_sensor_id_timestamp', 'sensor_id', 'timestamp', unique=False),
    # )


class AnomalyAlertORM(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sensor_id = Column(
        String(255), index=True, nullable=False
    )  # Could be a FK to a SensorORM if sensors are registered
    # sensor_reading_id = Column(Integer, ForeignKey('sensor_readings.id'), nullable=True) # Optional FK to specific reading

    anomaly_type = Column(String(100), nullable=False)
    severity = Column(Integer, nullable=False)  # ge=1, le=5 (validation at app level)
    confidence = Column(Float, nullable=True)  # ge=0, le=1 (validation at app level)
    description = Column(Text, nullable=True)
    evidence = Column(JSONB, nullable=True)
    recommended_actions = Column(
        ARRAY(String), nullable=True, default=[]
    )  # Ensure default is a list
    status = Column(String(50), default="open", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # sensor_reading = relationship("SensorReadingORM") # If FK is setup


class MaintenanceTaskStatus(str, Enum):
    """Enum for maintenance task status values"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MaintenanceTaskORM(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # anomaly_alert_id = Column(UUID(as_uuid=True), ForeignKey('anomaly_alerts.id'), nullable=True) # Optional FK

    equipment_id = Column(String(255), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(
        Integer, default=3, nullable=False
    )  # ge=1, le=5 (validation at app level)
    status = Column(String(50), default="pending", nullable=False)

    estimated_duration_hours = Column(Float, nullable=True)
    actual_duration_hours = Column(Float, nullable=True)

    required_skills = Column(ARRAY(String), nullable=True, default=[])
    parts_needed = Column(ARRAY(String), nullable=True, default=[])

    assigned_technician_id = Column(String(255), nullable=True)

    scheduled_start_time = Column(DateTime(timezone=True), nullable=True)
    scheduled_end_time = Column(DateTime(timezone=True), nullable=True)
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # anomaly_alert = relationship("AnomalyAlertORM") # If FK is setup


class MaintenanceLogORM(Base):
    __tablename__ = "maintenance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    task_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References maintenance_tasks.id
    equipment_id = Column(String(255), nullable=False, index=True)
    completion_date = Column(DateTime(timezone=True), nullable=False)
    technician_id = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(
        SQLEnum(MaintenanceTaskStatus), 
        default=MaintenanceTaskStatus.COMPLETED, 
        nullable=False
    )
    actual_duration_hours = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# Placeholder for a potential Sensor Hardware/Asset table
# class SensorORM(Base):
#    __tablename__ = "sensors"
#    id = Column(String(255), primary_key=True, index=True) # sensor_id from readings
#    type = Column(String(50))
#    location = Column(String(255))
#    installed_at = Column(DateTime(timezone=True))
#    # ... other relevant sensor metadata
