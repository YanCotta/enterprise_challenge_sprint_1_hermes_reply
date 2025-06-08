import uuid
from fastapi import APIRouter, Request, HTTPException, Depends
from smart_maintenance_saas.apps.api.dependencies import get_api_key
from smart_maintenance_saas.data.schemas import SensorReadingCreate
from smart_maintenance_saas.core.events.event_models import SensorDataReceivedEvent
from smart_maintenance_saas.core.event_bus.event_bus import EventBus

router = APIRouter()

@router.post("/ingest", status_code=200, dependencies=[Depends(get_api_key)])
async def ingest_sensor_data(
    reading: SensorReadingCreate,
    request: Request,
):
    """
    Accepts sensor data readings and publishes them to the event bus.
    """
    event_bus: EventBus = request.app.state.event_bus

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
