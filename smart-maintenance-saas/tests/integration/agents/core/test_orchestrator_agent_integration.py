"""
Integration tests for the OrchestratorAgent.

These tests verify the complete workflow and integration between
the OrchestratorAgent, HumanInterfaceAgent, SchedulingAgent, and Event Bus.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from apps.agents.core.orchestrator_agent import OrchestratorAgent
from apps.agents.interface.human_interface_agent import HumanInterfaceAgent
from apps.agents.decision.scheduling_agent import SchedulingAgent
from core.events.event_bus import EventBus
from core.events.event_models import (
    MaintenancePredictedEvent,
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
    ScheduleMaintenanceCommand,
)
from data.schemas import DecisionResponse


class TestOrchestratorAgentIntegration:
    """Integration test suite for OrchestratorAgent workflow scenarios."""

    @pytest.fixture
    async def event_bus(self):
        """Create a real event bus for integration testing."""
        bus = EventBus()
        yield bus
        # Cleanup
        await bus.shutdown()

    @pytest.fixture
    async def orchestrator_agent(self, event_bus):
        """Create and start an OrchestratorAgent."""
        agent = OrchestratorAgent("orchestrator_test", event_bus)
        await agent.start()
        yield agent
        await agent.stop()

    @pytest.fixture
    async def human_interface_agent(self, event_bus):
        """Create and start a HumanInterfaceAgent."""
        agent = HumanInterfaceAgent("human_interface_test", event_bus)
        await agent.start()
        yield agent
        await agent.stop()

    @pytest.fixture
    async def scheduling_agent(self, event_bus):
        """Create and start a SchedulingAgent."""
        agent = SchedulingAgent("scheduling_test", event_bus)
        await agent.start()
        yield agent
        await agent.stop()    @pytest.mark.asyncio
    async def test_urgent_maintenance_workflow_with_human_approval(
        self, event_bus, orchestrator_agent, human_interface_agent
    ):
        """
        Test Scenario 1: Urgent maintenance requiring human approval.

        Flow: MaintenancePredictedEvent (urgent) -> HumanDecisionRequiredEvent
              -> HumanDecisionResponseEvent (approve) -> ScheduleMaintenanceCommand
        """
        # Track events received by each agent
        received_events = {
            'human_decisions': [],
            'schedule_commands': []
        }

        # Mock handlers to capture events
        async def capture_human_decision(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_events['human_decisions'].append(event)

        async def capture_schedule_command(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_events['schedule_commands'].append(event)

        # Subscribe to events we want to monitor
        await event_bus.subscribe("HumanDecisionRequiredEvent", capture_human_decision)
        await event_bus.subscribe("ScheduleMaintenanceCommand", capture_schedule_command)

        # Create urgent maintenance prediction
        urgent_prediction = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="critical_pump_001",
            predicted_failure_date=datetime.utcnow() + timedelta(days=15),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=10),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=20),
            prediction_confidence=0.95,
            time_to_failure_days=15.0,
            maintenance_type="corrective",
            historical_data_points=150,
            recommended_actions=["Replace impeller", "Check bearings"],
            agent_id="prediction_agent_test"
        )

        # Publish the urgent prediction
        await event_bus.publish("MaintenancePredictedEvent", urgent_prediction)

        # Wait for orchestrator to process and publish human decision request
        await asyncio.sleep(0.1)

        # Verify human decision was requested
        assert len(received_events['human_decisions']) == 1
        human_decision_event = received_events['human_decisions'][0]
        assert human_decision_event.payload.decision_type.value == "maintenance_approval"
        assert human_decision_event.payload.priority == "high"

        # Wait for the human interface agent to auto-approve (it has a 2 second delay)
        await asyncio.sleep(2.5)

        # Verify schedule command was published after approval
        assert len(received_events['schedule_commands']) == 1
        schedule_command = received_events['schedule_commands'][0]
        assert schedule_command.maintenance_data["equipment_id"] == "critical_pump_001"
        assert schedule_command.auto_approved is False  # Human approved
        assert schedule_command.urgency_level == "high"
        assert schedule_command.maintenance_data["human_approved"] is True

        # Verify orchestrator state was updated
        orchestrator_state = await orchestrator_agent.get_system_state()
        assert len(orchestrator_state) >= 2  # Prediction and human decision states

        # Verify decision log
        decision_log = await orchestrator_agent.get_decision_log()
        assert len(decision_log) >= 2  # Maintenance processing + human decision processing

    @pytest.mark.asyncio
    async def test_non_urgent_maintenance_workflow_auto_approval(
        self, event_bus, orchestrator_agent
    ):
        """
        Test Scenario 2: Non-urgent maintenance with automatic approval.
        
        Flow: MaintenancePredictedEvent (non-urgent) -> ScheduleMaintenanceCommand
        """
        # Track schedule commands
        received_schedule_commands = []

        async def capture_schedule_command(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_schedule_commands.append(event)

        await event_bus.subscribe("ScheduleMaintenanceCommand", capture_schedule_command)

        # Create non-urgent maintenance prediction
        non_urgent_prediction = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="routine_motor_002",
            predicted_failure_date=datetime.utcnow() + timedelta(days=45),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=40),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=50),
            prediction_confidence=0.80,
            time_to_failure_days=45.0,
            maintenance_type="preventive",
            historical_data_points=200,
            recommended_actions=["Lubrication", "Belt inspection"],
            agent_id="prediction_agent_test"
        )

        # Publish the non-urgent prediction
        await event_bus.publish("MaintenancePredictedEvent", non_urgent_prediction)

        # Wait for orchestrator to process and auto-approve
        await asyncio.sleep(0.1)

        # Verify schedule command was published directly (no human approval needed)
        assert len(received_schedule_commands) == 1
        schedule_command = received_schedule_commands[0]
        assert schedule_command.maintenance_data['equipment_id'] == "routine_motor_002"
        assert schedule_command.auto_approved is True  # Auto approved
        assert schedule_command.urgency_level == "medium"

        # Verify orchestrator state
        orchestrator_state = await orchestrator_agent.get_system_state()
        prediction_key = f"prediction_{non_urgent_prediction.event_id}"
        assert prediction_key in orchestrator_state

        # Verify decision log shows auto-approval
        decision_log = await orchestrator_agent.get_decision_log()
        assert len(decision_log) >= 1
        last_decision = decision_log[-1]
        assert "auto-approving" in last_decision.decision_rationale.lower()

    @pytest.mark.asyncio
    async def test_human_rejection_workflow(
        self, event_bus, orchestrator_agent
    ):
        """
        Test Scenario 3: Human rejection of maintenance request.
        
        Flow: MaintenancePredictedEvent (urgent) -> HumanDecisionRequiredEvent 
              -> HumanDecisionResponseEvent (reject) -> No ScheduleMaintenanceCommand
        
        Note: We don't use human_interface_agent fixture to avoid auto-approval.
        """
        # Track events
        received_events = {
            'human_decisions': [],
            'schedule_commands': []
        }

        async def capture_human_decision(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_events['human_decisions'].append(event)

        async def capture_schedule_command(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_events['schedule_commands'].append(event)

        await event_bus.subscribe("HumanDecisionRequiredEvent", capture_human_decision)
        await event_bus.subscribe("ScheduleMaintenanceCommand", capture_schedule_command)

        # Create urgent maintenance prediction
        urgent_prediction = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="questionable_equipment_003",
            predicted_failure_date=datetime.utcnow() + timedelta(days=20),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=15),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=25),
            prediction_confidence=0.70,  # Lower confidence
            time_to_failure_days=20.0,
            maintenance_type="corrective",
            historical_data_points=50,
            recommended_actions=["Full inspection"],
            agent_id="prediction_agent_test"
        )

        # Publish the prediction
        await event_bus.publish("MaintenancePredictedEvent", urgent_prediction)
        await asyncio.sleep(0.1)

        # Verify human decision was requested
        assert len(received_events['human_decisions']) == 1
        human_decision_event = received_events['human_decisions'][0]

        # Simulate human rejection by directly publishing a rejection response
        # (bypassing the always-approving HumanInterfaceAgent simulation)
        rejection_response = DecisionResponse(
            request_id=human_decision_event.payload.request_id,
            decision="reject",
            justification="Budget constraints, defer to next quarter",
            operator_id="operator_budget_test",
            confidence=0.95
        )

        rejection_event = HumanDecisionResponseEvent(payload=rejection_response)
        await event_bus.publish("HumanDecisionResponseEvent", rejection_event)
        await asyncio.sleep(0.1)

        # Verify NO schedule command was published after rejection
        assert len(received_events['schedule_commands']) == 0

        # Verify orchestrator logged the rejection
        decision_log = await orchestrator_agent.get_decision_log()
        rejection_decisions = [
            d for d in decision_log 
            if "rejected" in d.decision_rationale.lower()
        ]
        assert len(rejection_decisions) >= 1

    @pytest.mark.asyncio
    async def test_concurrent_maintenance_predictions(
        self, event_bus, orchestrator_agent, human_interface_agent
    ):
        """
        Test Scenario 4: Multiple concurrent maintenance predictions.
        
        Verify the orchestrator can handle multiple simultaneous events correctly.
        """
        # Track all events
        received_human_decisions = []
        received_schedule_commands = []

        async def capture_human_decision(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_human_decisions.append(event)

        async def capture_schedule_command(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_schedule_commands.append(event)

        await event_bus.subscribe("HumanDecisionRequiredEvent", capture_human_decision)
        await event_bus.subscribe("ScheduleMaintenanceCommand", capture_schedule_command)

        # Create multiple predictions - mix of urgent and non-urgent
        predictions = [
            # Urgent - should require human approval
            MaintenancePredictedEvent(
                original_anomaly_event_id=uuid4(),
                equipment_id="urgent_equipment_001",
                predicted_failure_date=datetime.utcnow() + timedelta(days=10),
                confidence_interval_lower=datetime.utcnow() + timedelta(days=8),
                confidence_interval_upper=datetime.utcnow() + timedelta(days=12),
                time_to_failure_days=10.0,
                prediction_confidence=0.90,
                maintenance_type="corrective",
                historical_data_points=100,
                recommended_actions=["Emergency repair"],
                agent_id="prediction_agent_test"
            ),
            # Non-urgent - should auto-approve
            MaintenancePredictedEvent(
                original_anomaly_event_id=uuid4(),
                equipment_id="routine_equipment_002",
                predicted_failure_date=datetime.utcnow() + timedelta(days=60),
                confidence_interval_lower=datetime.utcnow() + timedelta(days=55),
                confidence_interval_upper=datetime.utcnow() + timedelta(days=65),
                time_to_failure_days=60.0,
                prediction_confidence=0.85,
                maintenance_type="preventive",
                historical_data_points=150,
                recommended_actions=["Routine maintenance"],
                agent_id="prediction_agent_test"
            ),
            # Another urgent - should require human approval
            MaintenancePredictedEvent(
                original_anomaly_event_id=uuid4(),
                equipment_id="urgent_equipment_003",
                predicted_failure_date=datetime.utcnow() + timedelta(days=25),
                confidence_interval_lower=datetime.utcnow() + timedelta(days=22),
                confidence_interval_upper=datetime.utcnow() + timedelta(days=28),
                time_to_failure_days=25.0,
                prediction_confidence=0.88,
                maintenance_type="corrective",
                historical_data_points=80,
                recommended_actions=["Critical repair"],
                agent_id="prediction_agent_test"
            )
        ]

        # Publish all predictions concurrently
        await asyncio.gather(*[
            event_bus.publish("MaintenancePredictedEvent", pred)
            for pred in predictions
        ])

        # Wait for processing
        await asyncio.sleep(0.2)

        # Verify results:
        # - 2 human decisions should be requested (urgent cases)  
        # - 3 schedule commands should be published (1 auto + 2 human-approved)
        assert len(received_human_decisions) == 2
        assert len(received_schedule_commands) == 3

        # Verify the auto-approved one is the non-urgent equipment
        auto_schedule = received_schedule_commands[0]
        assert auto_schedule.maintenance_data['equipment_id'] == "routine_equipment_002"
        assert auto_schedule.auto_approved is True        # Verify the human decisions are for urgent equipment
        human_decision_equipment_ids = [
            event.payload.context["equipment_id"]
            for event in received_human_decisions
        ]
        assert "urgent_equipment_001" in human_decision_equipment_ids
        assert "urgent_equipment_003" in human_decision_equipment_ids

        # Verify orchestrator state contains all predictions
        orchestrator_state = await orchestrator_agent.get_system_state()
        prediction_states = [
            key for key in orchestrator_state.keys() 
            if key.startswith("prediction_")
        ]
        assert len(prediction_states) == 3

        # Verify decision log has entries for all predictions
        decision_log = await orchestrator_agent.get_decision_log()
        maintenance_decisions = [
            d for d in decision_log 
            if d.decision_type == "maintenance_approval"
        ]
        assert len(maintenance_decisions) == 3

    @pytest.mark.asyncio
    async def test_event_correlation_tracking(
        self, event_bus, orchestrator_agent, human_interface_agent
    ):
        """
        Test Scenario 5: Verify event correlation IDs are properly maintained.
        
        Ensure correlation tracking works through the complete workflow.
        """
        received_human_decisions = []

        async def capture_human_decision(event_type_or_event, event_data=None):
            # Support both calling patterns from EventBus
            if isinstance(event_type_or_event, str):
                event = event_data
            else:
                event = event_type_or_event
            received_human_decisions.append(event)

        await event_bus.subscribe("HumanDecisionRequiredEvent", capture_human_decision)

        # Create prediction with specific correlation ID
        original_correlation_id = str(uuid4())
        prediction = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id="correlation_test_equipment",
            predicted_failure_date=datetime.utcnow() + timedelta(days=15),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=12),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=18),
            time_to_failure_days=15.0,
            prediction_confidence=0.85,
            maintenance_type="corrective",
            historical_data_points=100,
            recommended_actions=["Test repair"],
            agent_id="prediction_agent_test",
            correlation_id=original_correlation_id
        )

        # Publish prediction
        await event_bus.publish("MaintenancePredictedEvent", prediction)
        await asyncio.sleep(0.1)

        # Verify human decision event maintains correlation
        assert len(received_human_decisions) == 1
        human_decision = received_human_decisions[0]
        assert human_decision.correlation_id == original_correlation_id

        # Verify orchestrator state includes correlation tracking
        orchestrator_state = await orchestrator_agent.get_system_state()
        prediction_key = f"prediction_{prediction.event_id}"
        prediction_state = orchestrator_state[prediction_key]
        assert prediction_state["correlation_id"] == original_correlation_id
