import uuid
import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Security
from apps.api.dependencies import api_key_auth # Updated to use api_key_auth
from data.schemas import SensorReadingCreate
from core.events.event_models import SensorDataReceivedEvent
from core.events.event_bus import EventBus
from core.redis_client import get_redis_client, RedisClient

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest", status_code=200, dependencies=[Security(api_key_auth, scopes=["data:ingest"])])
async def ingest_sensor_data(
    reading: SensorReadingCreate,
    request: Request,
):
    """
    Ingests a single sensor data reading and publishes it to the event bus.
    
    Uses Redis for distributed idempotency checking to prevent duplicate processing
    in multi-replica deployments.

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
              
              For new requests:
              ```json
              {
                  "status": "event_published",
                  "event_id": "some-uuid",
                  "correlation_id": "some-uuid",
                  "sensor_id": "sensor_123"
              }
              ```
              
              For duplicate requests (same Idempotency-Key):
              ```json
              {
                  "status": "duplicate_ignored",
                  "event_id": "original-uuid",
                  "correlation_id": "some-uuid",
                  "sensor_id": "sensor_123"
              }
              ```

    Raises:
        HTTPException:
            - 500: If the system coordinator or event bus is not available.
            - 500: If there's an error publishing the event to the event bus.
            - 503: If Redis is unavailable (falls back to graceful degradation).
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

    # Handle Idempotency-Key using Redis for distributed idempotency
    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        try:
            redis_client = await get_redis_client()
            
            # Generate event_id early for idempotency check
            event_id = str(uuid.uuid4())
            
            # Atomic check and set with 10-minute TTL
            is_new, existing_event_id = await redis_client.check_idempotency(
                idempotency_key=idem_key,
                value=event_id,
                ttl_seconds=600  # 10 minutes
            )
            
            if not is_new:
                # Duplicate request - return cached response
                logger.info(f"Duplicate request detected for idempotency key: {idem_key}")
                return {
                    "status": "duplicate_ignored",
                    "event_id": existing_event_id,
                    "correlation_id": str(reading.correlation_id),
                    "sensor_id": reading.sensor_id,
                }
            
            # New request - proceed with event creation using pre-generated ID
            event = SensorDataReceivedEvent(
                raw_data=reading.dict(), # Send the whole reading as raw_data
                sensor_id=reading.sensor_id,
                correlation_id=str(reading.correlation_id) # Ensure correlation_id is a string for the event
            )
            # Override the auto-generated event_id with our pre-generated one
            event.event_id = uuid.UUID(event_id)
            
        except Exception as e:
            # Redis unavailable - log and continue without idempotency check
            logger.warning(f"Redis unavailable for idempotency check: {e}. Proceeding without duplicate protection.")
            
            event = SensorDataReceivedEvent(
                raw_data=reading.dict(),
                sensor_id=reading.sensor_id,
                correlation_id=str(reading.correlation_id)
            )
    else:
        # No idempotency key provided - create event normally
        event = SensorDataReceivedEvent(
            raw_data=reading.dict(),
            sensor_id=reading.sensor_id,
            correlation_id=str(reading.correlation_id)
        )

    # Publish event to the event bus
    try:
        await event_bus.publish(event)
        logger.info(f"Successfully published event {event.event_id} for sensor {reading.sensor_id}")
        
        return {
            "status": "event_published",
            "event_id": str(event.event_id),
            "correlation_id": str(reading.correlation_id),
            "sensor_id": reading.sensor_id
        }
    except Exception as e:
        # Log the exception details here if logging is set up
        logger.error(f"Failed to publish event for sensor {reading.sensor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")
