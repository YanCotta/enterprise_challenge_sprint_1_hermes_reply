"""
Unit tests for the OrchestratorAgent.

These tests verify the individual event handlers and decision-making logic
of the OrchestratorAgent in isolation.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from apps.agents.core.orchestrator_agent import OrchestratorAgent
from core.events.event_models import (
    AnomalyValidatedEvent,
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
    MaintenancePredictedEvent,
    ScheduleMaintenanceCommand,
)
from data.schemas import DecisionResponse, DecisionType


class TestOrchestratorAgent:
    """Test suite for OrchestratorAgent functionality."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus for testing."""
        event_bus = AsyncMock()
        event_bus.subscribe = AsyncMock()
        event_bus.publish = AsyncMock()
        return event_bus

    @pytest.fixture
    def orchestrator_agent(self, mock_event_bus):
        """Create an OrchestratorAgent instance for testing."""
        return OrchestratorAgent("test_orchestrator", mock_event_bus)

    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator_agent):
        """Test that the OrchestratorAgent initializes correctly."""
        assert orchestrator_agent.agent_id == "test_orchestrator"
        assert orchestrator_agent.system_state == {}
        assert orchestrator_agent.decision_log == []
        assert orchestrator_agent._state_lock is not None

    @pytest.mark.asyncio
    async def test_capabilities_registration(self, orchestrator_agent):
        """Test that capabilities are registered correctly."""
        await orchestrator_agent.register_capabilities()
        
        assert len(orchestrator_agent.capabilities) == 3
        
        capability_names = [cap.name for cap in orchestrator_agent.capabilities]
        assert "workflow_orchestration" in capability_names
        assert "decision_management" in capability_names
        assert "state_management" in capability_names

    @pytest.mark.asyncio
    async def test_start_subscribes_to_events(self, orchestrator_agent, mock_event_bus):
        """Test that starting the agent subscribes to the correct events."""
        await orchestrator_agent.start()
        
        # Verify subscriptions
        expected_calls = [
            ("AnomalyValidatedEvent", orchestrator_agent.handle_anomaly_validated),
            ("MaintenancePredictedEvent", orchestrator_agent.handle_maintenance_predicted),
            ("HumanDecisionResponseEvent", orchestrator_agent.handle_human_decision_response),
        ]
        
        assert mock_event_bus.subscribe.call_count == 3
        for event_type, handler in expected_calls:
            mock_event_bus.subscribe.assert_any_call(event_type, handler)

    @pytest.mark.asyncio
    async def test_handle_anomaly_validated_high_confidence(self, orchestrator_agent):
        """Test handling of high-confidence validated anomaly events."""
        # Create test event
        event = AnomalyValidatedEvent(
            original_anomaly_alert_payload={"anomaly_type": "temperature"},
            triggering_reading_payload={"sensor_id": "temp_001", "value": 85.0},
            validation_status="CONFIRMED",
            final_confidence=0.85,
            validation_reasons=["Exceeds threshold", "Pattern matches historical failures"],
            agent_id="validation_agent_1"
        )
        
        # Handle the event
        await orchestrator_agent.handle_anomaly_validated(event)
        
        # Verify state was updated
        state_key = f"anomaly_{event.event_id}"
        state_data = await orchestrator_agent._get_state(state_key)
        
        assert state_data is not None
        assert state_data["validation_status"] == "CONFIRMED"
        assert state_data["final_confidence"] == 0.85
        assert state_data["equipment_id"] == "temp_001"
        
        # Verify decision was logged
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert decision.decision_type == "anomaly_processing"
        assert "proceeding to prediction" in decision.decision_rationale.lower()

    @pytest.mark.asyncio
    async def test_handle_anomaly_validated_low_confidence(self, orchestrator_agent):
        """Test handling of low-confidence validated anomaly events."""
        # Create test event with low confidence
        event = AnomalyValidatedEvent(
            original_anomaly_alert_payload={"anomaly_type": "vibration"},
            triggering_reading_payload={"sensor_id": "vib_002", "value": 15.0},
            validation_status="UNCERTAIN",
            final_confidence=0.45,
            validation_reasons=["Unclear pattern"],
            agent_id="validation_agent_1"
        )
        
        # Handle the event
        await orchestrator_agent.handle_anomaly_validated(event)
        
        # Verify decision was logged with monitoring action
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert decision.decision_type == "anomaly_processing"
        assert "monitoring only" in decision.decision_rationale.lower()

    @pytest.mark.asyncio
    async def test_handle_maintenance_predicted_urgent(self, orchestrator_agent, mock_event_bus):
        """Test handling of urgent maintenance predictions (< 30 days)."""
        # Create urgent maintenance prediction
        event = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="pump_001",
            predicted_failure_date=datetime.utcnow() + timedelta(days=15),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=10),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=20),
            prediction_confidence=0.92,
            time_to_failure_days=15.0,
            maintenance_type="corrective",
            historical_data_points=100,
            recommended_actions=["Replace bearing", "Check alignment"],
            agent_id="prediction_agent_1"
        )
        
        # Handle the event
        await orchestrator_agent.handle_maintenance_predicted(event)
        
        # Verify human decision request was published
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "HumanDecisionRequiredEvent"
        
        published_event = call_args[0][1]
        assert isinstance(published_event, HumanDecisionRequiredEvent)
        assert published_event.payload.decision_type == DecisionType.MAINTENANCE_APPROVAL
        assert published_event.payload.priority == "high"
        
        # Verify state and decision log
        state_key = f"prediction_{event.event_id}"
        state_data = await orchestrator_agent._get_state(state_key)
        assert state_data["time_to_failure_days"] == 15.0
        
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert "requesting human approval" in decision.decision_rationale.lower()

    @pytest.mark.asyncio
    async def test_handle_maintenance_predicted_non_urgent(self, orchestrator_agent, mock_event_bus):
        """Test handling of non-urgent maintenance predictions (>= 30 days)."""
        # Create non-urgent maintenance prediction
        event = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="motor_002",
            predicted_failure_date=datetime.utcnow() + timedelta(days=45),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=40),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=50),
            prediction_confidence=0.78,
            time_to_failure_days=45.0,
            maintenance_type="preventive",
            historical_data_points=200,
            recommended_actions=["Lubrication", "Inspection"],
            agent_id="prediction_agent_1"
        )
        
        # Handle the event
        await orchestrator_agent.handle_maintenance_predicted(event)
        
        # Verify schedule maintenance command was published
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "ScheduleMaintenanceCommand"
        
        published_event = call_args[0][1]
        assert isinstance(published_event, ScheduleMaintenanceCommand)
        assert published_event.auto_approved is True
        assert published_event.urgency_level == "medium"
        assert published_event.source_prediction_event_id == str(event.event_id)
        
        # Verify decision log
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert "auto-approving" in decision.decision_rationale.lower()

    @pytest.mark.asyncio
    async def test_handle_human_decision_approve(self, orchestrator_agent, mock_event_bus):
        """Test handling of human approval decisions."""
        # Create approval response
        decision_response = DecisionResponse(
            request_id="maintenance_approval_12345",
            decision="approve",
            justification="Critical equipment failure risk",
            operator_id="operator_001",
            confidence=0.95
        )
        
        event = HumanDecisionResponseEvent(payload=decision_response)
        
        # Handle the event
        await orchestrator_agent.handle_human_decision_response(event)
        
        # Verify schedule maintenance command was published
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "ScheduleMaintenanceCommand"
        
        published_event = call_args[0][1]
        assert isinstance(published_event, ScheduleMaintenanceCommand)
        assert published_event.auto_approved is False
        assert published_event.urgency_level == "high"
        assert published_event.maintenance_data["human_approved"] is True
        
        # Verify state and decision log
        state_key = f"human_decision_{decision_response.request_id}"
        state_data = await orchestrator_agent._get_state(state_key)
        assert state_data["decision"] == "approve"
        assert state_data["operator_id"] == "operator_001"
        
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert "approved maintenance request" in decision.decision_rationale.lower()

    @pytest.mark.asyncio
    async def test_handle_human_decision_reject(self, orchestrator_agent, mock_event_bus):
        """Test handling of human rejection decisions."""
        # Create rejection response
        decision_response = DecisionResponse(
            request_id="maintenance_approval_12346",
            decision="reject",
            justification="Budget constraints",
            operator_id="operator_002",
            confidence=0.80
        )
        
        event = HumanDecisionResponseEvent(payload=decision_response)
        
        # Handle the event
        await orchestrator_agent.handle_human_decision_response(event)
        
        # Verify no schedule command was published
        mock_event_bus.publish.assert_not_called()
        
        # Verify decision was logged
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert "rejected maintenance request" in decision.decision_rationale.lower()
        assert "no scheduling command published" in decision.action_taken.lower()

    @pytest.mark.asyncio
    async def test_handle_human_decision_modify(self, orchestrator_agent, mock_event_bus):
        """Test handling of human modification requests."""
        # Create modification response
        decision_response = DecisionResponse(
            request_id="maintenance_approval_12347",
            decision="modify",
            justification="Change to less expensive parts",
            operator_id="operator_003",
            confidence=0.75
        )
        
        event = HumanDecisionResponseEvent(payload=decision_response)
        
        # Handle the event
        await orchestrator_agent.handle_human_decision_response(event)
        
        # Verify no immediate schedule command was published
        mock_event_bus.publish.assert_not_called()
        
        # Verify decision was logged
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert "modification" in decision.decision_rationale.lower()
        assert "manual follow-up required" in decision.action_taken.lower()

    @pytest.mark.asyncio
    async def test_handle_human_decision_defer(self, orchestrator_agent, mock_event_bus):
        """Test handling of human deferral decisions."""
        # Create deferral response
        decision_response = DecisionResponse(
            request_id="maintenance_approval_12348",
            decision="defer",
            justification="Wait for next shutdown window",
            operator_id="operator_004",
            confidence=0.85
        )
        
        event = HumanDecisionResponseEvent(payload=decision_response)
        
        # Handle the event
        await orchestrator_agent.handle_human_decision_response(event)
        
        # Verify no schedule command was published
        mock_event_bus.publish.assert_not_called()
        
        # Verify decision was logged
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert "deferred maintenance request" in decision.decision_rationale.lower()

    @pytest.mark.asyncio
    async def test_handle_human_decision_unknown(self, orchestrator_agent, mock_event_bus):
        """Test handling of unknown human decisions."""
        # Create unknown decision response
        decision_response = DecisionResponse(
            request_id="maintenance_approval_12349",
            decision="escalate",  # Unknown decision type
            justification="Need supervisor approval",
            operator_id="operator_005",
            confidence=0.60
        )
        
        event = HumanDecisionResponseEvent(payload=decision_response)
        
        # Handle the event
        await orchestrator_agent.handle_human_decision_response(event)
        
        # Verify no schedule command was published
        mock_event_bus.publish.assert_not_called()
        
        # Verify decision was logged with warning
        assert len(orchestrator_agent.decision_log) == 1
        decision = orchestrator_agent.decision_log[0]
        assert "unknown decision" in decision.decision_rationale.lower()
        assert "no action taken" in decision.action_taken.lower()

    @pytest.mark.asyncio
    async def test_state_management_thread_safety(self, orchestrator_agent):
        """Test that state management is thread-safe."""
        # Create multiple concurrent state updates
        async def update_state(key: str, value: str):
            await orchestrator_agent._update_state(key, {"test_value": value})
        
        # Run concurrent updates
        await asyncio.gather(
            update_state("key1", "value1"),
            update_state("key2", "value2"),
            update_state("key3", "value3"),
        )
        
        # Verify all updates were applied
        state1 = await orchestrator_agent._get_state("key1")
        state2 = await orchestrator_agent._get_state("key2")
        state3 = await orchestrator_agent._get_state("key3")
        
        assert state1["test_value"] == "value1"
        assert state2["test_value"] == "value2"
        assert state3["test_value"] == "value3"

    @pytest.mark.asyncio
    async def test_get_system_state(self, orchestrator_agent):
        """Test getting a copy of system state."""
        # Add some test state
        await orchestrator_agent._update_state("test_key", {"test": "data"})
        
        # Get state copy
        state_copy = await orchestrator_agent.get_system_state()
        
        # Verify it's a copy (not the same object)
        assert state_copy == orchestrator_agent.system_state
        assert state_copy is not orchestrator_agent.system_state

    @pytest.mark.asyncio
    async def test_get_decision_log(self, orchestrator_agent):
        """Test getting a copy of decision log."""
        # Add a test decision
        await orchestrator_agent._log_decision(
            decision_type="test",
            trigger_event="test_event",
            decision_rationale="test rationale",
            action_taken="test action",
            context_data={"test": "data"}
        )
        
        # Get decision log copy
        log_copy = await orchestrator_agent.get_decision_log()
        
        # Verify it's a copy
        assert len(log_copy) == 1
        assert log_copy[0].decision_type == "test"
        assert log_copy is not orchestrator_agent.decision_log

    @pytest.mark.asyncio
    async def test_get_health(self, orchestrator_agent):
        """Test health status reporting."""
        # Add some state and decisions
        await orchestrator_agent._update_state("test1", {"data": "1"})
        await orchestrator_agent._update_state("test2", {"data": "2"})
        await orchestrator_agent._log_decision(
            decision_type="test",
            trigger_event="test_event",
            decision_rationale="test",
            action_taken="test",
            context_data={}
        )
        
        # Get health status
        health = await orchestrator_agent.get_health()
        
        # Verify health information
        assert health["agent_id"] == "test_orchestrator"
        assert health["state_entries"] == 2
        assert health["decision_log_entries"] == 1
        assert health["last_decision"] is not None
        assert "timestamp" in health
