from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database.orm_models import HumanDecisionORM
from data.schemas import DecisionResponse


async def create_human_decision(db: AsyncSession, decision_data: DecisionResponse) -> HumanDecisionORM:
    """Create and persist a new human decision record."""
    new_decision = HumanDecisionORM(
        request_id=decision_data.request_id,
        operator_id=decision_data.operator_id,
        decision=decision_data.decision,
        justification=decision_data.justification,
        additional_notes=decision_data.additional_notes,
        confidence=decision_data.confidence,
        correlation_id=decision_data.correlation_id,
        timestamp=decision_data.timestamp,
    )
    db.add(new_decision)
    await db.commit()
    await db.refresh(new_decision)
    return new_decision


async def get_human_decisions(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    operator_id: Optional[str] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    start_dt: Optional[datetime] = None,
    end_dt: Optional[datetime] = None,
) -> List[HumanDecisionORM]:
    """Retrieve filtered, paginated human decisions ordered by newest first."""
    query = select(HumanDecisionORM).order_by(HumanDecisionORM.timestamp.desc())

    if operator_id:
        query = query.where(HumanDecisionORM.operator_id == operator_id)
    if request_id:
        query = query.where(HumanDecisionORM.request_id == request_id)
    if correlation_id:
        query = query.where(HumanDecisionORM.correlation_id == correlation_id)
    if start_dt:
        query = query.where(HumanDecisionORM.timestamp >= start_dt)
    if end_dt:
        query = query.where(HumanDecisionORM.timestamp <= end_dt)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
