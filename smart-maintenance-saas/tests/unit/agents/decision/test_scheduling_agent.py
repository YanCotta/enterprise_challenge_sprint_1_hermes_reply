"""
Unit tests for the SchedulingAgent.

Tests the core functionality of maintenance task scheduling including:
- Event handling for MaintenancePredictedEvent
- Maintenance request creation
- Schedule optimization using greedy algorithm
- Event publishing for MaintenanceScheduledEvent
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.agents.decision.scheduling_agent import SchedulingAgent, CalendarService
from core.events.event_models import MaintenancePredictedEvent, MaintenanceScheduledEvent
from data.schemas import MaintenanceRequest, OptimizedSchedule, ScheduleStatus


class TestCalendarService:
    """Test the CalendarService mock implementation."""
    
    def test_init(self):
        """Test CalendarService initialization."""
        service = CalendarService()
        assert service is not None
    
    def test_check_availability_business_hours(self):
        """Test availability checking during business hours."""
        service = CalendarService()
        
        # Test during business hours on weekday
        start_time = datetime(2025, 6, 9, 10, 0)  # Monday 10 AM
        end_time = datetime(2025, 6, 9, 14, 0)    # Monday 2 PM
        
        assert service.check_availability("tech_001", start_time, end_time) is True
    
    def test_check_availability_after_hours(self):
        """Test availability checking after business hours."""
        service = CalendarService()
        
        # Test after business hours
        start_time = datetime(2025, 6, 9, 19, 0)  # Monday 7 PM
        end_time = datetime(2025, 6, 9, 21, 0)    # Monday 9 PM
        
        assert service.check_availability("tech_001", start_time, end_time) is False
    
    def test_check_availability_weekend(self):
        """Test availability checking on weekend."""
        service = CalendarService()
        
        # Test on weekend
        start_time = datetime(2025, 6, 7, 10, 0)  # Saturday 10 AM
        end_time = datetime(2025, 6, 7, 14, 0)    # Saturday 2 PM
        
        assert service.check_availability("tech_001", start_time, end_time) is False
    
    def test_book_slot(self):
        """Test booking a time slot."""
        service = CalendarService()
        
        start_time = datetime(2025, 6, 9, 10, 0)
        end_time = datetime(2025, 6, 9, 14, 0)
        
        result = service.book_slot("tech_001", start_time, end_time, "request_123")
        assert result is True


class TestSchedulingAgent:
    """Test the SchedulingAgent functionality."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus."""
        event_bus = AsyncMock()
        return event_bus
    
    @pytest.fixture
    def scheduling_agent(self, mock_event_bus):
        """Create a SchedulingAgent instance for testing."""
        return SchedulingAgent("test_scheduling_agent", mock_event_bus)
    
    @pytest.fixture
    def sample_prediction_event_data(self):
        """Create sample MaintenancePredictedEvent data."""
        return {
            "event_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "original_anomaly_event_id": str(uuid4()),
            "equipment_id": "pump_001",
            "predicted_failure_date": (datetime.utcnow() + timedelta(days=15)).isoformat(),
            "confidence_interval_lower": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "confidence_interval_upper": (datetime.utcnow() + timedelta(days=20)).isoformat(),
            "prediction_confidence": 0.85,
            "time_to_failure_days": 15.0,
            "maintenance_type": "preventive",
            "prediction_method": "prophet",
            "historical_data_points": 100,
            "model_metrics": {"mae": 0.1, "rmse": 0.15},
            "recommended_actions": ["inspect_bearings", "check_vibration"],
            "agent_id": "prediction_agent_001"
        }
    
    def test_init(self, mock_event_bus):
        """Test SchedulingAgent initialization."""
        agent = SchedulingAgent("test_agent", mock_event_bus)
        
        assert agent.agent_id == "test_agent"
        assert agent.event_bus == mock_event_bus
        assert agent.calendar_service is not None
        assert isinstance(agent.calendar_service, CalendarService)
    
    @pytest.mark.asyncio
    async def test_start(self, scheduling_agent):
        """Test agent startup and event subscription."""
        await scheduling_agent.start()
        
        assert scheduling_agent.status == "running"
        scheduling_agent.event_bus.subscribe.assert_called_once_with(
            "MaintenancePredictedEvent",
            scheduling_agent.handle_maintenance_predicted_event
        )
    
    @pytest.mark.asyncio
    async def test_register_capabilities(self, scheduling_agent):
        """Test capability registration."""
        await scheduling_agent.register_capabilities()
        
        assert len(scheduling_agent.capabilities) == 2
        
        # Check maintenance scheduling capability
        scheduling_cap = scheduling_agent.capabilities[0]
        assert scheduling_cap.name == "maintenance_scheduling"
        assert "MaintenancePredictedEvent" in scheduling_cap.input_types
        assert "MaintenanceScheduledEvent" in scheduling_cap.output_types
        
        # Check technician assignment capability
        assignment_cap = scheduling_agent.capabilities[1]
        assert assignment_cap.name == "technician_assignment"
        assert "MaintenanceRequest" in assignment_cap.input_types
        assert "OptimizedSchedule" in assignment_cap.output_types
    
    def test_create_maintenance_request_high_priority(self, scheduling_agent):
        """Test creation of high priority maintenance request."""
        # Create prediction event with short time to failure (high priority)
        prediction_event = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="critical_pump_001",
            predicted_failure_date=datetime.utcnow() + timedelta(days=5),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=3),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=7),
            prediction_confidence=0.9,
            time_to_failure_days=5.0,
            maintenance_type="corrective",
            historical_data_points=50,
            agent_id="prediction_agent"
        )
        
        request = scheduling_agent._create_maintenance_request(prediction_event)
        
        assert request.equipment_id == "critical_pump_001"
        assert request.maintenance_type == "corrective"
        assert request.priority == 1  # High priority due to short time to failure
        assert request.estimated_duration_hours == 4.0  # Corrective maintenance duration
        assert "mechanical" in request.required_skills or "electrical" in request.required_skills
        assert request.deadline == prediction_event.predicted_failure_date
    
    def test_create_maintenance_request_low_priority(self, scheduling_agent):
        """Test creation of low priority maintenance request."""
        # Create prediction event with long time to failure (low priority)
        prediction_event = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="hvac_unit_002",
            predicted_failure_date=datetime.utcnow() + timedelta(days=180),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=150),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=210),
            prediction_confidence=0.7,
            time_to_failure_days=180.0,
            maintenance_type="preventive",
            historical_data_points=200,
            agent_id="prediction_agent"
        )
        
        request = scheduling_agent._create_maintenance_request(prediction_event)
        
        assert request.equipment_id == "hvac_unit_002"
        assert request.maintenance_type == "preventive" 
        assert request.priority == 4  # Low priority due to long time to failure
        assert request.estimated_duration_hours == 2.0  # Preventive maintenance duration
        assert "hvac" in request.required_skills
    
    @pytest.mark.asyncio
    async def test_schedule_maintenance_task_success(self, scheduling_agent):
        """Test successful maintenance task scheduling."""
        # Mock the calendar service to return availability
        with patch.object(scheduling_agent.calendar_service, 'check_availability', return_value=True), \
             patch.object(scheduling_agent.calendar_service, 'book_slot', return_value=True):
            
            request = MaintenanceRequest(
                id="req_001",
                equipment_id="pump_001",
                maintenance_type="preventive",
                priority=2,
                estimated_duration_hours=2.0,
                required_skills=["mechanical"],
                preferred_time_window_start=datetime.utcnow() + timedelta(days=1),
                preferred_time_window_end=datetime.utcnow() + timedelta(days=7),
                deadline=datetime.utcnow() + timedelta(days=14)
            )
            
            schedule = await scheduling_agent.schedule_maintenance_task(request)
            
            assert schedule.request_id == "req_001"
            assert schedule.status == ScheduleStatus.SCHEDULED
            assert schedule.assigned_technician_id is not None
            assert schedule.scheduled_start_time is not None
            assert schedule.scheduled_end_time is not None
            assert schedule.optimization_score is not None
            assert "technician_skills_match" in schedule.constraints_satisfied
            assert "within_time_window" in schedule.constraints_satisfied
            assert "technician_available" in schedule.constraints_satisfied
    
    @pytest.mark.asyncio
    async def test_schedule_maintenance_task_no_qualified_technicians(self, scheduling_agent):
        """Test scheduling failure when no qualified technicians are available."""
        request = MaintenanceRequest(
            id="req_002",
            equipment_id="specialized_equipment",
            maintenance_type="corrective",
            priority=1,
            estimated_duration_hours=4.0,
            required_skills=["quantum_mechanics", "rocket_science"],  # No technician has these skills
            preferred_time_window_start=datetime.utcnow() + timedelta(days=1),
            preferred_time_window_end=datetime.utcnow() + timedelta(days=7),
            deadline=datetime.utcnow() + timedelta(days=10)
        )
        
        schedule = await scheduling_agent.schedule_maintenance_task(request)
        
        assert schedule.request_id == "req_002"
        assert schedule.status == ScheduleStatus.FAILED_TO_SCHEDULE
        assert "no_qualified_technicians" in schedule.constraints_violated
        assert "No technicians available with required skills" in schedule.scheduling_notes
    
    @pytest.mark.asyncio
    async def test_schedule_maintenance_task_no_available_slots(self, scheduling_agent):
        """Test scheduling failure when no time slots are available."""
        # Mock the calendar service to return no availability
        with patch.object(scheduling_agent.calendar_service, 'check_availability', return_value=False):
            
            request = MaintenanceRequest(
                id="req_003",
                equipment_id="pump_002",
                maintenance_type="preventive",
                priority=3,
                estimated_duration_hours=2.0,
                required_skills=["mechanical"],
                preferred_time_window_start=datetime.utcnow() + timedelta(days=1),
                preferred_time_window_end=datetime.utcnow() + timedelta(days=2),  # Very short window
                deadline=datetime.utcnow() + timedelta(days=5)
            )
            
            schedule = await scheduling_agent.schedule_maintenance_task(request)
            
            assert schedule.request_id == "req_003"
            assert schedule.status == ScheduleStatus.FAILED_TO_SCHEDULE
            assert "no_available_time_slots" in schedule.constraints_violated
    
    def test_calculate_optimization_score(self, scheduling_agent):
        """Test optimization score calculation."""
        request = MaintenanceRequest(
            id="req_004",
            equipment_id="test_equipment",
            maintenance_type="preventive",
            priority=2,
            estimated_duration_hours=2.0,
            required_skills=["mechanical", "electrical"],
            preferred_time_window_start=datetime.utcnow(),
            preferred_time_window_end=datetime.utcnow() + timedelta(days=7)
        )
        
        technician = {
            "id": "tech_001",
            "name": "John Smith",
            "skills": ["electrical", "mechanical", "hvac"],
            "experience_years": 5,
            "availability_score": 0.8
        }
        
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        score = scheduling_agent._calculate_optimization_score(request, technician, start_time, end_time)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be a good match given skills overlap
    
    @pytest.mark.asyncio
    async def test_handle_maintenance_predicted_event_success(self, scheduling_agent, sample_prediction_event_data):
        """Test successful handling of MaintenancePredictedEvent."""
        # Mock schedule_maintenance_task to return successful schedule
        mock_schedule = OptimizedSchedule(
            request_id="test_request",
            status=ScheduleStatus.SCHEDULED,
            assigned_technician_id="tech_001",
            scheduled_start_time=datetime.utcnow() + timedelta(days=1),
            scheduled_end_time=datetime.utcnow() + timedelta(days=1, hours=2),
            optimization_score=0.85,
            constraints_satisfied=["technician_skills_match", "within_time_window"]
        )
        
        with patch.object(scheduling_agent, 'schedule_maintenance_task', return_value=mock_schedule) as mock_schedule_func, \
             patch.object(scheduling_agent, '_publish_maintenance_scheduled_event') as mock_publish:
            
            await scheduling_agent.handle_maintenance_predicted_event(
                "MaintenancePredictedEvent", 
                sample_prediction_event_data
            )
            
            # Verify schedule_maintenance_task was called
            mock_schedule_func.assert_called_once()
            
            # Verify event was published for successful scheduling
            mock_publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_maintenance_predicted_event_failure(self, scheduling_agent, sample_prediction_event_data):
        """Test handling of MaintenancePredictedEvent when scheduling fails."""
        # Mock schedule_maintenance_task to return failed schedule
        mock_schedule = OptimizedSchedule(
            request_id="test_request",
            status=ScheduleStatus.FAILED_TO_SCHEDULE,
            constraints_violated=["no_available_time_slots"]
        )
        
        with patch.object(scheduling_agent, 'schedule_maintenance_task', return_value=mock_schedule) as mock_schedule_func, \
             patch.object(scheduling_agent, '_publish_maintenance_scheduled_event') as mock_publish:
            
            await scheduling_agent.handle_maintenance_predicted_event(
                "MaintenancePredictedEvent", 
                sample_prediction_event_data
            )
            
            # Verify schedule_maintenance_task was called
            mock_schedule_func.assert_called_once()
            
            # Verify event was NOT published for failed scheduling
            mock_publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_maintenance_scheduled_event(self, scheduling_agent):
        """Test publishing MaintenanceScheduledEvent."""
        original_event = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="test_equipment",
            predicted_failure_date=datetime.utcnow() + timedelta(days=15),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=10),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=20),
            prediction_confidence=0.8,
            time_to_failure_days=15.0,
            historical_data_points=100,
            agent_id="prediction_agent"
        )
        
        schedule = OptimizedSchedule(
            request_id="req_001",
            status=ScheduleStatus.SCHEDULED,
            assigned_technician_id="tech_001",
            scheduled_start_time=datetime.utcnow() + timedelta(days=1),
            scheduled_end_time=datetime.utcnow() + timedelta(days=1, hours=2),
            optimization_score=0.85,
            constraints_satisfied=["technician_skills_match"]
        )
        
        with patch.object(scheduling_agent, '_publish_event') as mock_publish:
            await scheduling_agent._publish_maintenance_scheduled_event(original_event, schedule)
            
            mock_publish.assert_called_once()
            event_type, event_data = mock_publish.call_args[0]
            
            assert event_type == "MaintenanceScheduledEvent"
            assert event_data["equipment_id"] == "test_equipment"
            assert event_data["assigned_technician_id"] == "tech_001"
            assert event_data["scheduling_method"] == "greedy"
    
    @pytest.mark.asyncio
    async def test_process(self, scheduling_agent):
        """Test the process method."""
        test_data = {"test": "data"}
        result = await scheduling_agent.process(test_data)
        
        # The process method should return the input data as-is
        assert result == test_data
