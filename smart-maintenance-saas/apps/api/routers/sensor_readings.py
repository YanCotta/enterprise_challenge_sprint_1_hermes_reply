import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Security, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apps.api.dependencies import api_key_auth, get_db
from data.models import SensorReading
from data.schemas import SensorReading

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/readings", response_model=List[SensorReading], dependencies=[Security(api_key_auth, scopes=["data:read"])])
async def get_sensor_readings(
    limit: int = Query(default=100, le=1000, description="Maximum number of readings to return"),
    offset: int = Query(default=0, ge=0, description="Number of readings to skip"),
    sensor_id: Optional[str] = Query(default=None, description="Filter by specific sensor ID"),
    db: AsyncSession = Depends(get_db)
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
    try:
        # Build query
        query = select(SensorReading).order_by(desc(SensorReading.timestamp))
        
        # Add sensor filter if specified
        if sensor_id:
            query = query.where(SensorReading.sensor_id == sensor_id)
        
        # Add pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        readings = result.scalars().all()
        
        logger.info(f"Retrieved {len(readings)} sensor readings")
        return readings
        
    except Exception as e:
        logger.error(f"Error retrieving sensor readings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sensor readings: {str(e)}")

@router.get("/sensors", dependencies=[Security(api_key_auth, scopes=["data:read"])])
async def get_sensors_list(
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique sensor IDs in the database.
    
    Returns:
        List of unique sensor IDs with basic stats
    """
    try:
        # Get unique sensor IDs with counts
        from sqlalchemy import func
        
        query = select(
            SensorReading.sensor_id,
            func.count(SensorReading.sensor_id).label('reading_count'),
            func.max(SensorReading.timestamp).label('last_reading'),
            func.min(SensorReading.timestamp).label('first_reading')
        ).group_by(SensorReading.sensor_id)
        
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
        
        logger.info(f"Retrieved {len(sensor_list)} sensors")
        return sensor_list
        
    except Exception as e:
        logger.error(f"Error retrieving sensors list: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sensors list: {str(e)}")