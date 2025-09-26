import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Security, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from apps.api.dependencies import api_key_auth, get_db
from core.database.orm_models import MaintenanceLogORM, MaintenanceTaskStatus
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(tags=["decisions"], prefix="")

class DecisionLogEntry(BaseModel):
    id: str = Field(..., description="UUID of the decision/maintenance log entry")
    task_id: str = Field(..., description="Associated maintenance task UUID")
    equipment_id: str = Field(..., description="Equipment identifier")
    completion_date: datetime = Field(..., description="When the decision/work was completed")
    technician_id: str = Field(..., description="Technician / operator identifier")
    status: MaintenanceTaskStatus = Field(..., description="Resulting status")
    actual_duration_hours: Optional[float] = Field(None, description="Duration in hours if recorded")
    notes: Optional[str] = Field(None, description="Additional notes or justification")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")

    class Config:
        from_attributes = True

@router.get(
    "/api/v1/decisions",
    response_model=List[DecisionLogEntry],
    dependencies=[Security(api_key_auth, scopes=["data:read"])],
    summary="List decision / maintenance log entries",
    description="Returns maintenance log (decision) entries ordered by most recent first"
)
async def list_decision_logs(
    limit: int = Query(100, ge=1, le=500, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Entries to skip for pagination") ,
    equipment_id: Optional[str] = Query(None, description="Filter by equipment ID"),
    task_id: Optional[str] = Query(None, description="Filter by maintenance task ID"),
    status: Optional[MaintenanceTaskStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(MaintenanceLogORM).order_by(desc(MaintenanceLogORM.created_at))
        if equipment_id:
            query = query.where(MaintenanceLogORM.equipment_id == equipment_id)
        if task_id:
            query = query.where(MaintenanceLogORM.task_id == task_id)
        if status:
            query = query.where(MaintenanceLogORM.status == status)
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        rows = result.scalars().all()
        logger.info("decisions.list", extra={
            "count": len(rows),
            "equipment_id": equipment_id,
            "task_id": task_id,
            "status": status.name if status else None,
            "limit": limit,
            "offset": offset
        })
        return rows
    except Exception as e:  # noqa: BLE001
        logger.exception("Error retrieving decision logs")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve decisions: {str(e)}") from e
