"""Integration tests for Human Interface Agent."""

import asyncio
import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from apps.agents.interface.human_interface_agent import HumanInterfaceAgent
from core.events.event_models import HumanDecisionRequiredEvent, HumanDecisionResponseEvent
from data.schemas import DecisionRequest, DecisionResponse, DecisionType


class MockEventBus:
    """Mock event bus for integration testing."""
    
    def __init__(self):
        self.subscribers = {}
        self.published_events = []
    
    async def subscribe(self, event_type: str, handler):
        """Subscribe a handler to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event_type: str, event):
        """Publish an event to all subscribers."""
        self.published_events.append((event_type, event))
        
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                await handler(event)
    
    def get_published_events(self, event_type=None):
        """Get published events, optionally filtered by type."""
        if event_type:
            return [event for et, event in self.published_events if et == event_type]
        return self.published_events


class TestHumanInterfaceAgentIntegration:
    """Integration test suite for Human Interface Agent."""

    @pytest.fixture
    def event_bus(self):
        """Create a mock event bus for integration testing."""
        return MockEventBus()

    @pytest.fixture
    def agent(self, event_bus):
        """Create a Human Interface Agent instance for integration testing."""
        return HumanInterfaceAgent(
            agent_id="integration_test_agent",
            event_bus=event_bus
        )

    @pytest.fixture
    def decision_request(self):
        """Create a decision request for testing."""
        return DecisionRequest(
            request_id="integration_test_001",
            decision_type=DecisionType.MAINTENANCE_APPROVAL,
            context={
                "equipment_id": "pump_integration_test",
                "issue": "bearing_wear",
                "severity": "medium"
            },
            options=["approve", "reject", "schedule_later"],
            priority="high",
            requester_agent_id="anomaly_detection_agent",
            correlation_id="integration_corr_001"
        )

    @pytest.mark.asyncio
    async def test_full_decision_workflow(self, agent, event_bus, decision_request):
        """Test the complete decision workflow from request to response."""
        # Start the agent
        await agent.start()
        
        # Verify agent is running and subscribed
        assert agent.status == "running"
        assert "HumanDecisionRequiredEvent" in event_bus.subscribers
        
        # Create and publish a decision required event
        decision_event = HumanDecisionRequiredEvent(
            payload=decision_request,
            correlation_id="integration_corr_001"
        )
        
        # Publish the event
        await event_bus.publish("HumanDecisionRequiredEvent", decision_event)
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        
        # Verify a response event was published
        response_events = event_bus.get_published_events("HumanDecisionResponseEvent")
        assert len(response_events) == 1
        
        # Verify the response event content
        response_event = response_events[0]
        assert isinstance(response_event, HumanDecisionResponseEvent)
        assert response_event.correlation_id == "integration_corr_001"
        
        # Verify the decision response
        decision_response = response_event.payload
        assert isinstance(decision_response, DecisionResponse)
        assert decision_response.request_id == "integration_test_001"
        assert decision_response.operator_id == "sim_operator_001"
        assert decision_response.decision == "approve"  # High priority should be approved
        assert decision_response.correlation_id == "integration_corr_001"

    @pytest.mark.asyncio
    async def test_multiple_decision_requests(self, agent, event_bus):
        """Test handling multiple decision requests in sequence."""
        await agent.start()
        
        # Create multiple decision requests
        requests = []
        for i in range(3):
            request = DecisionRequest(
                request_id=f"multi_test_{i:03d}",
                decision_type=DecisionType.MAINTENANCE_APPROVAL,
                context={"equipment_id": f"equipment_{i}", "test_run": True},
                options=["approve", "reject"],
                priority="medium",
                requester_agent_id="test_agent",
                correlation_id=f"multi_corr_{i:03d}"
            )
            requests.append(request)
        
        # Publish all requests
        for request in requests:
            event = HumanDecisionRequiredEvent(
                payload=request,
                correlation_id=request.correlation_id
            )
            await event_bus.publish("HumanDecisionRequiredEvent", event)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Verify all responses were published
        response_events = event_bus.get_published_events("HumanDecisionResponseEvent")
        assert len(response_events) == 3
        
        # Verify each response corresponds to a request
        response_request_ids = {event.payload.request_id for event in response_events}
        expected_request_ids = {f"multi_test_{i:03d}" for i in range(3)}
        assert response_request_ids == expected_request_ids

    @pytest.mark.asyncio
    async def test_budget_approval_workflow(self, agent, event_bus):
        """Test budget approval decision workflow."""
        await agent.start()
        
        # Test budget within limits
        budget_request = DecisionRequest(
            request_id="budget_test_001",
            decision_type=DecisionType.BUDGET_APPROVAL,
            context={"amount": 5000, "department": "maintenance"},
            options=["approve", "reject"],
            priority="medium",
            requester_agent_id="budget_agent",
            correlation_id="budget_corr_001"
        )
        
        event = HumanDecisionRequiredEvent(
            payload=budget_request,
            correlation_id="budget_corr_001"
        )
        
        await event_bus.publish("HumanDecisionRequiredEvent", event)
        await asyncio.sleep(0.1)
        
        # Verify approval for amount within limits
        response_events = event_bus.get_published_events("HumanDecisionResponseEvent")
        assert len(response_events) == 1
        
        response = response_events[0].payload
        assert response.decision == "approve"
        assert "within limits" in response.justification.lower()

    @pytest.mark.asyncio
    async def test_emergency_response_workflow(self, agent, event_bus):
        """Test emergency response decision workflow."""
        await agent.start()
        
        # Test emergency response
        emergency_request = DecisionRequest(
            request_id="emergency_test_001",
            decision_type=DecisionType.EMERGENCY_RESPONSE,
            context={"incident_type": "equipment_failure", "location": "plant_floor_1"},
            options=["approve", "reject"],
            priority="critical",
            requester_agent_id="emergency_agent",
            correlation_id="emergency_corr_001"
        )
        
        event = HumanDecisionRequiredEvent(
            payload=emergency_request,
            correlation_id="emergency_corr_001"
        )
        
        await event_bus.publish("HumanDecisionRequiredEvent", event)
        await asyncio.sleep(0.1)
        
        # Verify emergency response approval
        response_events = event_bus.get_published_events("HumanDecisionResponseEvent")
        assert len(response_events) == 1
        
        response = response_events[0].payload
        assert response.decision == "approve"
        assert "emergency response approved" in response.justification.lower()

    @pytest.mark.asyncio
    async def test_agent_lifecycle_with_event_bus(self, agent, event_bus):
        """Test agent lifecycle integration with event bus."""
        # Initially, agent should not be subscribed
        assert "HumanDecisionRequiredEvent" not in event_bus.subscribers
        
        # Start agent
        await agent.start()
        assert agent.status == "running"
        assert "HumanDecisionRequiredEvent" in event_bus.subscribers
        assert len(event_bus.subscribers["HumanDecisionRequiredEvent"]) == 1
        
        # Stop agent
        await agent.stop()
        assert agent.status == "stopped"
        # Note: In a real implementation, unsubscription would happen here

    @pytest.mark.asyncio
    async def test_correlation_id_preservation(self, agent, event_bus):
        """Test that correlation IDs are preserved throughout the workflow."""
        await agent.start()
        
        correlation_id = "test_correlation_12345"
        
        request = DecisionRequest(
            request_id="correlation_test_001",
            decision_type=DecisionType.MAINTENANCE_APPROVAL,
            context={"test": "correlation_preservation"},
            options=["approve", "reject"],
            priority="medium",
            requester_agent_id="test_agent",
            correlation_id=correlation_id
        )
        
        event = HumanDecisionRequiredEvent(
            payload=request,
            correlation_id=correlation_id
        )
        
        await event_bus.publish("HumanDecisionRequiredEvent", event)
        await asyncio.sleep(0.1)
        
        # Verify correlation ID is preserved in response
        response_events = event_bus.get_published_events("HumanDecisionResponseEvent")
        assert len(response_events) == 1
        
        response_event = response_events[0]
        assert response_event.correlation_id == correlation_id
        assert response_event.payload.correlation_id == correlation_id

    @pytest.mark.asyncio
    async def test_concurrent_decision_handling(self, agent, event_bus):
        """Test handling of concurrent decision requests."""
        await agent.start()
        
        # Create multiple requests to be processed concurrently
        requests = []
        for i in range(5):
            request = DecisionRequest(
                request_id=f"concurrent_test_{i:03d}",
                decision_type=DecisionType.MAINTENANCE_APPROVAL,
                context={"equipment_id": f"concurrent_equipment_{i}"},
                options=["approve", "reject"],
                priority="medium",
                requester_agent_id="concurrent_test_agent",
                correlation_id=f"concurrent_corr_{i:03d}"
            )
            requests.append(request)
        
        # Publish all requests concurrently
        tasks = []
        for request in requests:
            event = HumanDecisionRequiredEvent(
                payload=request,
                correlation_id=request.correlation_id
            )
            task = asyncio.create_task(
                event_bus.publish("HumanDecisionRequiredEvent", event)
            )
            tasks.append(task)
        
        # Wait for all publications to complete
        await asyncio.gather(*tasks)
        
        # Wait for processing
        await asyncio.sleep(0.3)
        
        # Verify all responses were generated
        response_events = event_bus.get_published_events("HumanDecisionResponseEvent")
        assert len(response_events) == 5
        
        # Verify all requests were processed
        response_request_ids = {event.payload.request_id for event in response_events}
        expected_request_ids = {f"concurrent_test_{i:03d}" for i in range(5)}
        assert response_request_ids == expected_request_ids

    @pytest.mark.asyncio
    async def test_agent_capabilities_registration(self, agent):
        """Test that agent capabilities are properly registered."""
        await agent.register_capabilities()
        
        assert len(agent.capabilities) == 2
        
        # Verify capability names
        capability_names = {cap.name for cap in agent.capabilities}
        expected_names = {"human_decision_simulation", "maintenance_approval"}
        assert capability_names == expected_names
        
        # Verify input/output types
        for cap in agent.capabilities:
            assert len(cap.input_types) > 0
            assert len(cap.output_types) > 0
