import logging
from datetime import date, datetime, time, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Security, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import api_key_auth, get_db
from core.database.crud.crud_human_decision import get_human_decisions
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
    operator_id: Optional[str] = Query(None, max_length=255),
    request_id: Optional[str] = Query(None, max_length=255),
    correlation_id: Optional[str] = Query(None, max_length=255),
    start_date: Optional[date] = Query(
        None,
        description="Filter decisions captured on or after this date (UTC)",
    ),
    end_date: Optional[date] = Query(
        None,
        description="Filter decisions captured on or before this date (UTC)",
    ),
) -> List[DecisionLogEntry]:
    start_dt = (
        datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        if start_date
        else None
    )
    end_dt = (
        datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
        if end_date
        else None
    )

    decisions = await get_human_decisions(
        db=db,
        limit=limit,
        offset=offset,
        operator_id=operator_id,
        request_id=request_id,
        correlation_id=correlation_id,
        start_dt=start_dt,
        end_dt=end_dt,
    )

    logger.info(
        "human_decisions.list",
        extra={
            "count": len(decisions),
            "limit": limit,
            "offset": offset,
            "operator_id": operator_id,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "start_date": start_dt.isoformat() if start_dt else None,
            "end_date": end_dt.isoformat() if end_dt else None,
        },
    )

    response_payload: List[DecisionLogEntry] = []
    for record in decisions:
        try:
            response_payload.append(
                DecisionLogEntry(
                    request_id=record.request_id,
                    decision=record.decision,
                    justification=record.justification,
                    operator_id=record.operator_id,
                    timestamp=record.timestamp,
                    confidence=record.confidence if record.confidence is not None else 1.0,
                    additional_notes=record.additional_notes,
                    correlation_id=record.correlation_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "human_decisions.serialize_failed",
                extra={
                    "error": str(exc),
                    "record_id": getattr(record, "id", None),
                },
            )
    return response_payload
