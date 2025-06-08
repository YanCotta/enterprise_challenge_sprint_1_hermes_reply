"""
SchedulingAgent - Handles maintenance task scheduling based on predictions.

This agent receives MaintenancePredictedEvent notifications and schedules maintenance tasks
using optimization algorithms (currently simplified greedy approach, with OR-Tools planned for future).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
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
        self.logger.info("CalendarService initialized (dummy implementation)")
    
    def check_availability(self, technician_id: str, start_time: datetime, end_time: datetime) -> bool:
        self.logger.debug(f"Checking availability for technician {technician_id} from {start_time} to {end_time}")
        business_start, business_end = 8, 18
        if (start_time.hour >= business_start and end_time.hour <= business_end and
            start_time.weekday() < 5):
            self.logger.debug(f"Technician {technician_id} is available")
            return True
        self.logger.debug(f"Technician {technician_id} is not available")
        return False
    
    def book_slot(self, technician_id: str, start_time: datetime, end_time: datetime, 
                  maintenance_request_id: str) -> bool:
        self.logger.info(f"Booking slot for technician {technician_id}: {start_time} to {end_time} for request {maintenance_request_id}")
        return True


# Mock technicians data
mock_technicians = [
    {"id": "tech_001", "name": "John Smith", "skills": ["electrical", "mechanical"], "experience_years": 5, "availability_score": 0.8},
    {"id": "tech_002", "name": "Sarah Johnson", "skills": ["mechanical", "plumbing"], "experience_years": 8, "availability_score": 0.9},
]


class SchedulingAgent(BaseAgent):
    """
    SchedulingAgent handles maintenance task scheduling based on predictions.
    """
    
    def __init__(self, agent_id: str, event_bus: Any):
        super().__init__(agent_id, event_bus)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.calendar_service = CalendarService()
        self.logger.info(f"SchedulingAgent {agent_id} initialized")
    
    async def start(self) -> None:
        await super().start()
        await self.event_bus.subscribe(MaintenancePredictedEvent.__name__, self.handle_maintenance_predicted_event)
        self.logger.info(f"SchedulingAgent {self.agent_id} subscribed to {MaintenancePredictedEvent.__name__}")
    
    async def register_capabilities(self) -> None:
        self.capabilities.append(
            AgentCapability(name="maintenance_scheduling", description="Schedules maintenance tasks",
                            input_types=[MaintenancePredictedEvent.__name__], output_types=[MaintenanceScheduledEvent.__name__])
        )
        self.capabilities.append(
            AgentCapability(name="technician_assignment", description="Assigns optimal technicians",
                            input_types=["MaintenanceRequest"], output_types=["OptimizedSchedule"])
        )
        self.logger.debug(f"SchedulingAgent {self.agent_id} registered {len(self.capabilities)} capabilities")
    
    async def handle_maintenance_predicted_event(self, event_type: str, event_data_or_obj) -> None:
        event_obj = event_data_or_obj if isinstance(event_data_or_obj, MaintenancePredictedEvent) else MaintenancePredictedEvent(**event_data_or_obj)
        equipment_id = event_obj.equipment_id
        self.logger.info(f"Received {event_type} for equipment {equipment_id}")
        
        try:
            maintenance_request = self._create_maintenance_request(event_obj)
            self.logger.info(f"Created maintenance request {maintenance_request.id} for equipment {maintenance_request.equipment_id}")
            
            optimized_schedule = await self.schedule_maintenance_task(maintenance_request)
            
            if optimized_schedule.status == ScheduleStatus.SCHEDULED:
                await self._publish_maintenance_scheduled_event(event_obj, optimized_schedule)
                self.logger.info(f"Successfully scheduled maintenance for request {maintenance_request.id}")
            else:
                self.logger.warning(f"Failed to schedule maintenance for request {maintenance_request.id}: {optimized_schedule.status}")
                # Optionally publish a "SchedulingFailedEvent" here
                
        except Exception as e: # This will be caught by BaseAgent.handle_event's error handling
            self.logger.error(f"Error handling MaintenancePredictedEvent for eq {equipment_id}: {e}", exc_info=True)
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
    
    async def schedule_maintenance_task(self, maintenance_request: MaintenanceRequest) -> OptimizedSchedule:
        self.logger.info(f"Scheduling maintenance request {maintenance_request.id}")
        try:
            qualified_technicians = [tech for tech in mock_technicians if any(skill in tech["skills"] for skill in maintenance_request.required_skills)]
            if not qualified_technicians:
                return OptimizedSchedule(
                    request_id=maintenance_request.id, 
                    status=ScheduleStatus.FAILED_TO_SCHEDULE, 
                    constraints_violated=["no_qualified_technicians"],
                    scheduling_notes="No technicians available with required skills"
                )

            qualified_technicians.sort(key=lambda t: (t["availability_score"], t["experience_years"]), reverse=True)
            
            for technician in qualified_technicians:
                current_time = maintenance_request.preferred_time_window_start or datetime.utcnow()
                end_window = maintenance_request.preferred_time_window_end or (current_time + timedelta(days=30))
                
                while current_time < end_window:
                    if current_time.hour < 8: current_time = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
                    elif current_time.hour > 14: current_time = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0); continue
                    
                    scheduled_end = current_time + timedelta(hours=maintenance_request.estimated_duration_hours)
                    if self.calendar_service.check_availability(technician["id"], current_time, scheduled_end):
                        if self.calendar_service.book_slot(technician["id"], current_time, scheduled_end, maintenance_request.id):
                            score = self._calculate_optimization_score(maintenance_request, technician, current_time, scheduled_end)
                            
                            # Add constraints satisfied
                            constraints_satisfied = ["technician_skills_match", "within_time_window"]
                            
                            return OptimizedSchedule(
                                request_id=maintenance_request.id, status=ScheduleStatus.SCHEDULED,
                                assigned_technician_id=technician["id"], scheduled_start_time=current_time,
                                scheduled_end_time=scheduled_end, optimization_score=score,
                                constraints_satisfied=constraints_satisfied
                            )
                    current_time += timedelta(hours=2)
            
            return OptimizedSchedule(request_id=maintenance_request.id, status=ScheduleStatus.FAILED_TO_SCHEDULE, constraints_violated=["no_available_time_slots"])
        except Exception as e:
            self.logger.error(f"Error scheduling maintenance request {maintenance_request.id}: {e}", exc_info=True)
            # Let this exception propagate to be handled by handle_maintenance_predicted_event's try-except
            raise AgentProcessingError(f"Scheduling sub-process failed for request {maintenance_request.id}: {str(e)}", original_exception=e) from e # Import AgentProcessingError
    
    def _calculate_optimization_score(self, request: MaintenanceRequest, technician: Dict[str, Any], start_time: datetime, end_time: datetime) -> float:
        # Simplified scoring
        score = technician["availability_score"] * 0.5 + min(technician["experience_years"] / 10.0, 1.0) * 0.5
        return min(score, 1.0)
    
    async def _publish_maintenance_scheduled_event(self, original_event: MaintenancePredictedEvent, schedule: OptimizedSchedule) -> None:
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
                await self._publish_event("MaintenanceScheduledEvent", event_data_dict)
                self.logger.info(f"Published MaintenanceScheduledEvent for equipment {original_event.equipment_id}")
            else:
                self.logger.warning(f"Event bus not available. Cannot publish MaintenanceScheduledEvent for {original_event.equipment_id}")
                # Consider raising ConfigurationError if event bus is essential
        except Exception as e:
            self.logger.error(f"Error publishing MaintenanceScheduledEvent for eq {original_event.equipment_id}: {e}", exc_info=True)
            # Wrap and re-raise as EventPublishError
            raise EventPublishError(
                message=f"Failed to publish MaintenanceScheduledEvent for {original_event.equipment_id}: {str(e)}",
                original_exception=e
            ) from e
    
    async def process(self, data: Any) -> Any:
        # This agent's primary work is initiated by handle_maintenance_predicted_event
        self.logger.debug(f"SchedulingAgent {self.agent_id} received generic process call: {str(data)[:100]}...")
        # If data is a MaintenancePredictedEvent, route it (though it's usually handled by direct subscription)
        if isinstance(data, MaintenancePredictedEvent):
            await self.handle_maintenance_predicted_event(MaintenancePredictedEvent.__name__, data)
            return None # Explicitly return None as it's handled
        elif isinstance(data, dict) and "time_to_failure_days" in data and "equipment_id" in data: # Heuristic for dict
             try:
                event_obj = MaintenancePredictedEvent(**data)
                await self.handle_maintenance_predicted_event(MaintenancePredictedEvent.__name__, event_obj)
                return None
             except Exception as e: # Catch Pydantic validation or other errors
                 self.logger.error(f"Error processing dict data as MaintenancePredictedEvent: {e}", exc_info=True)
                 # Re-raise as AgentProcessingError to be caught by BaseAgent.handle_event
                 raise AgentProcessingError(f"Failed to process dict data as MaintenancePredictedEvent: {str(e)}", original_exception=e) from e
        return data
