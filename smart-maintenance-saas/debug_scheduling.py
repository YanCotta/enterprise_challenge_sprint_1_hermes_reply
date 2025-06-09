#!/usr/bin/env python3

import sys
import os
sys.path.append(os.getcwd())

from datetime import datetime, timedelta
from unittest.mock import Mock
from apps.agents.decision.scheduling_agent import SchedulingAgent, CalendarService
from data.schemas import MaintenanceRequest

# Mock technician data
MOCK_TECHNICIANS = [
    {"id": "tech_001", "name": "John Smith", "skills": ["electrical", "mechanical"], "experience_years": 5, "availability_score": 0.8},
]

# Create mock event bus
mock_event_bus = Mock()

# Create scheduling agent
agent = SchedulingAgent(agent_id="debug_agent", event_bus=mock_event_bus)

# Create mock calendar service
mock_calendar_service = Mock(spec=CalendarService)
mock_calendar_service.check_availability.return_value = True
mock_calendar_service.book_slot.return_value = True

# Replace the calendar service
agent.calendar_service = mock_calendar_service

# Create test request
request = MaintenanceRequest(
    id="req_slot1", 
    equipment_id="eq_slot1", 
    maintenance_type="repair", 
    priority=1,
    estimated_duration_hours=2, 
    required_skills=["electrical"],
    preferred_time_window_start=datetime(2023, 10, 27, 9, 0, 0),
    preferred_time_window_end=datetime(2023, 10, 27, 17, 0, 0)
)

technician = MOCK_TECHNICIANS[0]

print("Testing _find_available_slot_for_technician...")
print(f"Request: {request}")
print(f"Technician: {technician}")

# Mock utcnow to simulate frozen time
import unittest.mock
with unittest.mock.patch('apps.agents.decision.scheduling_agent.datetime') as mock_datetime:
    mock_datetime.utcnow.return_value = datetime(2023, 10, 26, 12, 0, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    try:
        slot = agent._find_available_slot_for_technician(technician, request)
        print(f"Result: {slot}")
        
        print(f"check_availability call count: {mock_calendar_service.check_availability.call_count}")
        print(f"check_availability calls: {mock_calendar_service.check_availability.call_args_list}")
        print(f"book_slot call count: {mock_calendar_service.book_slot.call_count}")
        print(f"book_slot calls: {mock_calendar_service.book_slot.call_args_list}")
        
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
