from fastapi import APIRouter, Request, HTTPException, Depends
from smart_maintenance_saas.apps.api.dependencies import get_api_key
from smart_maintenance_saas.data.schemas import DecisionResponse
from smart_maintenance_saas.core.events.event_models import HumanDecisionResponseEvent
from smart_maintenance_saas.core.event_bus.event_bus import EventBus

router = APIRouter()

@router.post("/decisions/respond", status_code=200, dependencies=[Depends(get_api_key)])
async def respond_to_decision_request(
    decision_response: DecisionResponse,
    request: Request,
):
    """
    Accepts a human decision response and publishes it to the event bus.
    """
    event_bus: EventBus = request.app.state.event_bus

    if not event_bus:
        raise HTTPException(status_code=500, detail="Event bus not available")

    event = HumanDecisionResponseEvent(
        payload=decision_response, # The HumanDecisionResponseEvent expects the DecisionResponse schema as payload
        correlation_id=decision_response.correlation_id # Pass correlation_id if available in DecisionResponse
    )

    try:
        await event_bus.publish(event)
        return {
            "status": "success",
            "event_id": str(event.event_id),
            "request_id": decision_response.request_id
        }
    except Exception as e:
        # Log the exception details here if logging is set up
        raise HTTPException(status_code=500, detail=f"Failed to publish human decision event: {str(e)}")
