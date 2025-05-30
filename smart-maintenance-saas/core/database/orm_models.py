import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    ForeignKey,
    func # for server_default=func.now()
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class SensorReadingORM(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    # Alternatively, for UUID PK:
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    sensor_id = Column(String(255), index=True, nullable=False)
    sensor_type = Column(String(50), nullable=False) # Consider Enum type if DB supports / desired
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    quality = Column(Float, default=1.0)
    metadata = Column(JSONB, nullable=True) # Changed to nullable=True for flexibility

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # For TimescaleDB - this assumes sqlalchemy-timescaledb is available or similar utility
    # If not, this will be a standard SQLAlchemy __table_args__ and TimescaleDB needs to be setup manually or via Alembic.
    __table_args__ = (
        {"timescaledb_hypertable": {'time_column_name': 'timestamp'}},
        # Example of a composite index (if needed):
        # Index('ix_sensor_readings_sensor_id_timestamp', 'sensor_id', 'timestamp', unique=False),
    )
    # If sqlalchemy-timescaledb is not used, comment out the timescaledb_hypertable part
    # and add a comment: # Manual TimescaleDB: Run `SELECT create_hypertable('sensor_readings', 'timestamp');`

class AnomalyAlertORM(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sensor_id = Column(String(255), index=True, nullable=False) # Could be a FK to a SensorORM if sensors are registered
    # sensor_reading_id = Column(Integer, ForeignKey('sensor_readings.id'), nullable=True) # Optional FK to specific reading
    
    anomaly_type = Column(String(100), nullable=False)
    severity = Column(Integer, nullable=False) # ge=1, le=5 (validation at app level)
    confidence = Column(Float, nullable=True) # ge=0, le=1 (validation at app level)
    description = Column(Text, nullable=True)
    evidence = Column(JSONB, nullable=True)
    recommended_actions = Column(ARRAY(String), nullable=True, default=[]) # Ensure default is a list
    status = Column(String(50), default="open", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # sensor_reading = relationship("SensorReadingORM") # If FK is setup

class MaintenanceTaskORM(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # anomaly_alert_id = Column(UUID(as_uuid=True), ForeignKey('anomaly_alerts.id'), nullable=True) # Optional FK

    equipment_id = Column(String(255), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=3, nullable=False) # ge=1, le=5 (validation at app level)
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # anomaly_alert = relationship("AnomalyAlertORM") # If FK is setup

# Placeholder for a potential Sensor Hardware/Asset table
# class SensorORM(Base):
#    __tablename__ = "sensors"
#    id = Column(String(255), primary_key=True, index=True) # sensor_id from readings
#    type = Column(String(50))
#    location = Column(String(255))
#    installed_at = Column(DateTime(timezone=True))
#    # ... other relevant sensor metadata
