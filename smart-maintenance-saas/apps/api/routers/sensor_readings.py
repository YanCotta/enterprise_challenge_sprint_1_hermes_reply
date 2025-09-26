import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Security, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apps.api.dependencies import api_key_auth, get_db
from core.database.orm_models import SensorReadingORM
from pydantic import BaseModel, Field


class SensorReadingPublic(BaseModel):
    """Public-facing sensor reading model aligned with stored ORM fields.

    This avoids strict requirements from the internal SensorReading schema
    (which expects ingestion_timestamp + non-null unit) that caused 500 errors
    when rows lacked those values or field names differed.
    """

    sensor_id: str = Field(..., description="Unique sensor identifier")
    sensor_type: Optional[str] = Field(None, description="Type/category of sensor (free-form; legacy rows may contain non-standard values)")
    value: float = Field(..., description="Numeric sensor value")
    unit: Optional[str] = Field(None, description="Measurement unit")
    timestamp: datetime = Field(..., description="Original reading timestamp (UTC)")
    quality: Optional[float] = Field(None, description="Quality score of reading")
    sensor_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    ingestion_timestamp: Optional[datetime] = Field(
        None, description="When the reading was ingested (DB created_at)"
    )

    class Config:
        from_attributes = True

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_LIMIT = 1000


@router.get(
    "/readings",
    response_model=List[SensorReadingPublic],
    dependencies=[Security(api_key_auth, scopes=["data:read"])],
    summary="Get recent sensor readings",
    tags=["sensor_readings"],
)
async def get_sensor_readings(
    limit: int = Query(
        default=100,
        ge=1,
        le=MAX_LIMIT,
        description=f"Maximum number of readings to return (capped at {MAX_LIMIT})",
    ),
    offset: int = Query(default=0, ge=0, description="Number of readings to skip (pagination)"),
    sensor_id: Optional[str] = Query(
        default=None, description="Optional filter to only include a specific sensor ID"
    ),
    start_ts: Optional[datetime] = Query(
        default=None,
        description="Return readings with timestamp >= this UTC datetime (ISO 8601)"
    ),
    end_ts: Optional[datetime] = Query(
        default=None,
        description="Return readings with timestamp <= this UTC datetime (ISO 8601)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve sensor readings from the database.
    
    Args:
        limit: Maximum number of readings to return (max 1000)
        offset: Number of readings to skip for pagination
        sensor_id: Optional filter by specific sensor ID
        db: Database session
        
    Returns:
        List of sensor readings with timestamp, sensor_id, value, etc.
    """
    start_time = time.perf_counter()
    try:
        # Base query ordered by newest first
        query = select(SensorReadingORM).order_by(desc(SensorReadingORM.timestamp))

        if sensor_id:
            query = query.where(SensorReadingORM.sensor_id == sensor_id)
        if start_ts:
            query = query.where(SensorReadingORM.timestamp >= start_ts)
        if end_ts:
            query = query.where(SensorReadingORM.timestamp <= end_ts)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        rows: List[SensorReadingORM] = result.scalars().all()

        transformed: List[SensorReadingPublic] = []
        allowed_types = {"temperature","vibration","pressure","bearing","pump","manufacturing","audio","forecasting","general"}
        for r in rows:
            stype = r.sensor_type if r.sensor_type in allowed_types else (r.sensor_type or "general")
            transformed.append(SensorReadingPublic(
                sensor_id=r.sensor_id,
                sensor_type=stype,
                value=r.value,
                unit=r.unit or None,
                timestamp=r.timestamp,
                quality=r.quality,
                sensor_metadata=getattr(r, "sensor_metadata", None),
                ingestion_timestamp=getattr(r, "created_at", None),
            ))

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        log_level = logging.WARNING if duration_ms > 1500 else logging.INFO
        logger.log(
            log_level,
            "sensor_readings.fetch",
            extra={
                "count": len(transformed),
                "sensor_filter": sensor_id,
                "limit": limit,
                "offset": offset,
                "start_ts": start_ts.isoformat() if start_ts else None,
                "end_ts": end_ts.isoformat() if end_ts else None,
                "duration_ms": round(duration_ms, 2),
                "slow": duration_ms > 1500,
            },
        )
        return transformed
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.exception("Error retrieving sensor readings (duration_ms=%s)", round(duration_ms,2))
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve sensor readings: {str(e)}"
        ) from e

@router.get("/sensors", dependencies=[Security(api_key_auth, scopes=["data:read"])])
async def get_sensors_list(
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique sensor IDs in the database.
    
    Returns:
        List of unique sensor IDs with basic stats
    """
    start_time = time.perf_counter()
    try:
        # Get unique sensor IDs with counts
        from sqlalchemy import func
        
        query = select(
            SensorReadingORM.sensor_id,
            func.count(SensorReadingORM.sensor_id).label('reading_count'),
            func.max(SensorReadingORM.timestamp).label('last_reading'),
            func.min(SensorReadingORM.timestamp).label('first_reading')
        ).group_by(SensorReadingORM.sensor_id)
        
        result = await db.execute(query)
        sensors = result.all()
        
        sensor_list = []
        for sensor in sensors:
            sensor_list.append({
                "sensor_id": sensor.sensor_id,
                "reading_count": sensor.reading_count,
                "last_reading": sensor.last_reading,
                "first_reading": sensor.first_reading
            })
        
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        log_level = logging.WARNING if duration_ms > 2000 else logging.INFO
        logger.log(log_level, "sensors.list.fetch", extra={
            "sensor_count": len(sensor_list),
            "duration_ms": round(duration_ms, 2),
            "slow": duration_ms > 2000,
        })
        return sensor_list
        
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(f"Error retrieving sensors list after {round(duration_ms,2)} ms: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sensors list: {str(e)}")