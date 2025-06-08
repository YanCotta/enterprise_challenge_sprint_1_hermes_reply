from fastapi import APIRouter, Request, HTTPException, Depends
from apps.api.dependencies import get_api_key
from data.schemas import DecisionResponse
from core.events.event_models import HumanDecisionResponseEvent
from core.events.event_bus import EventBus

router = APIRouter()

@router.post("/submit", status_code=201, dependencies=[Depends(get_api_key)])
async def submit_decision(
    decision_response: DecisionResponse,
    request: Request,
):
    """
    Accepts a human decision response and publishes it to the event bus.
    """
    coordinator = request.app.state.coordinator
    if not coordinator:
        raise HTTPException(status_code=500, detail="System coordinator not available")
    
    event_bus = coordinator.event_bus
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
