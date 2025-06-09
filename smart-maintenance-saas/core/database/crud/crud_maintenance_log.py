"""
CRUD operations for maintenance log records.
"""

import uuid
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database.orm_models import MaintenanceLogORM, MaintenanceTaskStatus
from data.schemas import MaintenanceLog, MaintenanceLogCreate


class CRUDMaintenanceLog:
    """
    CRUD operations for maintenance log records.
    """

    async def create(
        self, db: AsyncSession, *, obj_in: MaintenanceLogCreate
    ) -> MaintenanceLogORM:
        """
        Create a new maintenance log entry.

        Args:
            db: Database session
            obj_in: Data for creating the maintenance log

        Returns:
            Created MaintenanceLogORM instance
        """
        # Convert Pydantic model to dict and create ORM instance
        obj_data = obj_in.dict()
        db_obj = MaintenanceLogORM(**obj_data)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[MaintenanceLogORM]:
        """
        Get a maintenance log by its ID.

        Args:
            db: Database session
            id: Maintenance log ID

        Returns:
            MaintenanceLogORM instance or None if not found
        """
        result = await db.execute(
            select(MaintenanceLogORM).where(MaintenanceLogORM.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_task_id(
        self, db: AsyncSession, task_id: uuid.UUID
    ) -> List[MaintenanceLogORM]:
        """
        Get all maintenance logs for a specific task.

        Args:
            db: Database session
            task_id: Maintenance task ID

        Returns:
            List of MaintenanceLogORM instances
        """
        result = await db.execute(
            select(MaintenanceLogORM)
            .where(MaintenanceLogORM.task_id == task_id)
            .order_by(desc(MaintenanceLogORM.completion_date))
        )
        return result.scalars().all()

    async def get_by_equipment_id(
        self, db: AsyncSession, equipment_id: str, limit: int = 100
    ) -> List[MaintenanceLogORM]:
        """
        Get maintenance logs for a specific equipment.

        Args:
            db: Database session
            equipment_id: Equipment identifier
            limit: Maximum number of records to return

        Returns:
            List of MaintenanceLogORM instances
        """
        result = await db.execute(
            select(MaintenanceLogORM)
            .where(MaintenanceLogORM.equipment_id == equipment_id)
            .order_by(desc(MaintenanceLogORM.completion_date))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_technician_id(
        self, db: AsyncSession, technician_id: str, limit: int = 100
    ) -> List[MaintenanceLogORM]:
        """
        Get maintenance logs for a specific technician.

        Args:
            db: Database session
            technician_id: Technician identifier
            limit: Maximum number of records to return

        Returns:
            List of MaintenanceLogORM instances
        """
        result = await db.execute(
            select(MaintenanceLogORM)
            .where(MaintenanceLogORM.technician_id == technician_id)
            .order_by(desc(MaintenanceLogORM.completion_date))
            .limit(limit)
        )
        return result.scalars().all()

    def orm_to_pydantic(self, orm_obj: MaintenanceLogORM) -> MaintenanceLog:
        """
        Convert ORM object to Pydantic model.

        Args:
            orm_obj: MaintenanceLogORM instance

        Returns:
            MaintenanceLog Pydantic model
        """
        return MaintenanceLog(
            id=orm_obj.id,
            task_id=orm_obj.task_id,
            equipment_id=orm_obj.equipment_id,
            completion_date=orm_obj.completion_date,
            technician_id=orm_obj.technician_id,
            notes=orm_obj.notes,
            status=orm_obj.status,
            actual_duration_hours=orm_obj.actual_duration_hours,
            created_at=orm_obj.created_at,
            updated_at=orm_obj.updated_at,
        )

    async def get_maintenance_logs_as_pydantic(
        self, db: AsyncSession, equipment_id: Optional[str] = None, limit: int = 100
    ) -> List[MaintenanceLog]:
        """
        Get maintenance logs and return as Pydantic models.

        Args:
            db: Database session
            equipment_id: Optional equipment filter
            limit: Maximum number of records to return

        Returns:
            List of MaintenanceLog Pydantic models
        """
        if equipment_id:
            orm_logs = await self.get_by_equipment_id(db, equipment_id, limit)
        else:
            # Get all logs, ordered by completion date
            result = await db.execute(
                select(MaintenanceLogORM)
                .order_by(desc(MaintenanceLogORM.completion_date))
                .limit(limit)
            )
            orm_logs = result.scalars().all()

        return [self.orm_to_pydantic(orm_log) for orm_log in orm_logs]


# Create a global instance for easy importing
crud_maintenance_log = CRUDMaintenanceLog()
