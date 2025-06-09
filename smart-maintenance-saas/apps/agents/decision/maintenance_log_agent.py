"""
MaintenanceLogAgent handles logging of completed maintenance tasks.
"""

import asyncio
import logging
from typing import Callable, Optional, Union

from core.database.crud.crud_maintenance_log import CRUDMaintenanceLog
from core.events.event_models import MaintenanceCompletedEvent
from data.schemas import MaintenanceLogCreate
from core.base_agent_abc import BaseAgent

logger = logging.getLogger(__name__)


class MaintenanceLogAgent(BaseAgent):
    """
    Agent responsible for logging completed maintenance tasks to the database.
    
    This agent listens for MaintenanceCompletedEvent and creates maintenance log entries
    in the database to track maintenance history and outcomes.
    """

    def __init__(
        self,
        agent_id: str,
        event_bus,
        crud_maintenance_log: CRUDMaintenanceLog,
        db_session_factory: Callable,
    ):
        """
        Initialize the MaintenanceLogAgent.

        Args:
            agent_id: Unique identifier for this agent
            event_bus: Event bus for publishing/subscribing to events
            crud_maintenance_log: CRUD operations for maintenance logs
            db_session_factory: Factory function to create database sessions
        """
        super().__init__(agent_id, event_bus)
        self.crud_maintenance_log = crud_maintenance_log
        self.db_session_factory = db_session_factory
        
        logger.info(f"MaintenanceLogAgent {agent_id} initialized")

    async def start(self):
        """Start the agent and subscribe to relevant events."""
        await super().start()
        
        # Subscribe to MaintenanceCompletedEvent
        await self.event_bus.subscribe(
            MaintenanceCompletedEvent.__name__,
            self.handle_maintenance_completed_event
        )
        
        logger.info(f"MaintenanceLogAgent {self.agent_id} subscribed to MaintenanceCompletedEvent")

    async def handle_maintenance_completed_event(
        self,
        event_type_or_event: Union[str, MaintenanceCompletedEvent],
        event_data: Optional[MaintenanceCompletedEvent] = None
    ):
        """
        Handle MaintenanceCompletedEvent by creating a maintenance log entry.

        Args:
            event_type_or_event: Either event type string or MaintenanceCompletedEvent object
            event_data: MaintenanceCompletedEvent data (when called with event type string)
        """
        try:
            # Handle both calling patterns from the event bus
            if isinstance(event_type_or_event, MaintenanceCompletedEvent):
                event = event_type_or_event
            else:
                event = event_data

            if not event:
                logger.error("No MaintenanceCompletedEvent data provided")
                return

            logger.info(
                f"MaintenanceLogAgent {self.agent_id} received MaintenanceCompletedEvent "
                f"for task {event.task_id}"
            )

            # Create maintenance log entry
            await self._create_maintenance_log(event)

        except Exception as e:
            logger.error(
                f"MaintenanceLogAgent {self.agent_id} failed to handle "
                f"MaintenanceCompletedEvent: {e}"
            )

    async def _create_maintenance_log(self, event: MaintenanceCompletedEvent):
        """
        Create a maintenance log entry in the database.

        Args:
            event: MaintenanceCompletedEvent containing completion details
        """
        try:
            # Create the maintenance log data
            log_data = MaintenanceLogCreate(
                task_id=event.task_id,
                equipment_id=event.equipment_id,
                completion_date=event.completion_date,
                technician_id=event.technician_id,
                notes=event.notes,
                status=event.status,
                actual_duration_hours=event.actual_duration_hours,
            )

            # Save to database
            async with self.db_session_factory() as db:
                maintenance_log = await self.crud_maintenance_log.create(db, obj_in=log_data)
                
                logger.info(
                    f"MaintenanceLogAgent {self.agent_id} created maintenance log "
                    f"entry {maintenance_log.id} for task {event.task_id}"
                )

        except Exception as e:
            logger.error(
                f"MaintenanceLogAgent {self.agent_id} failed to create maintenance log "
                f"for task {event.task_id}: {e}"
            )
            raise

    async def process(self):
        """
        Main processing loop for the agent.
        
        For this agent, the main work is done through event handlers,
        so this method just maintains the agent's running state.
        """
        while self.running:
            await asyncio.sleep(1.0)  # Keep the agent alive

    async def stop(self):
        """Stop the agent gracefully."""
        logger.info(f"MaintenanceLogAgent {self.agent_id} stopping")
        await super().stop()
