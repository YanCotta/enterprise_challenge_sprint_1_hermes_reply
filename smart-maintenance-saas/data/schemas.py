# This file will contain Pydantic schemas for data validation and serialization.
# For example, sensor data schemas, asset information schemas, etc.

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union  # Ensure Any is imported

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
    timestamp: Optional[datetime] = Field(
        None, description="UTC timestamp of the reading"
    )
    sensor_type: Optional[SensorType] = Field(None, description="Type of the sensor")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    quality: float = Field(default=1.0, ge=0, le=1, description="Data quality score")
    correlation_id: Optional[uuid.UUID] = Field(
        None, description="Correlation ID for tracking"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat(), uuid.UUID: str}


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
        description="UTC timestamp when the reading was ingested",
    )

    class Config:
        from_attributes = True  # For Pydantic v2 ORM mode
        json_encoders = {datetime: lambda dt: dt.isoformat(), uuid.UUID: str}


class DataQuality(str, Enum):
    """Enum for data quality levels."""

    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"


class SensorReadingBase(BaseModel):
    """Base model for a single sensor reading."""

    sensor_id: str = Field(..., description="Unique identifier for the sensor.")
    sensor_type: SensorType = Field(..., description="Type of the sensor.")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the reading (UTC)."
    )
    value: Union[float, int, str, bool, Dict, List] = Field(
        ..., description="The actual sensor value."
    )
    unit: Optional[str] = Field(
        None,
        description="Unit of measurement for the sensor value (e.g., °C, %, mm/s).",
    )

    quality: DataQuality = Field(
        DataQuality.GOOD, description="Quality of the sensor reading."
    )
    sensor_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata for the reading."
    )  # Changed 'any' to 'Any'

    @validator("timestamp", pre=True, always=True)
    def ensure_utc_timestamp(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            return v.replace(tzinfo=datetime.timezone.utc)
        return v.astimezone(datetime.timezone.utc)


# (SensorType, SensorReading, AnomalyAlert, MaintenanceTask should already be in this file)

# Note: The original SensorReading that inherited SensorReadingBase is now replaced by the one above.
# This SensorReadingBase and SensorReadingCreate might need adjustments
# if they were intended to be used with the new SensorReading model.
# For now, they are left as is, as per the focused nature of the subtask.

class ValidationStatus(str, Enum):
    CREDIBLE_ANOMALY = "credible_anomaly"
    FALSE_POSITIVE_SUSPECTED = "false_positive_suspected"
    FURTHER_INVESTIGATION_NEEDED = "further_investigation_needed"

class AnomalyType(str, Enum):
    SPIKE = "spike"
    DRIFT = "drift"
    STUCK_AT_VALUE = "stuck_at_value"
    LOW_VALUE = "low_value"
    # For more dynamic descriptions from AnomalyDetectionAgent,
    # they might remain strings or a more generic "OTHER" type could be added.
    # For now, sticking to the primary examples.
    ENSEMBLE_IF_STATISTICAL = "ensemble_anomaly_if_and_statistical" # Example for combined types
    ISOLATION_FOREST = "isolation_forest_anomaly"
    STATISTICAL_Z_SCORE = "statistical_z_score_violation" # Example for specific stat violation
    STATISTICAL_THRESHOLD = "statistical_threshold_violation" # Example for specific stat violation
    TEMPERATURE_SPIKE = "temperature_spike"  # Specific temperature anomaly type
    UNKNOWN = "unknown_anomaly_type"
    OTHER = "other_type"


class AnomalyStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AnomalyDetectionParameters(BaseModel):
    """Parameters for configuring anomaly detection for a sensor."""

    sensor_id: str
    method: str  # e.g., "threshold", "z_score", "ewma"
    parameters: Dict[str, Any]  # Changed 'any' to 'Any'


class AnomalyAlert(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    sensor_id: str
    anomaly_type: AnomalyType = Field(default=AnomalyType.UNKNOWN, description="Type of anomaly detected")
    severity: int = Field(ge=1, le=5)  # 1 (low) to 5 (critical)
    confidence: float = Field(ge=0, le=1)  # Confidence in the anomaly detection
    description: str
    evidence: Dict[str, Any] = Field(
        default_factory=dict
    )  # e.g., {"current_value": 105.5, "baseline": 70.0}
    recommended_actions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: AnomalyStatus = Field(default=AnomalyStatus.OPEN, description="Status of the anomaly alert")

    class Config:
        from_attributes = True  # For Pydantic v2 ORM mode
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
    description: Optional[str] = None  # Optional field for more details
    priority: int = Field(default=3, ge=1, le=5)  # 1 (highest) to 5 (lowest)
    status: MaintenanceTaskStatus = Field(
        default=MaintenanceTaskStatus.PENDING,
        description="Current status of the maintenance task",
    )
    estimated_duration_hours: Optional[float] = None
    actual_duration_hours: Optional[float] = None
    required_skills: List[str] = Field(
        default_factory=list
    )  # e.g., ["electrical", "mechanical"]
    parts_needed: List[str] = Field(
        default_factory=list
    )  # e.g., ["part_xyz_123", "filter_abc_789"]
    assigned_technician_id: Optional[str] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None  # To be updated by the application logic

    class Config:
        from_attributes = True  # For Pydantic v2 ORM mode
        use_enum_values = True


class AssetInformation(BaseModel):
    """Schema for asset information."""

    asset_id: str = Field(..., description="Unique identifier for the asset.")
    name: str = Field(..., description="Name of the asset.")
    asset_type: str = Field(
        ..., description="Type of the asset (e.g., 'Pump', 'Motor', 'HVAC Unit')."
    )
    location: Optional[str] = Field(None, description="Location of the asset.")
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the asset.")
    model_number: Optional[str] = Field(None, description="Model number of the asset.")
    installation_date: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    operational_status: str = Field(
        "active",
        description="Operational status (e.g., 'active', 'inactive', 'under_maintenance').",
    )
    specifications: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Technical specifications."
    )  # Changed 'any' to 'Any'

    class Config:
        from_attributes = True


# Example of a more complex schema that might be used for API responses or data aggregation
class SensorDataSummary(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    reading_count: int
    last_reading_timestamp: Optional[datetime]
    average_value: Optional[float]  # Meaningful only for numeric types
    min_value: Optional[float]  # Meaningful only for numeric types
    max_value: Optional[float]  # Meaningful only for numeric types

    class Config:
        use_enum_values = True


# Further schemas can be added here as the application evolves, for example:
# - User schemas
# - Alert schemas
# - Predictive maintenance model input/output schemas
# - Configuration schemas for different system components


class NotificationChannel(str, Enum):
    """Supported notification channels."""

    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    CONSOLE = "console"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationRequest(BaseModel):
    """Schema for a notification request."""

    id: str = Field(..., description="Unique identifier for the notification request")
    recipient: str = Field(..., description="Recipient identifier (email, phone, etc.)")
    channel: NotificationChannel = Field(..., description="Notification channel to use")
    subject: str = Field(..., description="Notification subject/title")
    message: str = Field(..., description="Notification message content")
    priority: int = Field(default=3, ge=1, le=5, description="Priority level (1=highest, 5=lowest)")
    template_id: Optional[str] = Field(None, description="Template identifier if using templates")
    template_data: Dict[str, Any] = Field(default_factory=dict, description="Data for template rendering")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class NotificationStatus(str, Enum):
    """Status of a notification delivery."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationResult(BaseModel):
    """Schema for notification delivery result."""

    request_id: str = Field(..., description="Reference to the NotificationRequest ID")
    status: NotificationStatus = Field(..., description="Delivery status")
    channel_used: NotificationChannel = Field(..., description="Channel used for delivery")
    sent_at: Optional[datetime] = Field(None, description="When the notification was sent")
    delivered_at: Optional[datetime] = Field(None, description="When the notification was delivered")
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")
    provider_response: Dict[str, Any] = Field(default_factory=dict, description="Response from the notification provider")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class MaintenanceRequest(BaseModel):
    """Schema for a maintenance request generated from predictions."""

    id: str = Field(..., description="Unique identifier for the maintenance request")
    equipment_id: str = Field(..., description="Equipment/component identifier requiring maintenance")
    maintenance_type: str = Field(..., description="Type of maintenance needed")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1=highest, 5=lowest)")
    estimated_duration_hours: float = Field(..., gt=0, description="Estimated duration in hours")
    required_skills: List[str] = Field(default_factory=list, description="Required technician skills")
    preferred_time_window_start: Optional[datetime] = Field(None, description="Preferred start time")
    preferred_time_window_end: Optional[datetime] = Field(None, description="Preferred end time")
    deadline: Optional[datetime] = Field(None, description="Hard deadline for completion")
    parts_needed: List[str] = Field(default_factory=list, description="Required parts/materials")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class ScheduleStatus(str, Enum):
    """Status of a maintenance schedule."""

    SCHEDULED = "Scheduled"
    FAILED_TO_SCHEDULE = "Failed_To_Schedule"
    PENDING = "Pending"
    CANCELLED = "Cancelled"


class OptimizedSchedule(BaseModel):
    """Schema for an optimized maintenance schedule."""

    request_id: str = Field(..., description="Reference to the MaintenanceRequest ID")
    status: ScheduleStatus = Field(..., description="Status of the scheduling attempt")
    assigned_technician_id: Optional[str] = Field(None, description="ID of assigned technician")
    scheduled_start_time: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end_time: Optional[datetime] = Field(None, description="Scheduled end time")
    optimization_score: Optional[float] = Field(None, ge=0, le=1, description="Quality score of the schedule")
    constraints_satisfied: List[str] = Field(default_factory=list, description="List of satisfied constraints")
    constraints_violated: List[str] = Field(default_factory=list, description="List of violated constraints")
    alternative_slots: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative time slots if available")
    scheduling_notes: Optional[str] = Field(None, description="Additional scheduling notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# =============================================================================
# REPORTING MODELS
# =============================================================================

class ReportRequest(BaseModel):
    """Schema for requesting a report generation."""

    report_id: Optional[str] = Field(None, description="Optional report identifier")
    report_type: str = Field(..., description="Type of report to generate")
    format: str = Field(default="json", description="Output format (json/text)")
    time_range_start: Optional[datetime] = Field(None, description="Start time for report data")
    time_range_end: Optional[datetime] = Field(None, description="End time for report data")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional report parameters")
    include_charts: bool = Field(default=True, description="Whether to include charts in the report")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class ReportResult(BaseModel):
    """Schema for report generation results."""

    report_id: str = Field(..., description="Unique report identifier")
    report_type: str = Field(..., description="Type of report generated")
    format: str = Field(..., description="Output format (json/text)")
    content: str = Field(..., description="Report content in the requested format")
    generated_at: datetime = Field(..., description="UTC timestamp when report was generated")
    charts_encoded: Dict[str, str] = Field(default_factory=dict, description="Base64 encoded charts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional report metadata")
    error_message: Optional[str] = Field(None, description="Error message if report generation failed")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# =============================================================================
# LEARNING AGENT MODELS
# =============================================================================

class FeedbackData(BaseModel):
    """Schema for feedback data to be processed by the Learning Agent."""

    feedback_id: str = Field(..., description="Unique identifier for the feedback")
    feedback_text: str = Field(..., description="The textual content of the feedback")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the feedback was received")
    source: Optional[str] = Field(None, description="Source of the feedback (e.g., 'user', 'system', 'agent')")
    category: Optional[str] = Field(None, description="Category of feedback (e.g., 'maintenance', 'anomaly', 'prediction')")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the feedback")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class KnowledgeItem(BaseModel):
    """Schema for a knowledge item retrieved from the RAG system."""

    id: str = Field(..., description="Unique identifier for the knowledge item")
    description: str = Field(..., description="The textual content/description of the knowledge")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with the knowledge item")
    similarity_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Similarity score for retrieval relevance (cosine similarity can be negative)")
    created_at: Optional[datetime] = Field(None, description="When this knowledge was added")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class LearningResult(BaseModel):
    """Schema for the result of a learning operation."""

    knowledge_updated: bool = Field(..., description="Whether the knowledge base was successfully updated")
    knowledge_id: Optional[str] = Field(None, description="ID of the added/updated knowledge item")
    error_message: Optional[str] = Field(None, description="Error message if the operation failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the learning operation")


# Human Interface Agent Models
class DecisionType(str, Enum):
    """Enumeration of different types of decisions that can be requested from humans."""
    MAINTENANCE_APPROVAL = "maintenance_approval"
    EMERGENCY_RESPONSE = "emergency_response"
    BUDGET_APPROVAL = "budget_approval"
    SCHEDULE_CHANGE = "schedule_change"
    QUALITY_INSPECTION = "quality_inspection"


class DecisionRequest(BaseModel):
    """
    Schema for requesting a decision from a human operator.
    """
    request_id: str = Field(..., description="Unique identifier for the decision request")
    decision_type: DecisionType = Field(..., description="Type of decision being requested")
    context: Dict[str, Any] = Field(..., description="Context information for the decision")
    options: List[str] = Field(..., description="Available decision options")
    priority: str = Field(default="medium", description="Priority level (low, medium, high, critical)")
    requester_agent_id: str = Field(..., description="ID of the agent requesting the decision")
    deadline: Optional[datetime] = Field(None, description="Optional deadline for the decision")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class DecisionResponse(BaseModel):
    """
    Schema for a human decision response.
    """
    request_id: str = Field(..., description="ID of the original decision request")
    decision: str = Field(..., description="The chosen decision")
    justification: Optional[str] = Field(None, description="Optional explanation for the decision")
    operator_id: str = Field(..., description="ID of the human operator who made the decision")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the decision was made")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Confidence level in the decision")
    additional_notes: Optional[str] = Field(None, description="Any additional notes or comments")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# Orchestrator Agent Models
class WorkflowStep(BaseModel):
    """
    Schema for tracking workflow steps in the orchestrator.
    """
    step_id: str = Field(..., description="Unique identifier for the workflow step")
    step_name: str = Field(..., description="Name of the workflow step")
    agent_id: Optional[str] = Field(None, description="ID of the agent handling this step")
    status: str = Field(default="pending", description="Status of the step (pending, in_progress, completed, failed)")
    started_at: Optional[datetime] = Field(None, description="When the step was started")
    completed_at: Optional[datetime] = Field(None, description="When the step was completed")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the step")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Output data from the step")
    error_message: Optional[str] = Field(None, description="Error message if the step failed")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class DecisionLog(BaseModel):
    """
    Schema for logging decisions made by the orchestrator.
    """
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the decision")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the decision was made")
    decision_type: str = Field(..., description="Type of decision made")
    trigger_event: str = Field(..., description="Event that triggered the decision")
    decision_rationale: str = Field(..., description="Reasoning behind the decision")
    action_taken: str = Field(..., description="Action taken as a result of the decision")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Context data used in decision making")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class SystemState(BaseModel):
    """
    Schema for representing system state in the orchestrator.
    Simple Dict-based implementation as suggested in the plan.
    """
    state_data: Dict[str, Any] = Field(default_factory=dict, description="Dictionary containing system state information")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When the state was last updated")
    version: int = Field(default=1, description="Version number for state tracking")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# Maintenance Log schemas

class MaintenanceLogCreate(BaseModel):
    """
    Schema for creating a new maintenance log entry.
    """
    
    task_id: uuid.UUID = Field(..., description="Unique identifier of the maintenance task")
    equipment_id: str = Field(..., description="Identifier of the equipment that was maintained")
    completion_date: datetime = Field(..., description="Date and time when the maintenance was completed")
    technician_id: str = Field(..., description="Identifier of the technician who completed the task")
    notes: Optional[str] = Field(default=None, description="Optional notes about the maintenance completion")
    status: MaintenanceTaskStatus = Field(
        default=MaintenanceTaskStatus.COMPLETED, 
        description="Completion status of the maintenance task"
    )
    actual_duration_hours: Optional[float] = Field(
        default=None, 
        description="Actual time taken to complete the task in hours"
    )

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat(), uuid.UUID: str}


class MaintenanceLog(MaintenanceLogCreate):
    """
    Schema for a complete maintenance log, including database fields.
    """
    
    id: uuid.UUID = Field(..., description="Unique identifier for the maintenance log")
    created_at: datetime = Field(..., description="When the log entry was created")
    updated_at: datetime = Field(..., description="When the log entry was last updated")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat(), uuid.UUID: str}
        from_attributes = True  # For SQLAlchemy ORM compatibility


# =============================================================================
# HEALTH CHECK MODELS
# =============================================================================

class HealthStatus(BaseModel):
    """Schema for health check response."""
    
    status: str = Field(..., description="Overall health status (ok, degraded, failed)")
    database: str = Field(..., description="Database connection status (ok, failed)")
    redis: str = Field(..., description="Redis connection status (ok, failed)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp of health check")


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
