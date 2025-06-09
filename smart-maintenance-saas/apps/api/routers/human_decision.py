from fastapi import APIRouter, Request, HTTPException, Depends, Security
from apps.api.dependencies import api_key_auth # Updated to use api_key_auth
from data.schemas import DecisionResponse
from core.events.event_models import HumanDecisionResponseEvent
from core.events.event_bus import EventBus

router = APIRouter()

@router.post("/submit", status_code=201, dependencies=[Security(api_key_auth, scopes=["tasks:update"])])
async def submit_decision(
    decision_response: DecisionResponse,
    request: Request,
):
    """
    Submits a human operator's decision response to the system.

    This endpoint is typically called after a human operator has reviewed a
    `HumanDecisionRequiredEvent` (e.g., via a UI) and made a decision.
    The decision is then published as a `HumanDecisionResponseEvent` onto the event bus
    for other agents (like the OrchestratorAgent) to process.

    This endpoint is secured by an API key.

    Args:
        decision_response (DecisionResponse): The human operator's decision. This should
                                              conform to the `DecisionResponse` schema,
                                              including fields like `request_id` (linking to
                                              the original decision request), `decision`,
                                              `justification`, `operator_id`, and optionally
                                              `correlation_id`.
        request (Request): The FastAPI request object, used to access the system coordinator
                           and event bus.

    Returns:
        dict: A confirmation message including the status, event ID of the published
              `HumanDecisionResponseEvent`, and the original `request_id` of the decision.
              Example:
              ```json
              {
                  "status": "success",
                  "event_id": "some-uuid",
                  "request_id": "decision-request-abc"
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
