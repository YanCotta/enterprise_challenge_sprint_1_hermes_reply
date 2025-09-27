from fastapi import APIRouter, Request, HTTPException, Depends, Security
from apps.api.dependencies import api_key_auth, get_db  # include get_db for DB session
from data.schemas import DecisionResponse
from core.events.event_models import HumanDecisionResponseEvent
from core.events.event_bus import EventBus
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Import CRUD helper
from core.database.crud.crud_human_decision import create_human_decision

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/submit",
    status_code=201,
    dependencies=[Security(api_key_auth, scopes=["tasks:update"])],
    response_model=DecisionResponse,
    summary="Submit a human decision",
)
async def submit_decision(
    decision_response: DecisionResponse,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Submits (persists + publishes) a human operator's decision response.
    1. Persist decision to human_decisions table
    2. Publish HumanDecisionResponseEvent on the event bus
    """
    coordinator = request.app.state.coordinator
    if not coordinator:
        raise HTTPException(status_code=500, detail="System coordinator not available")

    event_bus: EventBus = coordinator.event_bus
    if not event_bus:
        raise HTTPException(status_code=500, detail="Event bus not available")

    try:
        # Persist
        await create_human_decision(db=db, decision_data=decision_response)
        logger.info(
            "human_decision.persisted",
            extra={"request_id": decision_response.request_id, "operator_id": decision_response.operator_id},
        )

        # Publish
        event = HumanDecisionResponseEvent(
            payload=decision_response,
            correlation_id=decision_response.correlation_id,
        )
        await event_bus.publish(event)
        logger.info(
            "human_decision.published",
            extra={"event_id": str(event.event_id), "request_id": decision_response.request_id},
        )
        return decision_response
    except Exception as e:  # noqa: BLE001
        logger.exception("Failed to submit human decision")
        raise HTTPException(status_code=500, detail="Failed to process and persist the decision.") from e
