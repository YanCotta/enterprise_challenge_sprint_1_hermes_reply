import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, Security, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import api_key_auth, get_db
from core.database.crud.crud_human_decision import get_human_decisions
from core.database.orm_models import HumanDecisionORM
from data.schemas import DecisionResponse as DecisionLogEntry  # Reuse schema until a dedicated log schema is defined

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/decisions", tags=["Decisions"])

@router.get(
    "",
    response_model=List[DecisionLogEntry],
    dependencies=[Security(api_key_auth, scopes=["data:read"])],
    summary="Retrieve human decision logs",
    description="Returns persisted human decisions ordered by most recent first."
)
async def get_decision_logs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[HumanDecisionORM]:
    decisions = await get_human_decisions(db=db, limit=limit, offset=offset)
    return decisions
