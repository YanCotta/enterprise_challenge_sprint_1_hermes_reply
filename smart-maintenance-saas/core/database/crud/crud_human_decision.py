from typing import List

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


async def get_human_decisions(db: AsyncSession, limit: int = 50, offset: int = 0) -> List[HumanDecisionORM]:
    """Retrieve a paginated list of human decisions ordered by most recent."""
    result = await db.execute(
        select(HumanDecisionORM).order_by(HumanDecisionORM.timestamp.desc()).offset(offset).limit(limit)
    )
    return result.scalars().all()
