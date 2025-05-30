from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smart_maintenance_saas.core.database.orm_models import SensorReadingORM
from smart_maintenance_saas.data.schemas import SensorReadingCreate # Assuming SensorReadingCreate is in schemas.py


class CRUDSensorReading:
    async def create_sensor_reading(
        self, db: AsyncSession, *, obj_in: SensorReadingCreate
    ) -> SensorReadingORM:
        """
        Create a new sensor reading.
        """
        # obj_in.model_dump() is for Pydantic v2. For v1, it's obj_in.dict()
        # Assuming Pydantic v2+ based on previous schema definitions.
        # exclude_unset=True helps in not setting fields that were not provided,
        # allowing database defaults to take effect if any.
        orm_data = obj_in.model_dump(exclude_unset=True)
        
        # If timestamp is not provided in obj_in and your ORM model expects it,
        # or if you want to ensure it's set if None was passed, handle it here.
        # SensorReadingCreate has timestamp as Optional[datetime]=None
        # SensorReadingORM has timestamp as nullable=False (but ORM might have server_default or client default)
        # For SensorReadingORM, timestamp is nullable=False and has no server_default.
        # So, it must be provided. The Pydantic model SensorReadingCreate allows it to be None.
        # If it's None, we should ensure it's set to datetime.utcnow() or handle as an error.
        # The Pydantic model definition for SensorReading (not Create) has default_factory=datetime.utcnow.
        # Let's ensure timestamp is set if not provided.
        if orm_data.get("timestamp") is None:
            orm_data["timestamp"] = datetime.utcnow()
            
        db_obj = SensorReadingORM(**orm_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_sensor_readings_by_sensor_id(
        self,
        db: AsyncSession,
        *,
        sensor_id: str,
        skip: int = 0,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[SensorReadingORM]:
        """
        Retrieve sensor readings for a specific sensor_id, with optional time filtering.
        """
        stmt = select(SensorReadingORM).where(SensorReadingORM.sensor_id == sensor_id)

        if start_time:
            stmt = stmt.where(SensorReadingORM.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(SensorReadingORM.timestamp <= end_time)

        stmt = stmt.order_by(SensorReadingORM.timestamp.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_sensor_reading_by_id(
        self, db: AsyncSession, *, reading_id: int
    ) -> Optional[SensorReadingORM]:
        """
        Retrieve a sensor reading by its primary key (id).
        """
        stmt = select(SensorReadingORM).where(SensorReadingORM.id == reading_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

# Create an instance of the CRUD class for easy import and use elsewhere
crud_sensor_reading = CRUDSensorReading()
