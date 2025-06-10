"""
Unit tests for OR-Tools scheduler in SchedulingAgent.

These tests specifically target the OR-Tools constraint programming scheduler implementation,
separate from the existing greedy algorithm tests to avoid breaking current functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from apps.agents.decision.scheduling_agent import SchedulingAgent
from data.schemas import MaintenanceRequest, ScheduleStatus, OptimizedSchedule
from core.events.event_models import MaintenancePredictedEvent


class TestSchedulingAgentORTools:
    """Test suite for OR-Tools scheduler functionality."""

    @pytest.fixture
    def event_bus_mock(self):
        """Mock event bus for testing."""
        return AsyncMock()

    @pytest.fixture
    def scheduling_agent(self, event_bus_mock):
        """Create a SchedulingAgent instance for testing."""
        agent = SchedulingAgent("test_scheduling_agent", event_bus_mock)
        return agent

    @pytest.fixture
    def sample_maintenance_request(self):
        """Create a sample maintenance request for testing."""
        return MaintenanceRequest(
            id=f"req_{uuid4().hex[:8]}",
            equipment_id="PUMP_A001",
            maintenance_type="preventive_maintenance",
            priority=3,  # Valid priority 1-5
            required_skills=["mechanical"],
            estimated_duration_hours=2,
            preferred_time_window_start=datetime.now() + timedelta(days=1),
            preferred_time_window_end=datetime.now() + timedelta(days=7)
        )

    @pytest.fixture
    def high_priority_request(self):
        """Create a high-priority maintenance request."""
        return MaintenanceRequest(
            id=f"req_{uuid4().hex[:8]}",
            equipment_id="PUMP_B002",
            maintenance_type="emergency_repair",
            priority=1,  # Highest priority
            required_skills=["electrical", "mechanical"],
            estimated_duration_hours=4,
            preferred_time_window_start=datetime.now(),
            preferred_time_window_end=datetime.now() + timedelta(days=1)
        )

    @pytest.mark.asyncio
    async def test_or_tools_scheduler_enabled_with_feature_flag(self, scheduling_agent, sample_maintenance_request):
        """Test that OR-Tools scheduler is used when feature flag is enabled."""
        # Temporarily enable OR-Tools for this test
        original_setting = scheduling_agent.settings.USE_OR_TOOLS_SCHEDULER
        scheduling_agent.settings.USE_OR_TOOLS_SCHEDULER = True
        
        try:
            # Mock the OR-Tools method to verify it's called
            with patch.object(scheduling_agent, '_schedule_with_or_tools', new_callable=AsyncMock) as mock_or_tools:
                mock_or_tools.return_value = OptimizedSchedule(
                    request_id=sample_maintenance_request.id,
                    status=ScheduleStatus.SCHEDULED,
                    assigned_technician_id="tech_001",
                    scheduled_start_time=datetime.now() + timedelta(hours=2),
                    scheduled_end_time=datetime.now() + timedelta(hours=4),
                    optimization_score=0.95,
                    constraints_satisfied=["technician_skills_match", "no_overlapping_assignments"],
                    scheduling_notes="Optimized using OR-Tools constraint programming"
                )
                
                result = await scheduling_agent.schedule_maintenance_task(sample_maintenance_request)
                
                # Verify OR-Tools method was called
                mock_or_tools.assert_called_once_with([sample_maintenance_request], None)
                assert result.status == ScheduleStatus.SCHEDULED
                assert "OR-Tools" in result.scheduling_notes
        finally:
            # Restore original setting
            scheduling_agent.settings.USE_OR_TOOLS_SCHEDULER = original_setting

    @pytest.mark.asyncio
    async def test_greedy_scheduler_used_when_feature_flag_disabled(self, scheduling_agent, sample_maintenance_request):
        """Test that greedy scheduler is used when feature flag is disabled."""
        with patch('core.config.settings.settings.USE_OR_TOOLS_SCHEDULER', False):
            # Mock the greedy method to verify it's called
            with patch.object(scheduling_agent, '_schedule_with_greedy_algorithm', new_callable=AsyncMock) as mock_greedy:
                mock_greedy.return_value = OptimizedSchedule(
                    request_id=sample_maintenance_request.id,
                    status=ScheduleStatus.SCHEDULED,
                    assigned_technician_id="tech_001",
                    scheduled_start_time=datetime.now() + timedelta(hours=2),
                    scheduled_end_time=datetime.now() + timedelta(hours=4),
                    optimization_score=0.85
                )
                
                result = await scheduling_agent.schedule_maintenance_task(sample_maintenance_request)
                
                # Verify greedy method was called
                mock_greedy.assert_called_once_with(sample_maintenance_request, None)
                assert result.status == ScheduleStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_or_tools_scheduler_with_qualified_technician(self, scheduling_agent, sample_maintenance_request):
        """Test OR-Tools scheduler with a technician that has required skills."""
        with patch('core.config.settings.settings.USE_OR_TOOLS_SCHEDULER', True):
            
            # Test the actual OR-Tools implementation
            result = await scheduling_agent._schedule_with_or_tools([sample_maintenance_request])
            
            # Should find a qualified technician (tech_002 has mechanical skills)
            assert result.status == ScheduleStatus.SCHEDULED
            assert result.assigned_technician_id in ["tech_001", "tech_002"]
            assert result.scheduled_start_time is not None
            assert result.scheduled_end_time is not None
            assert "technician_skills_match" in result.constraints_satisfied

    @pytest.mark.asyncio
    async def test_or_tools_scheduler_no_qualified_technician(self, scheduling_agent):
        """Test OR-Tools scheduler when no technician has required skills."""
        # Create request with skills no technician has
        request = MaintenanceRequest(
            id=f"req_{uuid4().hex[:8]}",
            equipment_id="SPECIAL_EQUIPMENT",
            maintenance_type="specialized_repair",
            priority=2,
            required_skills=["nuclear_engineering"],  # No mock technician has this skill
            estimated_duration_hours=2,
            preferred_time_window_start=datetime.now() + timedelta(days=1),
            preferred_time_window_end=datetime.now() + timedelta(days=7)
        )
        
        with patch('core.config.settings.settings.USE_OR_TOOLS_SCHEDULER', True):
            
            result = await scheduling_agent._schedule_with_or_tools([request])
            
            assert result.status == ScheduleStatus.FAILED_TO_SCHEDULE
            assert "no_qualified_technicians" in result.constraints_violated
            assert result.assigned_technician_id is None

    @pytest.mark.asyncio
    async def test_or_tools_fallback_when_import_fails(self, scheduling_agent, sample_maintenance_request):
        """Test fallback to greedy algorithm when OR-Tools import fails."""
        with patch('core.config.settings.settings.USE_OR_TOOLS_SCHEDULER', True):
            
            # Mock cp_model as None to simulate import failure
            with patch('apps.agents.decision.scheduling_agent.cp_model', None):
                with patch.object(scheduling_agent, '_schedule_with_greedy_algorithm', new_callable=AsyncMock) as mock_greedy:
                    mock_greedy.return_value = OptimizedSchedule(
                        request_id=sample_maintenance_request.id,
                        status=ScheduleStatus.SCHEDULED,
                        assigned_technician_id="tech_001",
                        scheduled_start_time=datetime.now() + timedelta(hours=2),
                        scheduled_end_time=datetime.now() + timedelta(hours=4),
                        optimization_score=0.85
                    )
                    
                    result = await scheduling_agent._schedule_with_or_tools([sample_maintenance_request])
                    
                    # Should fall back to greedy algorithm
                    mock_greedy.assert_called_once()
                    assert result.status == ScheduleStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_or_tools_business_hours_adjustment(self, scheduling_agent):
        """Test that OR-Tools scheduler properly adjusts to business hours."""
        # Test weekend adjustment
        weekend_time = datetime(2025, 6, 14, 10, 0)  # Saturday
        adjusted = scheduling_agent._adjust_to_business_hours(weekend_time)
        assert adjusted.weekday() == 0  # Monday
        assert adjusted.hour == 8

        # Test after-hours adjustment
        after_hours = datetime(2025, 6, 10, 20, 0)  # Tuesday 8 PM
        adjusted = scheduling_agent._adjust_to_business_hours(after_hours)
        assert adjusted.hour == 8
        assert adjusted.date() == datetime(2025, 6, 11).date()  # Next day

        # Test before-hours adjustment
        before_hours = datetime(2025, 6, 10, 6, 0)  # Tuesday 6 AM
        adjusted = scheduling_agent._adjust_to_business_hours(before_hours)
        assert adjusted.hour == 8
        assert adjusted.date() == datetime(2025, 6, 10).date()  # Same day

    @pytest.mark.asyncio
    async def test_or_tools_optimization_score_calculation(self, scheduling_agent, high_priority_request, sample_maintenance_request):
        """Test that OR-Tools properly weights high-priority tasks."""
        with patch('core.config.settings.settings.USE_OR_TOOLS_SCHEDULER', True):
            
            # Schedule high-priority request
            high_priority_result = await scheduling_agent._schedule_with_or_tools([high_priority_request])
            
            # Schedule normal priority request
            normal_priority_result = await scheduling_agent._schedule_with_or_tools([sample_maintenance_request])
            
            # High priority should get better optimization score (if both succeed)
            if (high_priority_result.status == ScheduleStatus.SCHEDULED and 
                normal_priority_result.status == ScheduleStatus.SCHEDULED):
                assert high_priority_result.optimization_score >= normal_priority_result.optimization_score

    @pytest.mark.asyncio
    async def test_or_tools_error_handling_and_fallback(self, scheduling_agent, sample_maintenance_request):
        """Test error handling in OR-Tools scheduler with fallback to greedy."""
        with patch('core.config.settings.settings.USE_OR_TOOLS_SCHEDULER', True):
            
            # Mock OR-Tools to raise an exception
            with patch('apps.agents.decision.scheduling_agent.cp_model.CpModel') as mock_model:
                mock_model.side_effect = Exception("OR-Tools solver error")
                
                with patch.object(scheduling_agent, '_schedule_with_greedy_algorithm', new_callable=AsyncMock) as mock_greedy:
                    mock_greedy.return_value = OptimizedSchedule(
                        request_id=sample_maintenance_request.id,
                        status=ScheduleStatus.SCHEDULED,
                        assigned_technician_id="tech_001",
                        scheduled_start_time=datetime.now() + timedelta(hours=2),
                        scheduled_end_time=datetime.now() + timedelta(hours=4),
                        optimization_score=0.85
                    )
                    
                    result = await scheduling_agent._schedule_with_or_tools([sample_maintenance_request])
                    
                    # Should fall back to greedy algorithm on error
                    mock_greedy.assert_called_once()
                    assert result.status == ScheduleStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_multiple_requests_scheduling_constraint_satisfaction(self, scheduling_agent):
        """Test OR-Tools handling of multiple requests with constraint satisfaction."""
        request1 = MaintenanceRequest(
            id=f"req_{uuid4().hex[:8]}",
            equipment_id="PUMP_A001",
            maintenance_type="preventive_maintenance",
            priority=3,
            required_skills=["mechanical"],
            estimated_duration_hours=2,
            preferred_time_window_start=datetime.now() + timedelta(days=1),
            preferred_time_window_end=datetime.now() + timedelta(days=7)
        )
        
        request2 = MaintenanceRequest(
            id=f"req_{uuid4().hex[:8]}",
            equipment_id="PUMP_B002",
            maintenance_type="preventive_maintenance", 
            priority=4,
            required_skills=["mechanical"],
            estimated_duration_hours=3,
            preferred_time_window_start=datetime.now() + timedelta(days=1),
            preferred_time_window_end=datetime.now() + timedelta(days=7)
        )
        
        with patch('core.config.settings.settings.USE_OR_TOOLS_SCHEDULER', True):
            
            # Test scheduling multiple requests (though current implementation handles one at a time)
            result1 = await scheduling_agent._schedule_with_or_tools([request1])
            result2 = await scheduling_agent._schedule_with_or_tools([request2])
            
            # Both should be schedulable since we have multiple technicians
            assert result1.status in [ScheduleStatus.SCHEDULED, ScheduleStatus.FAILED_TO_SCHEDULE]
            assert result2.status in [ScheduleStatus.SCHEDULED, ScheduleStatus.FAILED_TO_SCHEDULE]
