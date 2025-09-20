"""Unit tests for Human Interface Agent."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from apps.agents.interface.human_interface_agent import HumanInterfaceAgent
from core.events.event_models import (
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
)
from data.schemas import DecisionRequest, DecisionResponse, DecisionType


class TestHumanInterfaceAgent:
    """Test suite for Human Interface Agent."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus for testing."""
        event_bus = AsyncMock()
        event_bus.publish = AsyncMock()
        event_bus.subscribe = AsyncMock()
        return event_bus

    @pytest.fixture
    def agent(self, mock_event_bus):
        """Create a Human Interface Agent instance for testing."""
        return HumanInterfaceAgent(
            agent_id="test_human_interface_agent", event_bus=mock_event_bus
        )

    @pytest.fixture
    def sample_decision_request(self):
        """Create a sample decision request for testing."""
        return DecisionRequest(
            request_id="test_request_001",
            decision_type=DecisionType.MAINTENANCE_APPROVAL,
            context={"equipment_id": "pump_001", "issue": "unusual_vibration"},
            options=["approve", "reject", "schedule_later"],
            priority="high",
            requester_agent_id="anomaly_agent_001",
            correlation_id="corr_123",
        )

    @pytest.fixture
    def sample_decision_event(self, sample_decision_request):
        """Create a sample decision event for testing."""
        return HumanDecisionRequiredEvent(
            payload=sample_decision_request, correlation_id="corr_123"
        )

    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_event_bus):
        """Test that the agent initializes correctly."""
        agent = HumanInterfaceAgent(agent_id="test_agent", event_bus=mock_event_bus)

        assert agent.agent_id == "test_agent"
        assert agent.event_bus == mock_event_bus
        assert agent.simulated_operator_id == "sim_operator_001"
        assert agent.status == "initializing"

    @pytest.mark.asyncio
    async def test_agent_initialization_with_auto_id(self, mock_event_bus):
        """Test agent initialization with auto-generated ID."""
        agent = HumanInterfaceAgent(event_bus=mock_event_bus)

        assert agent.agent_id.startswith("human_interface_agent_")
        assert len(agent.agent_id.split("_")) == 4  # human_interface_agent_{8_char_hex}

    @pytest.mark.asyncio
    async def test_register_capabilities(self, agent):
        """Test capability registration."""
        await agent.register_capabilities()

        assert len(agent.capabilities) == 2

        # Check first capability
        cap1 = agent.capabilities[0]
        assert cap1.name == "human_decision_simulation"
        assert "HumanDecisionRequiredEvent" in cap1.input_types
        assert "HumanDecisionResponseEvent" in cap1.output_types

        # Check second capability
        cap2 = agent.capabilities[1]
        assert cap2.name == "maintenance_approval"
        assert "DecisionRequest" in cap2.input_types
        assert "DecisionResponse" in cap2.output_types

    @pytest.mark.asyncio
    async def test_start_agent(self, agent, mock_event_bus):
        """Test agent startup process."""
        await agent.start()

        assert agent.status == "running"
        mock_event_bus.subscribe.assert_called_once_with(
            "HumanDecisionRequiredEvent", agent.handle_decision_request
        )

    @pytest.mark.asyncio
    async def test_stop_agent(self, agent):
        """Test agent shutdown process."""
        await agent.stop()
        assert agent.status == "stopped"

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_handle_decision_request(
        self, mock_sleep, agent, mock_event_bus, sample_decision_event
    ):
        """Test handling of decision request events."""
        # Call the handler
        await agent.handle_decision_request(sample_decision_event)

        # Verify sleep was called for thinking time
        mock_sleep.assert_called_once_with(agent.thinking_time)

        # Verify event was published
        mock_event_bus.publish.assert_called_once()

        # Check the published event
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "HumanDecisionResponseEvent"

        published_event = call_args[0][1]
        assert isinstance(published_event, HumanDecisionResponseEvent)
        assert published_event.correlation_id == "corr_123"

        # Check the decision response
        response = published_event.payload
        assert isinstance(response, DecisionResponse)
        assert response.request_id == "test_request_001"
        assert response.operator_id == "sim_operator_001"
        assert (
            response.decision == "approve"
        )  # Should approve high priority maintenance
        assert "high priority" in response.justification.lower()

    @pytest.mark.asyncio
    async def test_simulate_maintenance_approval_high_priority(self, agent):
        """Test simulation of high priority maintenance approval."""
        request = DecisionRequest(
            request_id="test_001",
            decision_type=DecisionType.MAINTENANCE_APPROVAL,
            context={"equipment": "critical_pump"},
            options=["approve", "reject"],
            priority="high",
            requester_agent_id="test_agent",
        )

        decision, justification = await agent._simulate_human_decision(request)

        assert decision == "approve"
        assert "high priority" in justification.lower()

    @pytest.mark.asyncio
    async def test_simulate_maintenance_approval_emergency(self, agent):
        """Test simulation of emergency maintenance approval."""
        request = DecisionRequest(
            request_id="test_002",
            decision_type=DecisionType.MAINTENANCE_APPROVAL,
            context={"emergency": True, "equipment": "safety_system"},
            options=["approve", "reject"],
            priority="medium",
            requester_agent_id="test_agent",
        )

        decision, justification = await agent._simulate_human_decision(request)

        assert decision == "approve"
        assert "emergency" in justification.lower()

    @pytest.mark.asyncio
    async def test_simulate_budget_approval_within_limits(self, agent):
        """Test simulation of budget approval within limits."""
        request = DecisionRequest(
            request_id="test_003",
            decision_type=DecisionType.BUDGET_APPROVAL,
            context={"amount": 5000},
            options=["approve", "reject"],
            priority="medium",
            requester_agent_id="test_agent",
        )

        decision, justification = await agent._simulate_human_decision(request)

        assert decision == "approve"
        assert "5000" in justification
        assert "within limits" in justification.lower()

    @pytest.mark.asyncio
    async def test_simulate_budget_approval_exceeds_limits(self, agent):
        """Test simulation of budget approval exceeding limits."""
        request = DecisionRequest(
            request_id="test_004",
            decision_type=DecisionType.BUDGET_APPROVAL,
            context={"amount": 15000},
            options=["approve", "reject"],
            priority="medium",
            requester_agent_id="test_agent",
        )

        decision, justification = await agent._simulate_human_decision(request)

        assert decision == "reject"
        assert "15000" in justification
        assert "exceeds" in justification.lower()

    @pytest.mark.asyncio
    async def test_simulate_emergency_response(self, agent):
        """Test simulation of emergency response decision."""
        request = DecisionRequest(
            request_id="test_005",
            decision_type=DecisionType.EMERGENCY_RESPONSE,
            context={"incident": "fire_alarm"},
            options=["approve", "reject"],
            priority="critical",
            requester_agent_id="test_agent",
        )

        decision, justification = await agent._simulate_human_decision(request)

        assert decision == "approve"
        assert "emergency response approved" in justification.lower()

    @pytest.mark.asyncio
    async def test_simulate_decision_no_options(self, agent):
        """Test simulation when no options are provided."""
        request = DecisionRequest(
            request_id="test_006",
            decision_type=DecisionType.MAINTENANCE_APPROVAL,
            context={"equipment": "test"},
            options=[],
            priority="medium",
            requester_agent_id="test_agent",
        )

        decision, justification = await agent._simulate_human_decision(request)

        assert decision == "no_action"
        assert "no options available" in justification.lower()

    @pytest.mark.asyncio
    async def test_simulate_default_decision_type(self, agent):
        """Test simulation of a decision type that falls to default case."""
        # Use a valid enum value that isn't explicitly handled in the simulation logic
        request = DecisionRequest(
            request_id="test_007",
            # Valid enum but not explicitly handled
            decision_type=DecisionType.QUALITY_INSPECTION,
            context={"test": "data"},
            options=["option1", "option2"],
            priority="medium",
            requester_agent_id="test_agent",
        )

        decision, justification = await agent._simulate_human_decision(request)

        assert decision == "option1"  # Should default to first option
        assert "default decision" in justification.lower()

    @pytest.mark.asyncio
    async def test_process_decision_request_directly(
        self, agent, sample_decision_request, mock_event_bus
    ):
        """Test processing a decision request directly through process method."""
        result = await agent.process(sample_decision_request)

        assert result["status"] == "processed"
        assert result["request_id"] == "test_request_001"

        # Should have published an event
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_unknown_data_type(self, agent):
        """Test processing unknown data type."""
        result = await agent.process({"unknown": "data"})

        assert result["status"] == "no_processing_required"
        assert "dict" in result["data_type"]

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_handle_decision_request_error_handling(
        self, mock_sleep, agent, mock_event_bus
    ):
        """Test error handling in decision request processing."""
        # Create an invalid event that will cause an error
        invalid_event = Mock()
        invalid_event.payload = None
        invalid_event.correlation_id = "test_corr"

        # Should not raise an exception, but should log error
        await agent.handle_decision_request(invalid_event)

        # Verify no event was published due to error
        mock_event_bus.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_health_status(self, agent):
        """Test agent health status reporting."""
        health = await agent.get_health()

        assert health["agent_id"] == agent.agent_id
        assert health["status"] == agent.status
        assert "timestamp" in health
