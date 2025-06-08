"""
Integration tests for the OrchestratorAgent.

These tests verify the complete workflow and integration between
the OrchestratorAgent, HumanInterfaceAgent, SchedulingAgent, and Event Bus.
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone # Added timezone
from uuid import uuid4
from typing import Optional

from apps.agents.core.orchestrator_agent import OrchestratorAgent
from apps.agents.interface.human_interface_agent import HumanInterfaceAgent
# SchedulingAgent not directly used in all new tests but good to have for context
from apps.agents.decision.scheduling_agent import SchedulingAgent
from core.events.event_bus import EventBus
from core.events.event_models import (
    MaintenancePredictedEvent,
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
    ScheduleMaintenanceCommand,
)
from data.schemas import DecisionResponse
from core.config import settings as global_settings # Import global settings to modify them

# Helper function to create MaintenancePredictedEvent
def _create_maintenance_predicted_event(
    equipment_id: str,
    time_to_failure_days: float,
    prediction_confidence: float,
    maintenance_type: str = "corrective",
    agent_id: str = "prediction_agent_test_helper",
    correlation_id: Optional[str] = None
) -> MaintenancePredictedEvent:
    """Helper function to create MaintenancePredictedEvent instances for tests."""
    now = datetime.now(timezone.utc)
    return MaintenancePredictedEvent(
        original_anomaly_event_id=uuid4(),
        equipment_id=equipment_id,
        predicted_failure_date=now + timedelta(days=time_to_failure_days),
        confidence_interval_lower=now + timedelta(days=time_to_failure_days - 2), # Example
        confidence_interval_upper=now + timedelta(days=time_to_failure_days + 2), # Example
        prediction_confidence=prediction_confidence,
        time_to_failure_days=time_to_failure_days,
        maintenance_type=maintenance_type,
        historical_data_points=100, # Example
        recommended_actions=["Check system", "Perform diagnostics"], # Example
        agent_id=agent_id,
        correlation_id=correlation_id or str(uuid4())
    )


class TestOrchestratorAgentIntegration:
    """Integration test suite for OrchestratorAgent workflow scenarios."""

    @pytest.fixture
    async def event_bus(self):
        """Create a real event bus for integration testing."""
        bus = EventBus()
        # It's important that event bus is started if agents rely on it being active
        # However, the current EventBus implementation doesn't have an explicit start for subscriptions
        # await bus.start()
        yield bus
        await bus.shutdown()

    @pytest.fixture
    async def orchestrator_agent(self, event_bus, test_settings): # Added test_settings
        """Create and start an OrchestratorAgent."""
        # Apply test_settings to global_settings for the duration of this agent's lifecycle
        # This is a common pattern if a fixture needs to modify global state temporarily.
        # Ensure test_settings fixture handles restoration of original settings.
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

    # Removed SchedulingAgent fixture for now as it's not directly used in the new tests
    # @pytest.fixture
    # async def scheduling_agent(self, event_bus):
    #     """Create and start a SchedulingAgent."""
    #     agent = SchedulingAgent("scheduling_test", event_bus)
    #     await agent.start()
    #     yield agent
    #     await agent.stop()

    # Test Scenario 1a: Urgent TTF, High Confidence -> Auto-approve.
    @pytest.mark.asyncio
    async def test_auto_approval_urgent_ttf_high_confidence(
        self, event_bus, orchestrator_agent, test_settings
    ):
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75
        test_settings.ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR = 0.5  # Explicitly set for clarity

        schedule_commands_received = []
        human_decision_events_received = []

        async def capture_schedule_command(event: ScheduleMaintenanceCommand):
            schedule_commands_received.append(event)

        async def capture_human_decision(event: HumanDecisionRequiredEvent):
            human_decision_events_received.append(event)

        await event_bus.subscribe(ScheduleMaintenanceCommand.__name__, capture_schedule_command)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)

        # TTF=20 days (urgent), Confidence=0.95 (high)
        # This should be auto-approved based on the logic:
        # ttf_days (20) < URGENT_MAINTENANCE_DAYS (30) -> True (Urgent)
        # confidence (0.95) >= HIGH_CONFIDENCE_THRESHOLD (0.90) -> True
        # Result: Auto-approve
        prediction_event = _create_maintenance_predicted_event(
            equipment_id="eq_urgent_high_conf",
            time_to_failure_days=20,
            prediction_confidence=0.95
        )
        await event_bus.publish(prediction_event)
        await asyncio.sleep(0.1) # Allow event processing

        assert not human_decision_events_received, "HumanDecisionRequiredEvent should not be published"
        assert len(schedule_commands_received) == 1, "ScheduleMaintenanceCommand should be published"
        assert schedule_commands_received[0].auto_approved is True
        assert schedule_commands_received[0].maintenance_data["equipment_id"] == "eq_urgent_high_conf"

        decision_log = await orchestrator_agent.get_decision_log()
        assert len(decision_log) > 0
        last_decision = decision_log[-1]
        assert "auto-approving" in last_decision.decision_rationale.lower()
        assert "high confidence" in last_decision.decision_rationale.lower()
        assert last_decision.context_data["prediction_confidence"] == 0.95


    @pytest.mark.asyncio
    async def test_urgent_maintenance_workflow_with_human_approval(
        self, event_bus, orchestrator_agent, human_interface_agent, test_settings # Added test_settings
    ):
        # Apply specific settings for this test if needed, or rely on defaults in conftest
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90  # Default, but good to be explicit
        # This test implies that TTF=15 days with confidence 0.95 requires human approval.
        # Let's check the logic. If default very_urgent_factor is 0.5, then 15 days is NOT very urgent.
        # So it falls into "Urgent" category. If confidence is high (0.95), it should auto-approve.
        # The original test might have implicitly relied on different thresholds or logic.
        # For this test to require human approval, confidence must be < high_confidence_threshold.
        # Let's adjust confidence to 0.85 (moderate) to force human approval for an urgent case.

        received_events = {
            'human_decisions': [],
            'schedule_commands': []
        }

        async def capture_human_decision(event: HumanDecisionRequiredEvent):
            received_events['human_decisions'].append(event)

        async def capture_schedule_command(event: ScheduleMaintenanceCommand):
            received_events['schedule_commands'].append(event)

        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)
        await event_bus.subscribe(ScheduleMaintenanceCommand.__name__, capture_schedule_command)

        urgent_prediction = _create_maintenance_predicted_event(
            equipment_id="critical_pump_001",
            time_to_failure_days=15.0, # Urgent
            prediction_confidence=0.85 # Moderate, should require human approval
        )

        await event_bus.publish(urgent_prediction)
        await asyncio.sleep(0.1)

        assert len(received_events['human_decisions']) == 1
        human_decision_event = received_events['human_decisions'][0]
        assert human_decision_event.payload.decision_type.value == "maintenance_approval"
        assert human_decision_event.payload.priority == "high" # 15 days is urgent

        # HumanInterfaceAgent will auto-approve
        await asyncio.sleep(2.5) # Allow HumanInterfaceAgent to process

        assert len(received_events['schedule_commands']) == 1
        schedule_command = received_events['schedule_commands'][0]
        assert schedule_command.maintenance_data["equipment_id"] == "critical_pump_001"
        assert schedule_command.auto_approved is False
        assert schedule_command.urgency_level == "high"
        assert schedule_command.maintenance_data["human_approved"] is True

        orchestrator_state = await orchestrator_agent.get_system_state()
        assert len(orchestrator_state) >= 2
        decision_log = await orchestrator_agent.get_decision_log()
        assert len(decision_log) >= 2


    @pytest.mark.asyncio
    async def test_non_urgent_maintenance_workflow_auto_approval(
        self, event_bus, orchestrator_agent, test_settings # Added test_settings
    ):
        # Logic: Not urgent, high confidence -> auto-approve
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        # Other thresholds can be default

        received_schedule_commands = []
        async def capture_schedule_command(event: ScheduleMaintenanceCommand):
            received_schedule_commands.append(event)
        await event_bus.subscribe(ScheduleMaintenanceCommand.__name__, capture_schedule_command)

        # TTF=45 days (not urgent), Confidence=0.90 (high)
        non_urgent_prediction = _create_maintenance_predicted_event(
            equipment_id="routine_motor_002",
            time_to_failure_days=45.0,
            prediction_confidence=0.90
        )

        await event_bus.publish(non_urgent_prediction)
        await asyncio.sleep(0.1)

        assert len(received_schedule_commands) == 1
        schedule_command = received_schedule_commands[0]
        assert schedule_command.maintenance_data['equipment_id'] == "routine_motor_002"
        assert schedule_command.auto_approved is True
        assert schedule_command.urgency_level == "medium" # Corrected from "low", as per current logic

        orchestrator_state = await orchestrator_agent.get_system_state()
        prediction_key = f"prediction_{non_urgent_prediction.event_id}"
        assert prediction_key in orchestrator_state
        decision_log = await orchestrator_agent.get_decision_log()
        assert len(decision_log) >= 1
        last_decision = decision_log[-1]
        assert "auto-approving" in last_decision.decision_rationale.lower()
        assert "high confidence" in last_decision.decision_rationale.lower()


    @pytest.mark.asyncio
    async def test_human_rejection_workflow(
        self, event_bus, orchestrator_agent, test_settings # Added test_settings
    ):
        # Logic: Urgent, Moderate confidence -> Human decision required. Then human rejects.
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75

        received_events = {'human_decisions': [], 'schedule_commands': []}
        async def capture_human_decision(event: HumanDecisionRequiredEvent):
            received_events['human_decisions'].append(event)
        async def capture_schedule_command(event: ScheduleMaintenanceCommand):
            received_events['schedule_commands'].append(event)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)
        await event_bus.subscribe(ScheduleMaintenanceCommand.__name__, capture_schedule_command)

        # TTF=20 days (urgent), Confidence=0.80 (moderate) -> Human decision
        prediction = _create_maintenance_predicted_event(
            equipment_id="questionable_equipment_003",
            time_to_failure_days=20.0,
            prediction_confidence=0.80,
        )

        await event_bus.publish(prediction)
        await asyncio.sleep(0.1)

        assert len(received_events['human_decisions']) == 1
        human_decision_event = received_events['human_decisions'][0]

        rejection_response = DecisionResponse(
            request_id=human_decision_event.payload.request_id,
            decision="reject", justification="Budget constraints",
            operator_id="operator_budget_test", confidence=0.95
        )
        rejection_event = HumanDecisionResponseEvent(payload=rejection_response)
        await event_bus.publish(rejection_event)
        await asyncio.sleep(0.1)

        assert len(received_events['schedule_commands']) == 0
        decision_log = await orchestrator_agent.get_decision_log()
        assert any("reject" in d.decision_rationale.lower() for d in decision_log)
        assert any(d.context_data.get("human_decision") == "reject" for d in decision_log if d.decision_type == "human_decision_processing")


    @pytest.mark.asyncio
    async def test_concurrent_maintenance_predictions(
        self, event_bus, orchestrator_agent, human_interface_agent, test_settings # Added test_settings
    ):
        # Setting thresholds for varied outcomes
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR = 0.5 # Very urgent if < 15 days
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75
        test_settings.ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE = 40 # Allow non-urgent moderate to auto-approve if TTF < 40

        received_human_decisions = []
        received_schedule_commands = []
        async def capture_human_decision(event: HumanDecisionRequiredEvent): received_human_decisions.append(event)
        async def capture_schedule_command(event: ScheduleMaintenanceCommand): received_schedule_commands.append(event)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)
        await event_bus.subscribe(ScheduleMaintenanceCommand.__name__, capture_schedule_command)

        predictions = [
            # 1. Very Urgent (10d), High Conf (0.92) -> Auto-approve
            _create_maintenance_predicted_event("eq_v_urgent_h_conf", 10.0, 0.92),
            # 2. Urgent (25d), Moderate Conf (0.80) -> Human Approval
            _create_maintenance_predicted_event("eq_urgent_m_conf", 25.0, 0.80),
            # 3. Not Urgent (50d), High Conf (0.95) -> Auto-approve
            _create_maintenance_predicted_event("eq_n_urgent_h_conf", 50.0, 0.95),
            # 4. Not Urgent (35d), Moderate Conf (0.85), TTF < AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE (40d) -> Auto-approve
            _create_maintenance_predicted_event("eq_n_urgent_m_conf_auto", 35.0, 0.85),
            # 5. Not Urgent (45d), Moderate Conf (0.85), TTF > AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE (40d) -> Human Approval
            _create_maintenance_predicted_event("eq_n_urgent_m_conf_human", 45.0, 0.85),
        ]

        await asyncio.gather(*[event_bus.publish(pred) for pred in predictions])
        await asyncio.sleep(0.2) # Initial processing by orchestrator

        # Expected: Human approval for eq_urgent_m_conf, eq_n_urgent_m_conf_human
        assert len(received_human_decisions) == 2
        human_decision_eq_ids = sorted([e.payload.context["equipment_id"] for e in received_human_decisions])
        assert human_decision_eq_ids == sorted(["eq_urgent_m_conf", "eq_n_urgent_m_conf_human"])

        # Allow HumanInterfaceAgent to process approvals
        await asyncio.sleep(2.5)

        # Expected: Schedule commands for all 5 (3 auto + 2 human approved)
        assert len(received_schedule_commands) == 5

        auto_approved_cmds = [cmd for cmd in received_schedule_commands if cmd.auto_approved]
        human_approved_cmds = [cmd for cmd in received_schedule_commands if not cmd.auto_approved]

        assert len(auto_approved_cmds) == 3
        auto_approved_eq_ids = sorted([cmd.maintenance_data["equipment_id"] for cmd in auto_approved_cmds])
        assert auto_approved_eq_ids == sorted(["eq_v_urgent_h_conf", "eq_n_urgent_h_conf", "eq_n_urgent_m_conf_auto"])

        assert len(human_approved_cmds) == 2
        human_approved_eq_ids = sorted([cmd.maintenance_data["equipment_id"] for cmd in human_approved_cmds])
        assert human_approved_eq_ids == sorted(["eq_urgent_m_conf", "eq_n_urgent_m_conf_human"])


    @pytest.mark.asyncio
    async def test_event_correlation_tracking(
        self, event_bus, orchestrator_agent, human_interface_agent, test_settings # Added test_settings
    ):
        # This test implies that TTF=15 days with confidence 0.85 requires human approval.
        # Urgent (15 < 30), Moderate Conf (0.85 is between 0.75 and 0.90) -> Human Approval
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75

        received_human_decisions = []
        async def capture_human_decision(event: HumanDecisionRequiredEvent):
            received_human_decisions.append(event)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)

        original_correlation_id = str(uuid4())
        prediction = _create_maintenance_predicted_event(
            equipment_id="correlation_test_equipment",
            time_to_failure_days=15.0,
            prediction_confidence=0.85, # Moderate confidence
            correlation_id=original_correlation_id
        )

        await event_bus.publish(prediction)
        await asyncio.sleep(0.1)

        assert len(received_human_decisions) == 1
        human_decision = received_human_decisions[0]
        assert human_decision.correlation_id == original_correlation_id

        orchestrator_state = await orchestrator_agent.get_system_state()
        prediction_key = f"prediction_{prediction.event_id}"
        assert prediction_key in orchestrator_state
        prediction_state = orchestrator_state[prediction_key]
        assert prediction_state["correlation_id"] == original_correlation_id

    # TODO: Add test_settings fixture if not already in conftest.py for integration tests
    # For now, assuming direct modification of global_settings for test setup is acceptable for this step.
    # A proper fixture would look like:
    # @pytest.fixture
    # def test_settings(monkeypatch):
    #     original_settings = {key: getattr(global_settings, key) for key in dir(global_settings) if not key.startswith('_')}
    #     # Use a Pydantic model copy for modification if settings is a Pydantic model instance
    #     # For simplicity, this example directly patches global_settings
    #     # You could also monkeypatch specific attributes as needed for each test
    #     # e.g., monkeypatch.setattr(global_settings, 'ORCHESTRATOR_URGENT_MAINTENANCE_DAYS', 20)
    #     yield global_settings # The test will modify this instance
    #     # Restore original settings
    #     for key, value in original_settings.items():
    #         setattr(global_settings, key, value)
    # Test Scenario 1b: Urgent TTF, Moderate Confidence -> Human Approval
    @pytest.mark.asyncio
    async def test_human_approval_urgent_ttf_moderate_confidence(
        self, event_bus, orchestrator_agent, test_settings
    ):
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75
        # Very urgent factor default or 0.5. 20 days is not very urgent if urgent is 30.

        schedule_commands_received = []
        human_decision_events_received = []

        async def capture_schedule_command(event: ScheduleMaintenanceCommand): schedule_commands_received.append(event)
        async def capture_human_decision(event: HumanDecisionRequiredEvent): human_decision_events_received.append(event)
        await event_bus.subscribe(ScheduleMaintenanceCommand.__name__, capture_schedule_command)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)

        # TTF=20 days (urgent), Confidence=0.80 (moderate)
        # Logic: Urgent (20 < 30), Moderate Conf (0.75 <= 0.80 < 0.90) -> Human Approval
        prediction_event = _create_maintenance_predicted_event(
            equipment_id="eq_urgent_mod_conf", time_to_failure_days=20, prediction_confidence=0.80
        )
        await event_bus.publish(prediction_event)
        await asyncio.sleep(0.1)

        assert len(human_decision_events_received) == 1, "HumanDecisionRequiredEvent should be published"
        assert not schedule_commands_received, "ScheduleMaintenanceCommand should not be published directly"
        assert human_decision_events_received[0].payload.context["equipment_id"] == "eq_urgent_mod_conf"

        decision_log = await orchestrator_agent.get_decision_log()
        last_decision = decision_log[-1]
        assert "requesting human approval" in last_decision.decision_rationale.lower()
        assert "moderate confidence" in last_decision.decision_rationale.lower()

    # Test Scenario 1c: Urgent TTF, Low Confidence -> Human Approval.
    @pytest.mark.asyncio
    async def test_human_approval_urgent_ttf_low_confidence(
        self, event_bus, orchestrator_agent, test_settings
    ):
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75 # Low is below this

        human_decision_events_received = []
        async def capture_human_decision(event: HumanDecisionRequiredEvent): human_decision_events_received.append(event)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)

        # TTF=20 days (urgent), Confidence=0.70 (low)
        prediction_event = _create_maintenance_predicted_event(
            equipment_id="eq_urgent_low_conf", time_to_failure_days=20, prediction_confidence=0.70
        )
        await event_bus.publish(prediction_event)
        await asyncio.sleep(0.1)

        assert len(human_decision_events_received) == 1
        decision_log = await orchestrator_agent.get_decision_log()
        last_decision = decision_log[-1]
        assert "requesting human approval" in last_decision.decision_rationale.lower()
        assert "low confidence" in last_decision.decision_rationale.lower()

    # Test Scenario 1d: Not Urgent TTF, Low Confidence -> Human Approval.
    @pytest.mark.asyncio
    async def test_human_approval_not_urgent_ttf_low_confidence(
        self, event_bus, orchestrator_agent, test_settings
    ):
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75 # Low is below this

        human_decision_events_received = []
        async def capture_human_decision(event: HumanDecisionRequiredEvent): human_decision_events_received.append(event)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)

        # TTF=40 days (not urgent), Confidence=0.70 (low)
        prediction_event = _create_maintenance_predicted_event(
            equipment_id="eq_not_urgent_low_conf", time_to_failure_days=40, prediction_confidence=0.70
        )
        await event_bus.publish(prediction_event)
        await asyncio.sleep(0.1)

        assert len(human_decision_events_received) == 1
        decision_log = await orchestrator_agent.get_decision_log()
        last_decision = decision_log[-1]
        assert "requesting human approval" in last_decision.decision_rationale.lower()
        assert "low confidence" in last_decision.decision_rationale.lower()

    # Test Scenario 1e: Very Urgent TTF, Moderate Confidence -> Human Approval.
    @pytest.mark.asyncio
    async def test_human_approval_very_urgent_ttf_moderate_confidence(
        self, event_bus, orchestrator_agent, test_settings
    ):
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR = 0.5 # Very urgent if < 15 days
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75

        human_decision_events_received = []
        async def capture_human_decision(event: HumanDecisionRequiredEvent): human_decision_events_received.append(event)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)

        # TTF=10 days (very urgent), Confidence=0.80 (moderate)
        # Logic: Very Urgent (10 < 15), Moderate Conf (not high) -> Human Approval
        prediction_event = _create_maintenance_predicted_event(
            equipment_id="eq_v_urgent_mod_conf", time_to_failure_days=10, prediction_confidence=0.80
        )
        await event_bus.publish(prediction_event)
        await asyncio.sleep(0.1)

        assert len(human_decision_events_received) == 1
        decision_log = await orchestrator_agent.get_decision_log()
        last_decision = decision_log[-1]
        assert "requesting human approval" in last_decision.decision_rationale.lower()
        assert "very urgent" in last_decision.decision_rationale.lower()
        assert "not high" in last_decision.decision_rationale.lower() # or "moderate confidence"

    # Test Scenario for state validation: duplicate prediction before human decision
    @pytest.mark.asyncio
    async def test_duplicate_prediction_before_human_decision(
        self, event_bus, orchestrator_agent, test_settings
    ):
        test_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS = 30
        test_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD = 0.90
        test_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD = 0.75 # Low is below this

        human_decision_events_received = []
        async def capture_human_decision(event: HumanDecisionRequiredEvent):
            human_decision_events_received.append(event)
        await event_bus.subscribe(HumanDecisionRequiredEvent.__name__, capture_human_decision)

        equipment_id_test = "eq_duplicate_test"

        # 1. First Prediction: Urgent, Low Confidence -> Requires Human Approval
        prediction_event_1 = _create_maintenance_predicted_event(
            equipment_id=equipment_id_test, time_to_failure_days=20, prediction_confidence=0.70
        )
        await event_bus.publish(prediction_event_1)
        await asyncio.sleep(0.1)

        assert len(human_decision_events_received) == 1 # First decision request
        first_decision_request_id = human_decision_events_received[0].payload.request_id

        # Check state for pending approval
        pending_approval_key = f"pending_human_approval_{equipment_id_test}"
        state_after_first_pred = await orchestrator_agent.get_system_state()
        assert pending_approval_key in state_after_first_pred
        assert state_after_first_pred[pending_approval_key]["request_id"] == first_decision_request_id

        # 2. Second Prediction for the same equipment, while first is pending
        prediction_event_2 = _create_maintenance_predicted_event(
            equipment_id=equipment_id_test, time_to_failure_days=18, prediction_confidence=0.72 # Slightly different
        )
        await event_bus.publish(prediction_event_2)
        await asyncio.sleep(0.1)

        # Assert that NO NEW HumanDecisionRequiredEvent was published
        assert len(human_decision_events_received) == 1

        decision_log = await orchestrator_agent.get_decision_log()
        # There should be one for the first prediction, and one for ignoring the second.
        assert len(decision_log) >=2

        ignored_decision_logged = False
        for decision in decision_log:
            if decision.decision_type == "duplicate_prediction_handling" and \
               "ignored due to pending decision" in decision.decision_rationale.lower() and \
               decision.context_data["equipment_id"] == equipment_id_test:
                ignored_decision_logged = True
                break
        assert ignored_decision_logged, "Decision to ignore duplicate prediction was not logged correctly."

        # 3. Human responds to the FIRST request
        rejection_response = DecisionResponse(
            request_id=first_decision_request_id, # Use ID from the first request
            decision="reject", justification="Technician overloaded",
            operator_id="test_operator", confidence=1.0
        )
        rejection_event = HumanDecisionResponseEvent(payload=rejection_response, correlation_id=human_decision_events_received[0].correlation_id)
        await event_bus.publish(rejection_event)
        await asyncio.sleep(0.1)

        # Check state: pending approval flag should be cleared
        state_after_response = await orchestrator_agent.get_system_state()
        assert pending_approval_key not in state_after_response

        # 4. Third Prediction for the same equipment, after decision processed
        # This one should now generate a new human decision request
        prediction_event_3 = _create_maintenance_predicted_event(
            equipment_id=equipment_id_test, time_to_failure_days=15, prediction_confidence=0.65 # Low conf
        )
        await event_bus.publish(prediction_event_3)
        await asyncio.sleep(0.1)

        assert len(human_decision_events_received) == 2 # Now a second one should be generated
        assert human_decision_events_received[1].payload.context["equipment_id"] == equipment_id_test
        assert human_decision_events_received[1].payload.request_id != first_decision_request_id

        # And state should be set again for the new request
        state_after_third_pred = await orchestrator_agent.get_system_state()
        assert pending_approval_key in state_after_third_pred
        assert state_after_third_pred[pending_approval_key]["request_id"] == human_decision_events_received[1].payload.request_id

    # Note: A conftest.py for integration tests might be needed to provide the test_settings fixture
    # if it's not already globally available or easily mockable.
    # For this exercise, I'm assuming test_settings can be passed and will modify global_settings.
    # A better approach for test_settings is to use monkeypatching if it's a module-level variable.
    # If settings is a Pydantic object, its attributes can be directly set.
    @pytest.fixture
    def test_settings(self, monkeypatch):
        """Fixture to temporarily modify global settings for a test."""
        # Store original values of settings we might change
        original_values = {
            "ORCHESTRATOR_URGENT_MAINTENANCE_DAYS": global_settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS,
            "ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD": global_settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD,
            "ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD": global_settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD,
            "ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE": global_settings.ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE,
            "ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR": global_settings.ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR,
        }

        # Yield the global_settings object itself, which tests can modify
        yield global_settings

        # Restore original values after the test
        for key, value in original_values.items():
            setattr(global_settings, key, value)

# Existing tests might need slight adjustments if their expected behavior relied on the old logic.
# For example, urgency levels in ScheduleMaintenanceCommand or rationales in decision logs.
# The test_concurrent_maintenance_predictions was updated to reflect new logic.
# The test_urgent_maintenance_workflow_with_human_approval was updated.
# The test_non_urgent_maintenance_workflow_auto_approval was updated.
# The test_human_rejection_workflow was updated for consistency.
# The test_event_correlation_tracking was updated.
#
# The integration test file `test_orchestrator_agent_integration.py` has been updated:
#
# 1.  **Helper Function:** Added `_create_maintenance_predicted_event` to simplify event creation.
# 2.  **`test_settings` Fixture:** A `test_settings` fixture using `monkeypatch` has been added to allow modification of global settings for the duration of a test and ensure they are restored afterwards. This is crucial for testing different configuration scenarios.
# 3.  **New Test Scenarios (1a-1e):**
#     *   `test_auto_approval_urgent_ttf_high_confidence` (Scenario 1a)
#     *   `test_human_approval_urgent_ttf_moderate_confidence` (Scenario 1b)
#     *   `test_human_approval_urgent_ttf_low_confidence` (Scenario 1c)
#     *   `test_human_approval_not_urgent_ttf_low_confidence` (Scenario 1d)
#     *   `test_human_approval_very_urgent_ttf_moderate_confidence` (Scenario 1e)
#     These tests set specific orchestrator thresholds using the `test_settings` fixture and assert the correct behavior (auto-approval or human approval request) based on the new logic. They also check the decision log rationale.
# 4.  **Duplicate Prediction Test:**
#     *   Added `test_duplicate_prediction_before_human_decision` to verify that if a maintenance prediction arrives while another for the same equipment is awaiting human decision, the new one is ignored and the state flag (`pending_human_approval_...`) is managed correctly.
# 5.  **Existing Tests Updated:** The original tests (`test_urgent_maintenance_workflow_with_human_approval`, `test_non_urgent_maintenance_workflow_auto_approval`, `test_human_rejection_workflow`, `test_concurrent_maintenance_predictions`, `test_event_correlation_tracking`) were reviewed and slightly adjusted to use the `_create_maintenance_predicted_event` helper and the `test_settings` fixture, ensuring their assertions align with the new refined logic in `OrchestratorAgent`. For example, confidence values were chosen to ensure the intended path (human approval vs. auto-approval) was triggered according to the new rules.
#
# All planned tests have been implemented. The file is now ready.
