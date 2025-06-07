from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseEventModel(BaseModel):
    """
    Base model for all events, providing common fields.

    Attributes:
        timestamp: The time the event was created. Defaults to the current UTC time.
        event_id: A unique identifier for the event. Defaults to a new UUID4.
        correlation_id: An optional ID to correlate related events.
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of when the event was created.",
    )
    event_id: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the event."
    )
    correlation_id: Optional[str] = Field(
        default=None, description="Optional ID to correlate related events."
    )

    class Config:
        """Pydantic configuration options."""

        arbitrary_types_allowed = True  # Allows for types like UUID.
        json_encoders = {
            # Handles UUID serialization to string for JSON
            UUID: lambda v: str(v),
            # Handles datetime serialization to ISO format string
            datetime: lambda v: v.isoformat(),
        }


class SensorDataReceivedEvent(BaseEventModel):
    """
    Event indicating that raw data has been received from a sensor.

    Attributes:
        raw_data: The raw data payload from the sensor.
        source_topic: The topic or channel from which the data was received (e.g., MQTT topic).
        sensor_id: An identifier for the sensor that produced the data.
    """

    raw_data: Dict[str, Any] = Field(
        ..., description="The raw data payload from the sensor."
    )
    source_topic: Optional[str] = Field(
        default=None,
        description="The topic or channel from which the data was received.",
    )
    sensor_id: Optional[str] = Field(
        default=None, description="Identifier for the sensor that produced the data."
    )


class DataProcessedEvent(BaseEventModel):
    """
    Event indicating that sensor data has been processed.

    Attributes:
        processed_data: The processed data, typically a structured representation.
                        (Future: from core.database.models import SensorReading)
        original_event_id: The ID of the event that triggered this processing (e.g., SensorDataReceivedEvent).
        source_sensor_id: The identifier of the sensor whose data was processed.
    """

    processed_data: Any = Field(
        ...,
        description="The processed data. Placeholder for a specific model like SensorReading.",
    )
    # Future type: from core.database.models import SensorReading
    original_event_id: Optional[UUID] = Field(
        default=None, description="ID of the event that triggered this processing."
    )
    source_sensor_id: Optional[str] = Field(
        default=None, description="Identifier of the sensor whose data was processed."
    )


class AnomalyDetectedEvent(BaseEventModel):
    """
    Event indicating that an anomaly has been detected in the data.

    Attributes:
        anomaly_details: Details about the detected anomaly.
                         (Future: from core.database.models import AnomalyAlert)
        triggering_data: The data that triggered the anomaly detection.
                         (Future: from core.database.models import SensorReading)
        severity: The severity of the detected anomaly (e.g., "low", "medium", "high").
    """

    anomaly_details: Any = Field(
        ...,
        description="Details about the detected anomaly. Placeholder for AnomalyAlert model.",
    )
    # Future type: from core.database.models import AnomalyAlert
    triggering_data: Any = Field(
        ...,
        description="The data that triggered the anomaly. Placeholder for SensorReading model.",
    )
    # Future type: from core.database.models import SensorReading
    severity: str = Field(
        default="medium",
        description="Severity of the anomaly (e.g., 'low', 'medium', 'high').",
    )


class AgentStatusUpdateEvent(BaseEventModel):
    """
    Event representing a status update from an agent.

    Attributes:
        agent_id: The unique identifier of the agent.
        status: The current status of the agent (e.g., "running", "stopped", "error").
        message: An optional message providing more details about the status.
        capabilities: A list of dictionaries representing the agent's capabilities.
                      This is a simplified representation for serialization.
                      (Corresponds to List[AgentCapability] from apps.agents.base_agent)
    """

    agent_id: str = Field(..., description="Unique identifier of the agent.")
    status: str = Field(..., description="Current status of the agent.")
    message: Optional[str] = Field(
        default=None,
        description="Optional message providing more details about the status.",
    )
    capabilities: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Agent's capabilities, represented as a list of dictionaries.",
    )


class DataProcessingFailedEvent(BaseEventModel):
    """
    Event indicating that an error occurred during data processing.

    Attributes:
        agent_id: The identifier of the agent that was attempting to process the data.
        error_message: A message describing the error that occurred.
        original_event_payload: The payload of the event that the agent was trying to process.
                                This can be useful for debugging.
    """

    agent_id: str = Field(
        ..., description="Identifier of the agent that encountered the error."
    )
    error_message: str = Field(
        ..., description="Details of the error that occurred during processing."
    )
    original_event_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The original event payload that led to the processing failure.",
    )


class AnomalyValidatedEvent(BaseEventModel):
    """
    Event indicating that an anomaly has been validated by the ValidationAgent.

    Attributes:
        original_anomaly_alert_payload: The original anomaly alert data.
        triggering_reading_payload: The sensor reading data that triggered the anomaly.
        validation_status: Status of validation ("CONFIRMED", "FALSE_POSITIVE", "UNCERTAIN").
        final_confidence: Final confidence score after validation (0.0 to 1.0).
        validation_reasons: List of reasons explaining the validation decision.
        validated_at: Timestamp when validation was performed.
        agent_id: ID of the validation agent that processed this event.
    """

    original_anomaly_alert_payload: Dict[str, Any] = Field(
        ..., description="Original anomaly alert data that was validated."
    )
    triggering_reading_payload: Dict[str, Any] = Field(
        ..., description="Sensor reading data that triggered the anomaly detection."
    )
    validation_status: str = Field(
        ..., description="Validation status: CONFIRMED, FALSE_POSITIVE, or UNCERTAIN."
    )
    final_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Final confidence score after validation (0.0 to 1.0)."
    )
    validation_reasons: List[str] = Field(
        default_factory=list, description="List of reasons for the validation decision."
    )
    validated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the validation was performed.",
    )
    agent_id: str = Field(
        ..., description="ID of the validation agent that processed this event."
    )


class MaintenancePredictedEvent(BaseEventModel):
    """
    Event indicating that a maintenance prediction has been generated for equipment/component.
    
    This event is published by the PredictionAgent after analyzing historical data
    and generating time-to-failure predictions using Prophet or other ML models.

    Attributes:
        original_anomaly_event_id: Reference to the AnomalyValidatedEvent that triggered this prediction.
        equipment_id: Identifier of the equipment/component for which prediction is made.
        predicted_failure_date: Predicted date/time when maintenance will be needed.
        confidence_interval_lower: Lower bound of the prediction confidence interval.
        confidence_interval_upper: Upper bound of the prediction confidence interval.
        prediction_confidence: Overall confidence in the prediction (0.0 to 1.0).
        time_to_failure_days: Number of days until predicted failure/maintenance need.
        maintenance_type: Type of maintenance predicted (e.g., "preventive", "corrective", "inspection").
        prediction_method: Method used for prediction (e.g., "prophet", "linear_regression", "arima").
        historical_data_points: Number of historical data points used in the prediction.
        model_metrics: Dictionary containing model performance metrics (e.g., MAE, RMSE).
        recommended_actions: List of recommended maintenance actions.
        agent_id: ID of the prediction agent that generated this event.
    """

    original_anomaly_event_id: UUID = Field(
        ..., description="Reference to the AnomalyValidatedEvent that triggered this prediction."
    )
    equipment_id: str = Field(
        ..., description="Identifier of the equipment/component for which prediction is made."
    )
    predicted_failure_date: datetime = Field(
        ..., description="Predicted date/time when maintenance will be needed."
    )
    confidence_interval_lower: datetime = Field(
        ..., description="Lower bound of the prediction confidence interval."
    )
    confidence_interval_upper: datetime = Field(
        ..., description="Upper bound of the prediction confidence interval."
    )
    prediction_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence in the prediction (0.0 to 1.0)."
    )
    time_to_failure_days: float = Field(
        ..., ge=0.0, description="Number of days until predicted failure/maintenance need."
    )
    maintenance_type: str = Field(
        default="preventive", description="Type of maintenance predicted (e.g., 'preventive', 'corrective', 'inspection')."
    )
    prediction_method: str = Field(
        default="prophet", description="Method used for prediction (e.g., 'prophet', 'linear_regression', 'arima')."
    )
    historical_data_points: int = Field(
        ..., ge=0, description="Number of historical data points used in the prediction."
    )
    model_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Dictionary containing model performance metrics (e.g., MAE, RMSE)."
    )
    recommended_actions: List[str] = Field(
        default_factory=list, description="List of recommended maintenance actions."
    )
    agent_id: str = Field(
        ..., description="ID of the prediction agent that generated this event."
    )


class MaintenanceScheduledEvent(BaseEventModel):
    """
    Event indicating that a maintenance task has been scheduled by the SchedulingAgent.
    
    This event is published after the SchedulingAgent successfully schedules maintenance
    based on predictions from the PredictionAgent.

    Attributes:
        original_prediction_event_id: Reference to the MaintenancePredictedEvent that triggered this scheduling.
        schedule_details: Complete details of the optimized schedule.
        equipment_id: Identifier of the equipment/component that was scheduled for maintenance.
        assigned_technician_id: ID of the technician assigned to the maintenance task.
        scheduled_start_time: When the maintenance is scheduled to start.
        scheduled_end_time: When the maintenance is scheduled to end.
        scheduling_method: Method used for scheduling (e.g., "greedy", "or_tools", "manual").
        optimization_score: Quality score of the scheduling solution (0.0 to 1.0).
        constraints_satisfied: List of constraints that were satisfied during scheduling.
        constraints_violated: List of constraints that were violated during scheduling.
        agent_id: ID of the scheduling agent that generated this event.
    """

    original_prediction_event_id: UUID = Field(
        ..., description="Reference to the MaintenancePredictedEvent that triggered this scheduling."
    )
    schedule_details: Dict[str, Any] = Field(
        ..., description="Complete details of the optimized schedule (OptimizedSchedule model serialized)."
    )
    equipment_id: str = Field(
        ..., description="Identifier of the equipment/component that was scheduled for maintenance."
    )
    assigned_technician_id: Optional[str] = Field(
        None, description="ID of the technician assigned to the maintenance task."
    )
    scheduled_start_time: Optional[datetime] = Field(
        None, description="When the maintenance is scheduled to start."
    )
    scheduled_end_time: Optional[datetime] = Field(
        None, description="When the maintenance is scheduled to end."
    )
    scheduling_method: str = Field(
        default="greedy", description="Method used for scheduling (e.g., 'greedy', 'or_tools', 'manual')."
    )
    optimization_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Quality score of the scheduling solution (0.0 to 1.0)."
    )
    constraints_satisfied: List[str] = Field(
        default_factory=list, description="List of constraints that were satisfied during scheduling."
    )
    constraints_violated: List[str] = Field(
        default_factory=list, description="List of constraints that were violated during scheduling."
    )
    agent_id: str = Field(
        ..., description="ID of the scheduling agent that generated this event."
    )


class SystemFeedbackReceivedEvent(BaseEventModel):
    """
    Event indicating that system feedback has been received and needs to be processed by the Learning Agent.
    
    This event is published when the system receives feedback that should be stored
    in the knowledge base for future retrieval and learning purposes.

    Attributes:
        feedback_payload: The feedback data to be processed and stored.
        source_agent_id: Optional ID of the agent that generated or forwarded this feedback.
        processing_priority: Priority level for processing this feedback (1=highest, 5=lowest).
    """

    feedback_payload: Dict[str, Any] = Field(
        ..., description="The feedback data payload (FeedbackData model serialized)."
    )
    source_agent_id: Optional[str] = Field(
        None, description="ID of the agent that generated or forwarded this feedback."
    )
    processing_priority: int = Field(
        default=3, ge=1, le=5, description="Priority level for processing (1=highest, 5=lowest)."
    )


class HumanDecisionRequiredEvent(BaseEventModel):
    """
    Event indicating that a human decision is required.

    Attributes:
        payload: The decision request containing all necessary information for the human operator.
    """
    
    payload: Any = Field(
        ...,
        description="DecisionRequest object containing details about the required decision."
    )


class HumanDecisionResponseEvent(BaseEventModel):
    """
    Event indicating that a human has made a decision.

    Attributes:
        payload: The decision response containing the human's choice and justification.
    """
    
    payload: Any = Field(
        ...,
        description="DecisionResponse object containing the human's decision and details."
    )


class ScheduleMaintenanceCommand(BaseEventModel):
    """
    Command event to trigger maintenance scheduling.
    
    This event is published by the OrchestratorAgent when a maintenance task
    needs to be scheduled, either automatically or after human approval.
    
    Attributes:
        maintenance_data: Data about the maintenance that needs to be scheduled.
        urgency_level: Level of urgency (low, medium, high, critical).
        auto_approved: Whether this maintenance was auto-approved or went through human review.
        source_prediction_event_id: ID of the original MaintenancePredictedEvent that triggered this.
    """
    
    maintenance_data: Dict[str, Any] = Field(
        ...,
        description="Data about the maintenance task to be scheduled."
    )
    urgency_level: str = Field(
        default="medium",
        description="Urgency level: low, medium, high, critical."
    )
    auto_approved: bool = Field(
        default=False,
        description="Whether this maintenance was automatically approved."
    )
    source_prediction_event_id: Optional[str] = Field(
        None,
        description="ID of the MaintenancePredictedEvent that triggered this command."
    )


# Example of how to use these models (for testing purposes, can be removed or commented out):
# if __name__ == "__main__":
#     sensor_event = SensorDataReceivedEvent(
#         raw_data={"temperature": 25.5, "humidity": 60},
#         sensor_id="sensor-001",
#         source_topic="sensors/livingroom/temp_humidity"
#     )
#     print("Sensor Event:", sensor_event.json(indent=2))
#
#     processed_event = DataProcessedEvent(
#         processed_data={"temp_celsius": 25.5, "humidity_percent": 60.0, "unit": "metric"},
#         original_event_id=sensor_event.event_id,
#         source_sensor_id="sensor-001",
#         correlation_id=sensor_event.correlation_id
#     )
#     print("\nProcessed Event:", processed_event.json(indent=2))
#
#     anomaly_event = AnomalyDetectedEvent(
#         anomaly_details={"type": "high_temperature", "threshold": 30.0, "value": 31.5},
#         triggering_data=processed_event.processed_data,
#         severity="high",
#         correlation_id=sensor_event.correlation_id
#     )
#     print("\nAnomaly Event:", anomaly_event.json(indent=2))
#
#     status_event = AgentStatusUpdateEvent(
#         agent_id="data_processing_agent_1",
#         status="running",
#         capabilities=[
#             {"name": "process_temp", "input_types": ["raw_temp"], "output_types": ["celsius"]},
#             {"name": "detect_humidity_anomaly", "input_types": ["humidity"], "output_types": ["alert"]}
#         ]
#     )
#     print("\nAgent Status Event:", status_event.json(indent=2))
#
#     # Test base model defaults
#     base_ev = BaseEventModel()
#     print("\nBase Event (for checking defaults):", base_ev.json(indent=2))
