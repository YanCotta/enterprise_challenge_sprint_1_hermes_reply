"""
SchedulingAgent - Handles maintenance task scheduling based on predictions.

This agent receives MaintenancePredictedEvent notifications and schedules maintenance tasks
using optimization algorithms (currently simplified greedy approach, with OR-Tools planned for future).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from apps.agents.base_agent import BaseAgent, AgentCapability
from core.events.event_models import MaintenancePredictedEvent, MaintenanceScheduledEvent
from data.schemas import MaintenanceRequest, OptimizedSchedule, ScheduleStatus


logger = logging.getLogger(__name__)


class CalendarService:
    """
    Dummy CalendarService for mocking external calendar integrations.
    In production, this would integrate with actual calendar systems like Google Calendar,
    Outlook, or specialized maintenance management systems.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CalendarService")
        self.logger.info("CalendarService initialized (dummy implementation)")
    
    def check_availability(self, technician_id: str, start_time: datetime, end_time: datetime) -> bool:
        """
        Check if a technician is available during the specified time window.
        
        Args:
            technician_id: ID of the technician to check
            start_time: Start of the time window
            end_time: End of the time window
            
        Returns:
            bool: True if technician is available, False otherwise
        """
        self.logger.debug(f"Checking availability for technician {technician_id} from {start_time} to {end_time}")
        
        # Mock logic: assume technicians are available during business hours (8 AM - 6 PM)
        business_start = 8  # 8 AM
        business_end = 18   # 6 PM
        
        # Simple availability check based on business hours
        if (start_time.hour >= business_start and end_time.hour <= business_end and
            start_time.weekday() < 5):  # Monday = 0, Friday = 4
            self.logger.debug(f"Technician {technician_id} is available")
            return True
        
        self.logger.debug(f"Technician {technician_id} is not available")
        return False
    
    def book_slot(self, technician_id: str, start_time: datetime, end_time: datetime, 
                  maintenance_request_id: str) -> bool:
        """
        Book a time slot for a technician.
        
        Args:
            technician_id: ID of the technician
            start_time: Start time of the booking
            end_time: End time of the booking
            maintenance_request_id: ID of the maintenance request
            
        Returns:
            bool: True if booking successful, False otherwise
        """
        self.logger.info(f"Booking slot for technician {technician_id}: {start_time} to {end_time} "
                        f"for request {maintenance_request_id}")
        
        # Mock implementation - always succeeds for now
        return True


# Mock technicians data
mock_technicians = [
    {
        "id": "tech_001",
        "name": "John Smith",
        "skills": ["electrical", "mechanical", "hvac"],
        "experience_years": 5,
        "availability_score": 0.8
    },
    {
        "id": "tech_002", 
        "name": "Sarah Johnson",
        "skills": ["mechanical", "plumbing", "general"],
        "experience_years": 8,
        "availability_score": 0.9
    },
    {
        "id": "tech_003",
        "name": "Mike Davis",
        "skills": ["electrical", "electronics", "automation"],
        "experience_years": 12,
        "availability_score": 0.7
    },
    {
        "id": "tech_004",
        "name": "Lisa Chen",
        "skills": ["hvac", "refrigeration", "controls"],
        "experience_years": 6,
        "availability_score": 0.85
    }
]


class SchedulingAgent(BaseAgent):
    """
    SchedulingAgent handles maintenance task scheduling based on predictions.
    
    This agent subscribes to MaintenancePredictedEvent and generates optimized
    maintenance schedules using various optimization strategies.
    """
    
    def __init__(self, agent_id: str, event_bus: Any):
        """
        Initialize the SchedulingAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            event_bus: Event bus for inter-agent communication
        """
        super().__init__(agent_id, event_bus)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.calendar_service = CalendarService()
        self.logger.info(f"SchedulingAgent {agent_id} initialized")
    
    async def start(self) -> None:
        """Start the agent and subscribe to relevant events."""
        await super().start()
        
        # Subscribe to MaintenancePredictedEvent
        await self.event_bus.subscribe(
            "MaintenancePredictedEvent",
            self.handle_maintenance_predicted_event
        )
        
        self.logger.info(f"SchedulingAgent {self.agent_id} subscribed to MaintenancePredictedEvent")
    
    async def register_capabilities(self) -> None:
        """Register the agent's capabilities."""
        self.capabilities.append(
            AgentCapability(
                name="maintenance_scheduling",
                description="Schedules maintenance tasks based on predictions using optimization algorithms",
                input_types=["MaintenancePredictedEvent"],
                output_types=["MaintenanceScheduledEvent"]
            )
        )
        
        self.capabilities.append(
            AgentCapability(
                name="technician_assignment",
                description="Assigns optimal technicians to maintenance tasks based on skills and availability",
                input_types=["MaintenanceRequest"],
                output_types=["OptimizedSchedule"]
            )
        )
        
        self.logger.debug(f"SchedulingAgent {self.agent_id} registered {len(self.capabilities)} capabilities")
    
    async def handle_maintenance_predicted_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle MaintenancePredictedEvent by creating and scheduling maintenance requests.
        
        Args:
            event_type: Type of the event (should be "MaintenancePredictedEvent")
            event_data: Event payload containing prediction data
        """
        self.logger.info(f"Received {event_type} for equipment {event_data.get('equipment_id')}")
        
        try:
            # Parse the event data
            prediction_event = MaintenancePredictedEvent(**event_data)
            
            # Transform prediction into maintenance request
            maintenance_request = self._create_maintenance_request(prediction_event)
            self.logger.info(f"Created maintenance request {maintenance_request.id} for equipment {maintenance_request.equipment_id}")
            
            # Schedule the maintenance task
            optimized_schedule = await self.schedule_maintenance_task(maintenance_request)
            
            # Publish MaintenanceScheduledEvent if scheduling was successful
            if optimized_schedule.status == ScheduleStatus.SCHEDULED:
                await self._publish_maintenance_scheduled_event(prediction_event, optimized_schedule)
                self.logger.info(f"Successfully scheduled maintenance for request {maintenance_request.id}")
            else:
                self.logger.warning(f"Failed to schedule maintenance for request {maintenance_request.id}: {optimized_schedule.status}")
                
        except Exception as e:
            self.logger.error(f"Error handling MaintenancePredictedEvent: {e}", exc_info=True)
    
    def _create_maintenance_request(self, prediction_event: MaintenancePredictedEvent) -> MaintenanceRequest:
        """
        Create a MaintenanceRequest from a MaintenancePredictedEvent.
        
        Args:
            prediction_event: The prediction event data
            
        Returns:
            MaintenanceRequest: The created maintenance request
        """
        # Calculate priority based on time to failure and confidence
        if prediction_event.time_to_failure_days <= 7:
            priority = 1  # Critical - within a week
        elif prediction_event.time_to_failure_days <= 30:
            priority = 2  # High - within a month
        elif prediction_event.time_to_failure_days <= 90:
            priority = 3  # Medium - within 3 months
        else:
            priority = 4  # Low - more than 3 months
        
        # Estimate duration based on maintenance type
        duration_map = {
            "preventive": 2.0,
            "corrective": 4.0,
            "inspection": 1.0,
            "replacement": 6.0,
            "calibration": 1.5
        }
        estimated_duration = duration_map.get(prediction_event.maintenance_type, 3.0)
        
        # Determine required skills based on equipment type (simplified logic)
        equipment_id = prediction_event.equipment_id.lower()
        required_skills = []
        if "pump" in equipment_id or "motor" in equipment_id:
            required_skills = ["mechanical", "electrical"]
        elif "hvac" in equipment_id or "air" in equipment_id:
            required_skills = ["hvac", "refrigeration"]
        elif "sensor" in equipment_id:
            required_skills = ["electrical", "electronics"]
        else:
            required_skills = ["general", "mechanical"]
        
        # Set preferred time window (e.g., schedule before predicted failure with buffer)
        buffer_days = max(1, prediction_event.time_to_failure_days * 0.1)  # 10% buffer, minimum 1 day
        preferred_deadline = prediction_event.predicted_failure_date - timedelta(days=buffer_days)
        preferred_start = datetime.utcnow() + timedelta(days=1)  # Start tomorrow at earliest
        
        return MaintenanceRequest(
            id=str(uuid4()),
            equipment_id=prediction_event.equipment_id,
            maintenance_type=prediction_event.maintenance_type,
            priority=priority,
            estimated_duration_hours=estimated_duration,
            required_skills=required_skills,
            preferred_time_window_start=preferred_start,
            preferred_time_window_end=preferred_deadline,
            deadline=prediction_event.predicted_failure_date,
            parts_needed=[]  # Would be determined by more detailed analysis
        )
    
    async def schedule_maintenance_task(self, maintenance_request: MaintenanceRequest) -> OptimizedSchedule:
        """
        Schedule a maintenance task using optimization algorithms.
        
        Currently implements a greedy assignment algorithm. Future versions will
        integrate OR-Tools for more sophisticated optimization.
        
        Args:
            maintenance_request: The maintenance request to schedule
            
        Returns:
            OptimizedSchedule: The optimized schedule result
        """
        self.logger.info(f"Scheduling maintenance request {maintenance_request.id}")
        
        try:
            # TODO: Replace with OR-Tools implementation for more sophisticated optimization
            # For now, using simplified greedy assignment logic
            
            # Filter technicians by required skills
            qualified_technicians = []
            for tech in mock_technicians:
                if any(skill in tech["skills"] for skill in maintenance_request.required_skills):
                    qualified_technicians.append(tech)
            
            if not qualified_technicians:
                self.logger.warning(f"No qualified technicians found for request {maintenance_request.id}")
                return OptimizedSchedule(
                    request_id=maintenance_request.id,
                    status=ScheduleStatus.FAILED_TO_SCHEDULE,
                    constraints_violated=["no_qualified_technicians"],
                    scheduling_notes="No technicians available with required skills"
                )
            
            # Sort by availability score and experience
            qualified_technicians.sort(
                key=lambda t: (t["availability_score"], t["experience_years"]), 
                reverse=True
            )
            
            # Try to find an available time slot for the best technician
            for technician in qualified_technicians:
                # Try to schedule within preferred time window
                current_time = maintenance_request.preferred_time_window_start or datetime.utcnow()
                end_window = maintenance_request.preferred_time_window_end or (current_time + timedelta(days=30))
                
                # Check availability in 4-hour blocks during business hours
                while current_time < end_window:
                    # Ensure we're scheduling during business hours
                    if current_time.hour < 8:
                        current_time = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
                    elif current_time.hour > 14:  # Last start time for a 4-hour job
                        current_time = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                        continue
                    
                    scheduled_end = current_time + timedelta(hours=maintenance_request.estimated_duration_hours)
                    
                    # Check if technician is available
                    if self.calendar_service.check_availability(technician["id"], current_time, scheduled_end):
                        # Book the slot
                        if self.calendar_service.book_slot(technician["id"], current_time, scheduled_end, maintenance_request.id):
                            
                            # Calculate optimization score based on various factors
                            score = self._calculate_optimization_score(
                                maintenance_request, technician, current_time, scheduled_end
                            )
                            
                            return OptimizedSchedule(
                                request_id=maintenance_request.id,
                                status=ScheduleStatus.SCHEDULED,
                                assigned_technician_id=technician["id"],
                                scheduled_start_time=current_time,
                                scheduled_end_time=scheduled_end,
                                optimization_score=score,
                                constraints_satisfied=[
                                    "technician_skills_match",
                                    "within_time_window",
                                    "technician_available"
                                ],
                                scheduling_notes=f"Assigned to {technician['name']} (experience: {technician['experience_years']} years)"
                            )
                    
                    # Move to next time slot (try every 2 hours)
                    current_time += timedelta(hours=2)
            
            # If no slot found for any qualified technician
            self.logger.warning(f"No available time slots found for request {maintenance_request.id}")
            return OptimizedSchedule(
                request_id=maintenance_request.id,
                status=ScheduleStatus.FAILED_TO_SCHEDULE,
                constraints_violated=["no_available_time_slots"],
                scheduling_notes="All qualified technicians are unavailable in the preferred time window"
            )
            
        except Exception as e:
            self.logger.error(f"Error scheduling maintenance request {maintenance_request.id}: {e}", exc_info=True)
            return OptimizedSchedule(
                request_id=maintenance_request.id,
                status=ScheduleStatus.FAILED_TO_SCHEDULE,
                constraints_violated=["scheduling_error"],
                scheduling_notes=f"Scheduling failed due to error: {str(e)}"
            )
    
    def _calculate_optimization_score(self, request: MaintenanceRequest, technician: Dict[str, Any], 
                                    start_time: datetime, end_time: datetime) -> float:
        """
        Calculate an optimization score for a schedule assignment.
        
        Args:
            request: The maintenance request
            technician: The assigned technician data
            start_time: Scheduled start time
            end_time: Scheduled end time
            
        Returns:
            float: Optimization score between 0.0 and 1.0
        """
        score = 0.0
        
        # Factor 1: Technician availability score (30%)
        score += technician["availability_score"] * 0.3
        
        # Factor 2: Skills match (25%)
        matching_skills = len(set(request.required_skills) & set(technician["skills"]))
        total_required_skills = len(request.required_skills)
        if total_required_skills > 0:
            skills_score = matching_skills / total_required_skills
        else:
            skills_score = 1.0
        score += skills_score * 0.25
        
        # Factor 3: Experience relevance (20%)
        experience_score = min(technician["experience_years"] / 10.0, 1.0)  # Cap at 10 years
        score += experience_score * 0.2
        
        # Factor 4: Time window preference (15%)
        if request.preferred_time_window_start and request.preferred_time_window_end:
            window_duration = (request.preferred_time_window_end - request.preferred_time_window_start).total_seconds()
            delay_from_preferred = (start_time - request.preferred_time_window_start).total_seconds()
            if window_duration > 0:
                time_score = max(0, 1.0 - (delay_from_preferred / window_duration))
            else:
                time_score = 1.0
        else:
            time_score = 1.0
        score += time_score * 0.15
        
        # Factor 5: Priority adjustment (10%)
        priority_score = (6 - request.priority) / 5.0  # Higher priority = higher score
        score += priority_score * 0.1
        
        return min(score, 1.0)  # Ensure score doesn't exceed 1.0
    
    async def _publish_maintenance_scheduled_event(self, original_event: MaintenancePredictedEvent, 
                                                 schedule: OptimizedSchedule) -> None:
        """
        Publish a MaintenanceScheduledEvent.
        
        Args:
            original_event: The original prediction event
            schedule: The optimized schedule
        """
        try:
            event_data = MaintenanceScheduledEvent(
                original_prediction_event_id=original_event.event_id,
                schedule_details=schedule.dict(),
                equipment_id=original_event.equipment_id,
                assigned_technician_id=schedule.assigned_technician_id,
                scheduled_start_time=schedule.scheduled_start_time,
                scheduled_end_time=schedule.scheduled_end_time,
                scheduling_method="greedy",
                optimization_score=schedule.optimization_score,
                constraints_satisfied=schedule.constraints_satisfied,
                constraints_violated=schedule.constraints_violated,
                agent_id=self.agent_id,
                correlation_id=original_event.correlation_id
            )
            
            await self._publish_event("MaintenanceScheduledEvent", event_data.dict())
            self.logger.info(f"Published MaintenanceScheduledEvent for equipment {original_event.equipment_id}")
            
        except Exception as e:
            self.logger.error(f"Error publishing MaintenanceScheduledEvent: {e}", exc_info=True)
    
    async def process(self, data: Any) -> Any:
        """
        Main processing method for the agent.
        
        Args:
            data: Input data to process
            
        Returns:
            Any: Processing result
        """
        # This method is called by the base class event handler
        # For this agent, specific event handling is done in handle_maintenance_predicted_event
        self.logger.debug(f"SchedulingAgent {self.agent_id} processing data: {str(data)[:100]}...")
        return data
