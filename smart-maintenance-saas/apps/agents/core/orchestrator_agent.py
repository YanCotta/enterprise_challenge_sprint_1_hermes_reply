"""
OrchestratorAgent: Central coordinator for the Smart Maintenance SaaS system.

This agent manages high-level workflow orchestration, making rule-based decisions
to trigger appropriate agents based on system events and state.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from apps.agents.base_agent import BaseAgent, AgentCapability
from core.events.event_models import (
    AnomalyValidatedEvent,
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
    MaintenancePredictedEvent,
    ScheduleMaintenanceCommand,
)
from data.schemas import DecisionLog, DecisionRequest, DecisionType, SystemState, WorkflowStep

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Central coordinator agent that manages high-level workflow orchestration.
    
    The OrchestratorAgent subscribes to key system events and makes rule-based
    decisions about what actions to take next. It maintains system state and
    logs all decisions for audit purposes.
    
    Key responsibilities:
    - Monitor validated anomalies and decide on next steps
    - Evaluate maintenance predictions and determine approval workflow
    - Process human decisions and continue workflows accordingly
    - Maintain system state and decision audit trail
    """

    def __init__(self, agent_id: str, event_bus: Any):
        """
        Initialize the OrchestratorAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            event_bus: Event bus instance for inter-agent communication
        """
        super().__init__(agent_id, event_bus)
        
        # Initialize state management
        self.system_state: Dict[str, Any] = {}
        self.decision_log: List[DecisionLog] = []
        self._state_lock = asyncio.Lock()
        
        logger.info(f"OrchestratorAgent {agent_id} initialized with empty state")

    async def register_capabilities(self) -> None:
        """Register the capabilities of this agent."""
        self.capabilities = [
            AgentCapability(
                name="workflow_orchestration",
                description="Coordinates high-level workflows between agents",
                input_types=[
                    "AnomalyValidatedEvent",
                    "MaintenancePredictedEvent", 
                    "HumanDecisionResponseEvent"
                ],
                output_types=[
                    "HumanDecisionRequiredEvent",
                    "ScheduleMaintenanceCommand"
                ]
            ),
            AgentCapability(
                name="decision_management",
                description="Makes rule-based decisions for workflow routing",
                input_types=["system_state", "event_data"],
                output_types=["decision_log", "workflow_commands"]
            ),
            AgentCapability(
                name="state_management",
                description="Maintains system state and decision audit trail",
                input_types=["state_updates"],
                output_types=["system_state", "decision_log"]
            )
        ]
        logger.info(f"OrchestratorAgent {self.agent_id} registered {len(self.capabilities)} capabilities")

    async def start(self) -> None:
        """Start the agent and subscribe to relevant events."""
        await super().start()
        
        # Subscribe to key system events
        await self.event_bus.subscribe("AnomalyValidatedEvent", self.handle_anomaly_validated)
        await self.event_bus.subscribe("MaintenancePredictedEvent", self.handle_maintenance_predicted)
        await self.event_bus.subscribe("HumanDecisionResponseEvent", self.handle_human_decision_response)
        
        logger.info(f"OrchestratorAgent {self.agent_id} subscribed to key events")

    async def process(self, data: Any) -> Any:
        """
        Main processing logic for generic data.
        
        This method is required by BaseAgent but most processing happens
        in specific event handlers.
        """
        logger.debug(f"OrchestratorAgent {self.agent_id} processing generic data: {type(data)}")
        # Most processing happens in specific event handlers
        return None

    async def handle_anomaly_validated(self, event_type_or_event: Union[str, AnomalyValidatedEvent], event_data: AnomalyValidatedEvent = None) -> None:
        """
        Handle validated anomaly events.
        
        When an anomaly is validated with high confidence, log the decision
        to proceed to prediction phase. The PredictionAgent is already subscribed
        to this event, so no additional event publishing is needed.
        
        Args:
            event_type_or_event: Either event type string or the anomaly event object
            event_data: Event data when called with event type string
        """
        # Support both calling patterns from EventBus
        if isinstance(event_type_or_event, str):
            event = event_data
        else:
            event = event_type_or_event
        logger.info(
            f"OrchestratorAgent {self.agent_id} handling AnomalyValidatedEvent "
            f"with confidence {event.final_confidence}"
        )
        
        try:
            # Update system state
            await self._update_state(f"anomaly_{event.event_id}", {
                "validation_status": event.validation_status,
                "final_confidence": event.final_confidence,
                "equipment_id": event.triggering_reading_payload.get("sensor_id", "unknown"),
                "timestamp": event.timestamp,
                "handled_at": datetime.utcnow()
            })
            
            # Make decision based on confidence level
            if event.final_confidence > 0.7:
                decision_rationale = f"High confidence anomaly ({event.final_confidence:.2f}) - proceeding to prediction"
                action_taken = "Logged for prediction agent processing"
                
                logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
                
            else:
                decision_rationale = f"Low confidence anomaly ({event.final_confidence:.2f}) - monitoring only"
                action_taken = "Logged for monitoring, no immediate action"
                
                logger.warning(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
            
            # Log the decision
            await self._log_decision(
                decision_type="anomaly_processing",
                trigger_event=f"AnomalyValidatedEvent:{event.event_id}",
                decision_rationale=decision_rationale,
                action_taken=action_taken,
                context_data={
                    "validation_status": event.validation_status,
                    "final_confidence": event.final_confidence,
                    "equipment_id": event.triggering_reading_payload.get("sensor_id", "unknown")
                },
                correlation_id=event.correlation_id
            )
            
        except Exception as e:
            logger.error(
                f"OrchestratorAgent {self.agent_id}: Error handling AnomalyValidatedEvent: {e}",
                exc_info=True
            )

    async def handle_maintenance_predicted(self, event_type_or_event: Union[str, MaintenancePredictedEvent], event_data: MaintenancePredictedEvent = None) -> None:
        """
        Handle maintenance prediction events.
        
        Evaluates the urgency of predicted maintenance and decides whether to:
        - Request human approval for urgent maintenance (time_to_failure < 30 days)
        - Auto-approve and schedule non-urgent maintenance (time_to_failure >= 30 days)
        
        Args:
            event_type_or_event: Either event type string or the maintenance prediction event object
            event_data: Event data when called with event type string
        """
        # Support both calling patterns from EventBus
        if isinstance(event_type_or_event, str):
            event = event_data
        else:
            event = event_type_or_event
        logger.info(
            f"OrchestratorAgent {self.agent_id} handling MaintenancePredictedEvent "
            f"for equipment {event.equipment_id} with {event.time_to_failure_days:.1f} days to failure"
        )
        
        try:
            # Update system state
            await self._update_state(f"prediction_{event.event_id}", {
                "equipment_id": event.equipment_id,
                "time_to_failure_days": event.time_to_failure_days,
                "prediction_confidence": event.prediction_confidence,
                "maintenance_type": event.maintenance_type,
                "timestamp": event.timestamp,
                "handled_at": datetime.utcnow(),
                "correlation_id": event.correlation_id
            })
            
            # Decision logic based on urgency
            if event.time_to_failure_days < 30:
                # High urgency - require human approval
                decision_rationale = f"Urgent maintenance needed ({event.time_to_failure_days:.1f} days) - requesting human approval"
                action_taken = "Published HumanDecisionRequiredEvent for approval"
                
                # Create human decision request
                decision_request = DecisionRequest(
                    request_id=f"maintenance_approval_{event.event_id}",
                    decision_type=DecisionType.MAINTENANCE_APPROVAL,
                    context={
                        "equipment_id": event.equipment_id,
                        "time_to_failure_days": event.time_to_failure_days,
                        "prediction_confidence": event.prediction_confidence,
                        "maintenance_type": event.maintenance_type,
                        "predicted_failure_date": event.predicted_failure_date.isoformat(),
                        "recommended_actions": event.recommended_actions,
                        "urgency_reason": f"Only {event.time_to_failure_days:.1f} days until predicted failure"
                    },
                    options=["approve", "modify", "reject", "defer"],
                    priority="high",
                    requester_agent_id=self.agent_id,
                    correlation_id=event.correlation_id
                )
                
                # Publish human decision request
                human_decision_event = HumanDecisionRequiredEvent(
                    payload=decision_request,
                    correlation_id=event.correlation_id
                )
                
                await self._publish_event("HumanDecisionRequiredEvent", human_decision_event)
                logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
                
            else:
                # Low urgency - auto-approve and schedule
                decision_rationale = f"Non-urgent maintenance ({event.time_to_failure_days:.1f} days) - auto-approving"
                action_taken = "Published ScheduleMaintenanceCommand for automatic scheduling"
                
                # Create schedule maintenance command
                schedule_command = ScheduleMaintenanceCommand(
                    maintenance_data={
                        "equipment_id": event.equipment_id,
                        "maintenance_type": event.maintenance_type,
                        "time_to_failure_days": event.time_to_failure_days,
                        "prediction_confidence": event.prediction_confidence,
                        "predicted_failure_date": event.predicted_failure_date.isoformat(),
                        "recommended_actions": event.recommended_actions,
                        "priority": "medium"
                    },
                    urgency_level="medium",
                    auto_approved=True,
                    source_prediction_event_id=str(event.event_id),
                    correlation_id=event.correlation_id
                )
                
                await self._publish_event("ScheduleMaintenanceCommand", schedule_command)
                logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
            
            # Log the decision
            await self._log_decision(
                decision_type="maintenance_approval",
                trigger_event=f"MaintenancePredictedEvent:{event.event_id}",
                decision_rationale=decision_rationale,
                action_taken=action_taken,
                context_data={
                    "equipment_id": event.equipment_id,
                    "time_to_failure_days": event.time_to_failure_days,
                    "prediction_confidence": event.prediction_confidence,
                    "maintenance_type": event.maintenance_type,
                    "urgency_threshold": 30
                },
                correlation_id=event.correlation_id
            )
            
        except Exception as e:
            logger.error(
                f"OrchestratorAgent {self.agent_id}: Error handling MaintenancePredictedEvent: {e}",
                exc_info=True
            )

    async def handle_human_decision_response(self, event_type_or_event: Union[str, HumanDecisionResponseEvent], event_data: HumanDecisionResponseEvent = None) -> None:
        """
        Handle human decision responses.
        
        When a human makes a decision about maintenance approval, this handler
        processes the response and takes appropriate action.
        
        Args:
            event_type_or_event: Either event type string or the human decision response event object
            event_data: Event data when called with event type string
        """
        # Support both calling patterns from EventBus
        if isinstance(event_type_or_event, str):
            event = event_data
        else:
            event = event_type_or_event
        logger.info(
            f"OrchestratorAgent {self.agent_id} handling HumanDecisionResponseEvent "
            f"for request {event.payload.request_id}"
        )
        
        try:
            response = event.payload
            
            # Update system state
            await self._update_state(f"human_decision_{response.request_id}", {
                "request_id": response.request_id,
                "decision": response.decision,
                "justification": response.justification,
                "operator_id": response.operator_id,
                "confidence": response.confidence,
                "timestamp": response.timestamp,
                "handled_at": datetime.utcnow()
            })
            
            # Process the decision
            if response.decision.lower() in ["approve", "approved"]:
                decision_rationale = f"Human approved maintenance request {response.request_id}"
                action_taken = "Published ScheduleMaintenanceCommand for approved maintenance"
                
                # Extract the original prediction event ID from the request ID
                prediction_event_id = response.request_id.replace("maintenance_approval_", "")
                prediction_key = f"prediction_{prediction_event_id}"
                
                # Get original prediction data from system state
                system_state = await self.get_system_state()
                prediction_data = system_state.get(prediction_key, {})
                
                # Create maintenance command with original equipment data
                schedule_command = ScheduleMaintenanceCommand(
                    maintenance_data={
                        "equipment_id": prediction_data.get("equipment_id"),
                        "maintenance_type": prediction_data.get("maintenance_type"),
                        "time_to_failure_days": prediction_data.get("time_to_failure_days"),
                        "human_approved": True,
                        "approval_justification": response.justification,
                        "operator_id": response.operator_id,
                        "approval_confidence": response.confidence,
                        "priority": "high"  # Human approved urgent maintenance
                    },
                    urgency_level="high",
                    auto_approved=False,
                    source_prediction_event_id=prediction_event_id,
                    correlation_id=event.correlation_id
                )
                
                await self._publish_event("ScheduleMaintenanceCommand", schedule_command)
                logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
                
            elif response.decision.lower() in ["reject", "rejected", "deny", "denied"]:
                decision_rationale = f"Human rejected maintenance request {response.request_id}"
                action_taken = "Logged rejection, no scheduling command published"
                
                logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
                
            elif response.decision.lower() in ["modify", "modified"]:
                decision_rationale = f"Human requested modification of maintenance request {response.request_id}"
                action_taken = "Logged modification request, manual follow-up required"
                
                logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
                
            elif response.decision.lower() in ["defer", "deferred"]:
                decision_rationale = f"Human deferred maintenance request {response.request_id}"
                action_taken = "Logged deferral, maintenance postponed"
                
                logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
                
            else:
                decision_rationale = f"Unknown decision '{response.decision}' for request {response.request_id}"
                action_taken = "Logged unknown decision, no action taken"
                
                logger.warning(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
            
            # Log the decision
            await self._log_decision(
                decision_type="human_decision_processing",
                trigger_event=f"HumanDecisionResponseEvent:{event.event_id}",
                decision_rationale=decision_rationale,
                action_taken=action_taken,
                context_data={
                    "request_id": response.request_id,
                    "human_decision": response.decision,
                    "justification": response.justification,
                    "operator_id": response.operator_id,
                    "confidence": response.confidence
                },
                correlation_id=event.correlation_id
            )
            
        except Exception as e:
            logger.error(
                f"OrchestratorAgent {self.agent_id}: Error handling HumanDecisionResponseEvent: {e}",
                exc_info=True
            )

    async def _update_state(self, key: str, data: Dict[str, Any]) -> None:
        """
        Update system state with thread safety.
        
        Args:
            key: State key to update
            data: Data to store for this key
        """
        async with self._state_lock:
            self.system_state[key] = data
            logger.debug(f"OrchestratorAgent {self.agent_id}: Updated state key '{key}'")

    async def _get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get system state with thread safety.
        
        Args:
            key: State key to retrieve
            
        Returns:
            State data for the key, or None if not found
        """
        async with self._state_lock:
            return self.system_state.get(key)

    async def _log_decision(
        self,
        decision_type: str,
        trigger_event: str,
        decision_rationale: str,
        action_taken: str,
        context_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log a decision made by the orchestrator.
        
        Args:
            decision_type: Type of decision made
            trigger_event: Event that triggered the decision
            decision_rationale: Reasoning behind the decision
            action_taken: Action taken as a result
            context_data: Contextual data for the decision
            correlation_id: Optional correlation ID for tracking
        """
        decision_log_entry = DecisionLog(
            decision_type=decision_type,
            trigger_event=trigger_event,
            decision_rationale=decision_rationale,
            action_taken=action_taken,
            context_data=context_data,
            correlation_id=correlation_id
        )
        
        self.decision_log.append(decision_log_entry)
        
        logger.info(
            f"OrchestratorAgent {self.agent_id}: Decision logged - "
            f"Type: {decision_type}, Action: {action_taken}"
        )

    async def get_system_state(self) -> Dict[str, Any]:
        """
        Get a copy of the current system state.
        
        Returns:
            Copy of the current system state
        """
        async with self._state_lock:
            return self.system_state.copy()

    async def get_decision_log(self) -> List[DecisionLog]:
        """
        Get a copy of the current decision log.
        
        Returns:
            Copy of the current decision log
        """
        return self.decision_log.copy()

    async def get_health(self) -> Dict[str, Any]:
        """
        Get health status including state information.
        
        Returns:
            Health status with state metrics
        """
        base_health = await super().get_health()
        
        async with self._state_lock:
            state_count = len(self.system_state)
        
        decision_count = len(self.decision_log)
        
        base_health.update({
            "state_entries": state_count,
            "decision_log_entries": decision_count,
            "last_decision": self.decision_log[-1].timestamp.isoformat() if self.decision_log else None
        })
        
        return base_health
