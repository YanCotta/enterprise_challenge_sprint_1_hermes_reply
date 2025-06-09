"""
SchedulingAgent - Handles maintenance task scheduling based on predictions.

This agent receives MaintenancePredictedEvent notifications and schedules maintenance tasks
using optimization algorithms (currently simplified greedy approach, with OR-Tools planned for future).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from core.base_agent_abc import BaseAgent, AgentCapability
from core.events.event_models import MaintenancePredictedEvent, MaintenanceScheduledEvent
from data.schemas import MaintenanceRequest, OptimizedSchedule, ScheduleStatus
from data.exceptions import EventPublishError, AgentProcessingError # Import EventPublishError and AgentProcessingError

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Dummy CalendarService for mocking external calendar integrations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CalendarService")
        self.logger.info("CalendarService initialized (dummy implementation)", extra={"correlation_id": "N/A"})
    
    def check_availability(self, technician_id: str, start_time: datetime, end_time: datetime) -> bool:
        # Assuming correlation_id is not available in this context or passed down
        self.logger.debug(f"Checking availability for technician {technician_id} from {start_time} to {end_time}", extra={"correlation_id": "N/A"})
        business_start, business_end = 8, 18
        if (start_time.hour >= business_start and end_time.hour <= business_end and
            start_time.weekday() < 5):
            self.logger.debug(f"Technician {technician_id} is available", extra={"correlation_id": "N/A"})
            return True
        self.logger.debug(f"Technician {technician_id} is not available", extra={"correlation_id": "N/A"})
        return False
    
    def book_slot(self, technician_id: str, start_time: datetime, end_time: datetime, 
                  maintenance_request_id: str) -> bool:
        # Assuming correlation_id is not available in this context or passed down
        self.logger.info(f"Booking slot for technician {technician_id}: {start_time} to {end_time} for request {maintenance_request_id}", extra={"correlation_id": "N/A"})
        return True


# Mock technicians data
mock_technicians = [
    {"id": "tech_001", "name": "John Smith", "skills": ["electrical", "mechanical"], "experience_years": 5, "availability_score": 0.8},
    {"id": "tech_002", "name": "Sarah Johnson", "skills": ["mechanical", "plumbing"], "experience_years": 8, "availability_score": 0.9},
]


class SchedulingAgent(BaseAgent):
    """
    The SchedulingAgent is responsible for handling maintenance task scheduling.

    It listens for `MaintenancePredictedEvent`s, which indicate a potential need
    for maintenance based on predictions from other agents. Upon receiving such an
    event, this agent:

    1.  Creates a `MaintenanceRequest` based on the prediction details.
    2.  Utilizes a (currently simplified) scheduling algorithm to find a suitable
        time slot and assign an appropriate technician. This involves:
        - Checking technician skills against request requirements.
        - Using a `CalendarService` (mocked for now) to check technician availability.
        - Selecting a technician based on availability and qualifications.
    3.  If scheduling is successful, it publishes a `MaintenanceScheduledEvent`
        with the details of the scheduled task, including the assigned technician,
        start and end times.
    4.  If scheduling fails (e.g., no qualified or available technicians), it logs
        the failure. Future enhancements could involve publishing a
        `SchedulingFailedEvent`.

    The agent uses mock technician data and a simplified greedy approach for scheduling,
    with plans to integrate more sophisticated optimization (e.g., using OR-Tools)
    in the future.
    """
    
    def __init__(self, agent_id: str, event_bus: Any):
        super().__init__(agent_id, event_bus)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.calendar_service = CalendarService()
        self.logger.info(f"SchedulingAgent {agent_id} initialized", extra={"correlation_id": "N/A"})
    
    async def start(self) -> None:
        await super().start()
        await self.event_bus.subscribe(MaintenancePredictedEvent.__name__, self.handle_maintenance_predicted_event)
        self.logger.info(
            f"SchedulingAgent {self.agent_id} subscribed to {MaintenancePredictedEvent.__name__}",
            extra={"correlation_id": "N/A"}
        )
    
    async def register_capabilities(self) -> None:
        self.capabilities.append(
            AgentCapability(name="maintenance_scheduling", description="Schedules maintenance tasks",
                            input_types=[MaintenancePredictedEvent.__name__], output_types=[MaintenanceScheduledEvent.__name__])
        )
        self.capabilities.append(
            AgentCapability(name="technician_assignment", description="Assigns optimal technicians",
                            input_types=["MaintenanceRequest"], output_types=["OptimizedSchedule"])
        )
        self.logger.debug(
            f"SchedulingAgent {self.agent_id} registered {len(self.capabilities)} capabilities",
            extra={"correlation_id": "N/A"}
        )
    
    async def handle_maintenance_predicted_event(self, event_type_name: str, event_data: dict) -> None:
        # Convert the event data dict to a MaintenancePredictedEvent object
        event_obj = MaintenancePredictedEvent(**event_data)
        equipment_id = event_obj.equipment_id
        correlation_id = getattr(event_obj, 'correlation_id', "N/A") # Extract correlation_id

        self.logger.info(
            f"Received MaintenancePredictedEvent for equipment {equipment_id}",
            extra={"correlation_id": correlation_id}
        )
        
        try:
            maintenance_request = self._create_maintenance_request(event_obj) # correlation_id not directly needed here
            self.logger.info(
                f"Created maintenance request {maintenance_request.id} for equipment {maintenance_request.equipment_id}",
                extra={"correlation_id": correlation_id}
            )
            
            optimized_schedule = await self.schedule_maintenance_task(maintenance_request, correlation_id=correlation_id)
            
            if optimized_schedule.status == ScheduleStatus.SCHEDULED:
                await self._publish_maintenance_scheduled_event(event_obj, optimized_schedule, correlation_id=correlation_id)
                self.logger.info(
                    f"Successfully scheduled maintenance for request {maintenance_request.id}",
                    extra={"correlation_id": correlation_id}
                )
            else:
                self.logger.warning(
                    f"Failed to schedule maintenance for request {maintenance_request.id}: {optimized_schedule.status}",
                    extra={"correlation_id": correlation_id}
                )
                # Optionally publish a "SchedulingFailedEvent" here
                
        except Exception as e: # This will be caught by BaseAgent.handle_event's error handling
            self.logger.error(
                f"Error handling MaintenancePredictedEvent for eq {equipment_id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            raise # Re-raise to be handled by BaseAgent's error handling logic
    
    def _create_maintenance_request(self, prediction_event: MaintenancePredictedEvent) -> MaintenanceRequest:
        # Calculate priority based on time to failure
        if prediction_event.time_to_failure_days <= 7:
            priority = 1  # High priority
        elif prediction_event.time_to_failure_days <= 30:
            priority = 2  # Medium priority  
        elif prediction_event.time_to_failure_days <= 90:
            priority = 3  # Low priority
        else:
            priority = 4  # Very low priority
        
        # Calculate duration based on maintenance type
        if prediction_event.maintenance_type == "corrective":
            estimated_duration = 4.0  # Corrective maintenance takes longer
        elif prediction_event.maintenance_type == "preventive":
            estimated_duration = 2.0  # Preventive maintenance is quicker
        else:
            estimated_duration = 2.0  # Default
            
        # Map equipment type to required skills
        equipment_id = prediction_event.equipment_id.lower()
        if "hvac" in equipment_id:
            required_skills = ["hvac", "mechanical"]
        elif "pump" in equipment_id:
            required_skills = ["mechanical", "hydraulics"]
        elif "motor" in equipment_id:
            required_skills = ["electrical", "mechanical"]
        else:
            required_skills = ["mechanical"]  # Default fallback
        
        preferred_deadline = prediction_event.predicted_failure_date - timedelta(days=max(1, prediction_event.time_to_failure_days * 0.1))
        preferred_start = datetime.utcnow() + timedelta(days=1)
        
        return MaintenanceRequest(
            id=str(uuid4()), equipment_id=prediction_event.equipment_id,
            maintenance_type=prediction_event.maintenance_type, priority=priority,
            estimated_duration_hours=estimated_duration, required_skills=required_skills,
            preferred_time_window_start=preferred_start, preferred_time_window_end=preferred_deadline,
            deadline=prediction_event.predicted_failure_date, parts_needed=[]
        )

    def _find_best_qualified_technician(self, maintenance_request: MaintenanceRequest, technicians: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Finds the best qualified and available technician for a maintenance request.

        Args:
            maintenance_request: The maintenance request details.
            technicians: A list of available technicians.

        Returns:
            The best qualified technician dictionary or None if no suitable technician is found.
        """
        qualified_technicians = [
            tech for tech in technicians
            if any(skill in tech["skills"] for skill in maintenance_request.required_skills)
        ]

        if not qualified_technicians:
            self.logger.debug(f"No technicians found with skills: {maintenance_request.required_skills} for request {maintenance_request.id}")
            return None

        # Sort by availability score (descending) then experience (descending)
        qualified_technicians.sort(key=lambda t: (t["availability_score"], t["experience_years"]), reverse=True)

        # For this refactoring, we return the top one.
        # Future enhancements could return a list of top N.
        self.logger.debug(f"Found {len(qualified_technicians)} qualified technicians for request {maintenance_request.id}. Best: {qualified_technicians[0]['id']}")
        return qualified_technicians[0]

    def _find_available_slot_for_technician(
        self, technician: Dict[str, Any], maintenance_request: MaintenanceRequest, correlation_id: Optional[str] = None
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Finds an available time slot for a given technician and maintenance request.

        Args:
            technician: The technician to check availability for.
            maintenance_request: The maintenance request details.
            correlation_id: Optional correlation ID for logging.

        Returns:
            A tuple of (scheduled_start_time, scheduled_end_time) if a slot is found and booked,
            otherwise None.
        """
        current_time = maintenance_request.preferred_time_window_start or datetime.utcnow()
        # Ensure current_time is not in the past for scheduling, adjust to next possible working hour if so.
        now = datetime.utcnow()
        if current_time < now:
            current_time = now

        # Align current_time to a sensible start, e.g., next hour or next working day's start
        if current_time.minute != 0 or current_time.second != 0 or current_time.microsecond != 0:
             current_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


        end_window = maintenance_request.preferred_time_window_end or (current_time + timedelta(days=30)) # Default 30 day window

        self.logger.debug(
            f"Searching slot for tech {technician['id']} for req {maintenance_request.id} from {current_time} to {end_window}",
            extra={"correlation_id": correlation_id}
        )

        while current_time < end_window:
            # Adjust to business hours (e.g., 8 AM)
            if current_time.hour < 8:
                current_time = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
            # If current_time is past a reasonable hour to schedule a task of X duration (e.g. 14:00 for a 4hr task, assuming end by 18:00)
            # or if it's a weekend
            max_start_hour = 18 - int(maintenance_request.estimated_duration_hours + 0.99) # e.g. 18-4 = 14:00
            if current_time.hour > max_start_hour or current_time.weekday() >= 5: # Monday is 0, Friday is 4
                current_time = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                if current_time >= end_window : # Check if we jumped past the window
                    break
                continue # Re-evaluate new current_time in the loop

            scheduled_end = current_time + timedelta(hours=maintenance_request.estimated_duration_hours)

            # Ensure scheduled_end is within business hours too
            if scheduled_end.hour > 18 or (scheduled_end.day != current_time.day and scheduled_end.hour !=0) : # ends after 6 PM or spills to next day incorrectly
                 current_time += timedelta(hours=1) # Try next hour
                 continue


            if self.calendar_service.check_availability(technician["id"], current_time, scheduled_end):
                if self.calendar_service.book_slot(technician["id"], current_time, scheduled_end, maintenance_request.id):
                    self.logger.info(
                        f"Slot found and booked for tech {technician['id']} for req {maintenance_request.id}: {current_time} to {scheduled_end}",
                        extra={"correlation_id": correlation_id}
                    )
                    return current_time, scheduled_end

            current_time += timedelta(hours=1) # Check next hour slot

        self.logger.debug(
            f"No available slot found for tech {technician['id']} for req {maintenance_request.id} within the window.",
            extra={"correlation_id": correlation_id}
        )
        return None

    async def schedule_maintenance_task(self, maintenance_request: MaintenanceRequest, correlation_id: Optional[str] = None) -> OptimizedSchedule:
        self.logger.info(
            f"Scheduling maintenance request {maintenance_request.id}",
            extra={"correlation_id": correlation_id}
        )
        try:
            # Using mock_technicians directly as per the existing code structure
            best_technician = self._find_best_qualified_technician(maintenance_request, mock_technicians)

            if not best_technician:
                self.logger.warning(f"No qualified technicians for request {maintenance_request.id}", extra={"correlation_id": correlation_id})
                return OptimizedSchedule(
                    request_id=maintenance_request.id, 
                    status=ScheduleStatus.FAILED_TO_SCHEDULE, 
                    constraints_violated=["no_qualified_technicians"],
                    scheduling_notes="No technicians available with required skills."
                )
            
            # For now, trying only the best technician as per initial refactor plan.
            # Future: Iterate top N technicians.
            slot = self._find_available_slot_for_technician(best_technician, maintenance_request, correlation_id)
            
            if slot:
                scheduled_start, scheduled_end = slot
                score = self._calculate_optimization_score(maintenance_request, best_technician, scheduled_start, scheduled_end)
                constraints_satisfied = ["technician_skills_match", "within_time_window", "technician_available"]

                return OptimizedSchedule(
                    request_id=maintenance_request.id, status=ScheduleStatus.SCHEDULED,
                    assigned_technician_id=best_technician["id"], scheduled_start_time=scheduled_start,
                    scheduled_end_time=scheduled_end, optimization_score=score,
                    constraints_satisfied=constraints_satisfied
                )
            else:
                self.logger.warning(
                    f"No available slot found for the best technician {best_technician['id']} for request {maintenance_request.id}",
                    extra={"correlation_id": correlation_id}
                )
                return OptimizedSchedule(
                    request_id=maintenance_request.id,
                    status=ScheduleStatus.FAILED_TO_SCHEDULE,
                    constraints_violated=["no_available_time_slots_for_qualified_technician"],
                    scheduling_notes=f"No available slot for qualified technician {best_technician['id']}."
                )

        except Exception as e:
            self.logger.error(
                f"Error scheduling maintenance request {maintenance_request.id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            # Let this exception propagate to be handled by handle_maintenance_predicted_event's try-except
            raise AgentProcessingError(f"Scheduling sub-process failed for request {maintenance_request.id}: {str(e)}", original_exception=e) from e # Import AgentProcessingError
    
    def _calculate_optimization_score(self, request: MaintenanceRequest, technician: Dict[str, Any], start_time: datetime, end_time: datetime) -> float:
        # Simplified scoring
        score = technician["availability_score"] * 0.5 + min(technician["experience_years"] / 10.0, 1.0) * 0.5
        return min(score, 1.0)
    
    async def _publish_maintenance_scheduled_event(self, original_event: MaintenancePredictedEvent, schedule: OptimizedSchedule, correlation_id: Optional[str] = None) -> None:
        """Publish a MaintenanceScheduledEvent using the event bus directly."""
        try:
            # Create the event object instance
            event_data_object = MaintenanceScheduledEvent(
                original_prediction_event_id=original_event.event_id,
                schedule_details=schedule.model_dump(), # Use model_dump() for Pydantic V2+
                equipment_id=original_event.equipment_id,
                assigned_technician_id=schedule.assigned_technician_id,
                scheduled_start_time=schedule.scheduled_start_time,
                scheduled_end_time=schedule.scheduled_end_time,
                scheduling_method="greedy", # Example
                optimization_score=schedule.optimization_score,
                constraints_satisfied=schedule.constraints_satisfied or [],
                constraints_violated=schedule.constraints_violated or [],
                agent_id=self.agent_id,
                correlation_id=original_event.correlation_id
            )
            
            # Convert to dictionary for _publish_event
            event_data_dict = event_data_object.model_dump()
            
            if self.event_bus:
                await self._publish_event("MaintenanceScheduledEvent", event_data_dict) # _publish_event likely needs correlation_id too
                self.logger.info(
                    f"Published MaintenanceScheduledEvent for equipment {original_event.equipment_id}",
                    extra={"correlation_id": correlation_id}
                )
            else:
                self.logger.warning(
                    f"Event bus not available. Cannot publish MaintenanceScheduledEvent for {original_event.equipment_id}",
                    extra={"correlation_id": correlation_id}
                )
                # Consider raising ConfigurationError if event bus is essential
        except Exception as e:
            self.logger.error(
                f"Error publishing MaintenanceScheduledEvent for eq {original_event.equipment_id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            # Wrap and re-raise as EventPublishError
            raise EventPublishError(
                message=f"Failed to publish MaintenanceScheduledEvent for {original_event.equipment_id}: {str(e)}",
                original_exception=e
            ) from e
    
    async def process(self, data: Any) -> Any:
        # This agent's primary work is initiated by handle_maintenance_predicted_event
        correlation_id = getattr(data, 'correlation_id', "N/A") if hasattr(data, 'correlation_id') else "N/A"
        if isinstance(data, dict): # If data is a dict, try to get correlation_id from it
            correlation_id = data.get('correlation_id', "N/A")

        self.logger.debug(
            f"SchedulingAgent {self.agent_id} received generic process call: {str(data)[:100]}...",
            extra={"correlation_id": correlation_id}
        )
        # If data is a MaintenancePredictedEvent, route it (though it's usually handled by direct subscription)
        if isinstance(data, MaintenancePredictedEvent):
            # correlation_id will be extracted within handle_maintenance_predicted_event
            await self.handle_maintenance_predicted_event(data)
            return None # Explicitly return None as it's handled
        elif isinstance(data, dict) and "time_to_failure_days" in data and "equipment_id" in data: # Heuristic for dict
             try:
                event_obj = MaintenancePredictedEvent(**data)
                # correlation_id will be extracted within handle_maintenance_predicted_event from event_obj
                await self.handle_maintenance_predicted_event(event_obj)
                return None
             except Exception as e: # Catch Pydantic validation or other errors
                 self.logger.error(
                     f"Error processing dict data as MaintenancePredictedEvent: {e}",
                     exc_info=True,
                     extra={"correlation_id": correlation_id} # Use correlation_id extracted from dict
                 )
                 # Re-raise as AgentProcessingError to be caught by BaseAgent.handle_event
                 raise AgentProcessingError(f"Failed to process dict data as MaintenancePredictedEvent: {str(e)}", original_exception=e) from e
        return data
