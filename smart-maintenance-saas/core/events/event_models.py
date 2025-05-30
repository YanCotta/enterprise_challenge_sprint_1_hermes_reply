from datetime import datetime
from typing import Optional, List, Any, Dict
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
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the event was created.")
    event_id: UUID = Field(default_factory=uuid4, description="Unique identifier for the event.")
    correlation_id: Optional[str] = Field(default=None, description="Optional ID to correlate related events.")

    class Config:
        """Pydantic configuration options."""
        arbitrary_types_allowed = True # Allows for types like UUID.
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
    raw_data: Dict[str, Any] = Field(..., description="The raw data payload from the sensor.")
    source_topic: Optional[str] = Field(default=None, description="The topic or channel from which the data was received.")
    sensor_id: Optional[str] = Field(default=None, description="Identifier for the sensor that produced the data.")


class DataProcessedEvent(BaseEventModel):
    """
    Event indicating that sensor data has been processed.

    Attributes:
        processed_data: The processed data, typically a structured representation.
                        (Future: from core.database.models import SensorReading)
        original_event_id: The ID of the event that triggered this processing (e.g., SensorDataReceivedEvent).
        source_sensor_id: The identifier of the sensor whose data was processed.
    """
    processed_data: Any = Field(..., description="The processed data. Placeholder for a specific model like SensorReading.")
    # Future type: from core.database.models import SensorReading
    original_event_id: Optional[UUID] = Field(default=None, description="ID of the event that triggered this processing.")
    source_sensor_id: Optional[str] = Field(default=None, description="Identifier of the sensor whose data was processed.")


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
    anomaly_details: Any = Field(..., description="Details about the detected anomaly. Placeholder for AnomalyAlert model.")
    # Future type: from core.database.models import AnomalyAlert
    triggering_data: Any = Field(..., description="The data that triggered the anomaly. Placeholder for SensorReading model.")
    # Future type: from core.database.models import SensorReading
    severity: str = Field(default="medium", description="Severity of the anomaly (e.g., 'low', 'medium', 'high').")


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
    message: Optional[str] = Field(default=None, description="Optional message providing more details about the status.")
    capabilities: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Agent's capabilities, represented as a list of dictionaries."
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
    agent_id: str = Field(..., description="Identifier of the agent that encountered the error.")
    error_message: str = Field(..., description="Details of the error that occurred during processing.")
    original_event_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The original event payload that led to the processing failure."
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
