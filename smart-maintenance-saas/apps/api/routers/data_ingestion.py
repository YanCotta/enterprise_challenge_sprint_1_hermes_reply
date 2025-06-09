import uuid
from fastapi import APIRouter, Request, HTTPException, Depends, Security
from apps.api.dependencies import api_key_auth # Updated to use api_key_auth
from data.schemas import SensorReadingCreate
from core.events.event_models import SensorDataReceivedEvent
from core.events.event_bus import EventBus

router = APIRouter()

@router.post("/ingest", status_code=200, dependencies=[Security(api_key_auth, scopes=["data:ingest"])])
async def ingest_sensor_data(
    reading: SensorReadingCreate,
    request: Request,
):
    """
    Ingests a single sensor data reading and publishes it to the event bus.

    This endpoint is secured by an API key.

    Args:
        reading (SensorReadingCreate): The sensor data to ingest. This should conform to
                                       the `SensorReadingCreate` schema, including fields
                                       like `sensor_id`, `value`, `timestamp`, etc.
                                       A `correlation_id` (UUID) can be optionally provided;
                                       if not, one will be generated.
        request (Request): The FastAPI request object, used to access the system coordinator
                           and event bus.

    Returns:
        dict: A confirmation message including the status, event ID of the published
              `SensorDataReceivedEvent`, the `correlation_id` used, and the `sensor_id`.
              Example:
              ```json
              {
                  "status": "event_published",
                  "event_id": "some-uuid",
                  "correlation_id": "some-uuid",
                  "sensor_id": "sensor_123"
              }
              ```

    Raises:
        HTTPException:
            - 500: If the system coordinator or event bus is not available.
            - 500: If there's an error publishing the event to the event bus.
    """
    coordinator = request.app.state.coordinator
    if not coordinator:
        raise HTTPException(status_code=500, detail="System coordinator not available")
    
    event_bus = coordinator.event_bus
    if not event_bus:
        raise HTTPException(status_code=500, detail="Event bus not available")

    # Ensure a correlation_id is present
    if reading.correlation_id is None:
        reading.correlation_id = uuid.uuid4()

    event = SensorDataReceivedEvent(
        raw_data=reading.dict(), # Send the whole reading as raw_data
        sensor_id=reading.sensor_id,
        correlation_id=str(reading.correlation_id) # Ensure correlation_id is a string for the event
    )

    try:
        await event_bus.publish(event)
        return {
            "status": "event_published",
            "event_id": str(event.event_id),
            "correlation_id": str(reading.correlation_id),
            "sensor_id": reading.sensor_id
        }
    except Exception as e:
        # Log the exception details here if logging is set up
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")
