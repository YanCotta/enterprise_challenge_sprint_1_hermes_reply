"""
OrchestratorAgent: Central coordinator for the Smart Maintenance SaaS system.

This agent manages high-level workflow orchestration, making rule-based decisions
to trigger appropriate agents based on system events and state.
"""

import asyncio
import logging
from datetime import datetime, timezone # Ensure timezone is imported
from typing import Any, Dict, List, Optional, Union

from core.base_agent_abc import BaseAgent, AgentCapability
from core.config import settings # Import settings
from core.events.event_models import (
    AnomalyValidatedEvent,
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
    MaintenancePredictedEvent,
    ScheduleMaintenanceCommand,
)
from data.schemas import DecisionLog, DecisionRequest, DecisionType, SystemState, WorkflowStep
from data.exceptions import WorkflowError, SmartMaintenanceBaseException, EventPublishError

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Central coordinator agent that manages high-level workflow orchestration.
    """

    def __init__(self, agent_id: str, event_bus: Any):
        super().__init__(agent_id, event_bus)
        self.system_state: Dict[str, Any] = {}
        self.decision_log: List[DecisionLog] = []
        self._state_lock = asyncio.Lock()
        logger.info(f"OrchestratorAgent {agent_id} initialized with empty state")

    async def register_capabilities(self) -> None:
        self.capabilities = [
            AgentCapability(
                name="workflow_orchestration",
                description="Coordinates high-level workflows between agents",
                input_types=[
                    AnomalyValidatedEvent.__name__,
                    MaintenancePredictedEvent.__name__,
                    HumanDecisionResponseEvent.__name__
                ],
                output_types=[
                    HumanDecisionRequiredEvent.__name__,
                    ScheduleMaintenanceCommand.__name__
                ]
            ),
            AgentCapability(
                name="decision_management",
                description="Manages decision-making processes and approval workflows",
                input_types=[
                    HumanDecisionResponseEvent.__name__,
                ],
                output_types=[
                    ScheduleMaintenanceCommand.__name__,
                ]
            ),
            AgentCapability(
                name="state_management",
                description="Maintains and manages system state across workflows",
                input_types=[
                    AnomalyValidatedEvent.__name__,
                    MaintenancePredictedEvent.__name__,
                ],
                output_types=[]
            ),
        ]
        logger.info(f"OrchestratorAgent {self.agent_id} registered {len(self.capabilities)} capabilities")

    async def start(self) -> None:
        await super().start()
        await self.event_bus.subscribe(AnomalyValidatedEvent.__name__, self.handle_anomaly_validated)
        await self.event_bus.subscribe(MaintenancePredictedEvent.__name__, self.handle_maintenance_predicted)
        await self.event_bus.subscribe(HumanDecisionResponseEvent.__name__, self.handle_human_decision_response)
        logger.info(f"OrchestratorAgent {self.agent_id} subscribed to key events")

    async def process(self, data: Any) -> Any:
        logger.debug(f"OrchestratorAgent {self.agent_id} processing generic data: {type(data)}")
        return None

    async def _publish_event_with_check(self, event_data_obj: Any):
        if self.event_bus:
            try:
                await self.event_bus.publish(event_data_obj)
                logger.info(f"Agent {self.agent_id} successfully published event '{event_data_obj.__class__.__name__}'.")
            except Exception as e:
                raise EventPublishError(
                    message=f"Agent {self.agent_id}: Failed to publish event '{event_data_obj.__class__.__name__}': {str(e)}",
                    original_exception=e
                ) from e
        else:
            logger.warning(f"Agent {self.agent_id}: Event bus not available. Cannot publish event '{event_data_obj.__class__.__name__}'.")

    async def handle_anomaly_validated(self, event: AnomalyValidatedEvent) -> None:
        _handler_name = self.handle_anomaly_validated.__name__

        # Ensure event and critical fields are present
        if not event or not hasattr(event, 'event_id') or not hasattr(event, 'triggering_reading_payload'):
            logger.error(f"OrchestratorAgent {self.agent_id}: Invalid or incomplete AnomalyValidatedEvent received.")
            raise WorkflowError("Invalid or incomplete AnomalyValidatedEvent received.")

        _event_id_for_log = event.event_id
        logger.info(f"OrchestratorAgent {self.agent_id} starting {_handler_name} for event ID {_event_id_for_log}, confidence {getattr(event, 'final_confidence', 'N/A')}")
        
        try:
            # sensor_id is critical for some logging/decision contexts.
            sensor_id = event.triggering_reading_payload.get("sensor_id")
            if not sensor_id:
                 logger.warning(f"AnomalyValidatedEvent {_event_id_for_log} missing sensor_id in triggering_reading_payload.")
                 # Decide if this is a fatal error for this handler. For now, it defaults to "unknown".

            await self._update_state(f"anomaly_{event.event_id}", {
                "validation_status": event.validation_status, "final_confidence": event.final_confidence,
                "equipment_id": sensor_id or "unknown", # Use retrieved sensor_id
                "timestamp": event.timestamp, "handled_at": datetime.now(timezone.utc)
            })
            
            if event.final_confidence > 0.7:
                decision_rationale = f"High confidence anomaly ({event.final_confidence:.2f}) - proceeding to prediction"
                action_taken = "Logged for prediction agent processing"
            else:
                decision_rationale = f"Low confidence anomaly ({event.final_confidence:.2f}) - monitoring only"
                action_taken = "Logged for monitoring, no immediate action"
            logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
            
            await self._log_decision(
                decision_type="anomaly_processing", trigger_event=f"{AnomalyValidatedEvent.__name__}:{event.event_id}",
                decision_rationale=decision_rationale, action_taken=action_taken,
                context_data={"validation_status": event.validation_status, "final_confidence": event.final_confidence,
                              "equipment_id": sensor_id or "unknown"},
                correlation_id=event.correlation_id
            )
            logger.info(f"OrchestratorAgent {self.agent_id} completed {_handler_name} for event ID {_event_id_for_log}")
        except SmartMaintenanceBaseException as app_exc:
            logger.error(f"OrchestratorAgent {self.agent_id}: App error in {_handler_name} for event ID {_event_id_for_log}: {app_exc}", exc_info=True)
        except Exception as e:
            logger.error(f"OrchestratorAgent {self.agent_id}: Generic error in {_handler_name} for event ID {_event_id_for_log}: {e}", exc_info=True)

    async def handle_maintenance_predicted(self, event: MaintenancePredictedEvent) -> None:
        _handler_name = self.handle_maintenance_predicted.__name__

        if not event or not all(hasattr(event, attr) for attr in ['event_id', 'equipment_id', 'time_to_failure_days', 'prediction_confidence', 'maintenance_type', 'predicted_failure_date']):
            logger.error(f"OrchestratorAgent {self.agent_id}: Invalid or incomplete MaintenancePredictedEvent received.")
            raise WorkflowError("Invalid or incomplete MaintenancePredictedEvent received.")

        _event_id_for_log = event.event_id
        equipment_id = event.equipment_id # Critical data

        logger.info(f"OrchestratorAgent {self.agent_id} starting {_handler_name} for event ID {_event_id_for_log} on equipment {equipment_id}")

        try:
            # Check for pending human approval for this equipment
            pending_approval_key = f"pending_human_approval_{equipment_id}"
            if await self._get_state(pending_approval_key):
                decision_rationale = f"New maintenance prediction for equipment {equipment_id} received while a previous decision is still pending. Ignored due to pending decision."
                action_taken = "Ignored due to pending decision"
                logger.warning(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
                await self._log_decision(
                    decision_type="duplicate_prediction_handling", trigger_event=f"{MaintenancePredictedEvent.__name__}:{_event_id_for_log}",
                    decision_rationale=decision_rationale, action_taken=action_taken,
                    context_data={"equipment_id": equipment_id, "pending_approval_key": pending_approval_key},
                    correlation_id=getattr(event, 'correlation_id', None)
                )
                return

            await self._update_state(f"prediction_{_event_id_for_log}", {
                "equipment_id": equipment_id, "time_to_failure_days": event.time_to_failure_days,
                "prediction_confidence": event.prediction_confidence, "maintenance_type": event.maintenance_type,
                "timestamp": event.timestamp, "handled_at": datetime.now(timezone.utc), "correlation_id": getattr(event, 'correlation_id', None)
            })

            ttf_days = event.time_to_failure_days
            confidence = event.prediction_confidence
            action_taken = "No action determined"
            requires_human_approval = True
            very_urgent_threshold = settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS * settings.ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR

            # Decision logic (as per previous implementation)
            if ttf_days < very_urgent_threshold:
                if confidence >= settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD:
                    decision_rationale = f"Very urgent maintenance ({ttf_days:.1f} days), high confidence ({confidence:.2f}). Auto-approving."
                    requires_human_approval = False
                else:
                     decision_rationale = f"Very urgent maintenance ({ttf_days:.1f} days), but confidence ({confidence:.2f}) is not high. Requesting human approval."
            elif ttf_days < settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS:
                if confidence >= settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD:
                    decision_rationale = f"Urgent maintenance ({ttf_days:.1f} days), high confidence ({confidence:.2f}). Auto-approving."
                    requires_human_approval = False
                elif confidence >= settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD:
                    decision_rationale = f"Urgent maintenance ({ttf_days:.1f} days), moderate confidence ({confidence:.2f}). Requesting human approval."
                else:
                    decision_rationale = f"Urgent maintenance ({ttf_days:.1f} days), low confidence ({confidence:.2f}). Requesting human approval."
            else:
                if confidence >= settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD:
                    decision_rationale = f"Non-urgent maintenance ({ttf_days:.1f} days), high confidence ({confidence:.2f}). Auto-approving."
                    requires_human_approval = False
                elif confidence >= settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD and \
                     ttf_days < settings.ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE:
                    decision_rationale = (f"Non-urgent maintenance ({ttf_days:.1f} days), moderate confidence ({confidence:.2f}), within auto-approval window. Auto-approving.")
                    requires_human_approval = False
                elif confidence >= settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD:
                     decision_rationale = (f"Non-urgent maintenance ({ttf_days:.1f} days), moderate confidence ({confidence:.2f}), outside auto-approval window. Requesting human approval.")
                else:
                    decision_rationale = f"Non-urgent maintenance ({ttf_days:.1f} days), low confidence ({confidence:.2f}). Requesting human approval."

            if requires_human_approval:
                action_taken = "Published HumanDecisionRequiredEvent"
                decision_request = DecisionRequest(
                    request_id=f"maintenance_approval_{_event_id_for_log}", decision_type=DecisionType.MAINTENANCE_APPROVAL,
                    context={
                        "equipment_id": equipment_id, "time_to_failure_days": ttf_days,
                        "prediction_confidence": confidence, "maintenance_type": event.maintenance_type,
                        "predicted_failure_date": event.predicted_failure_date.isoformat(),
                        "recommended_actions": event.recommended_actions, "urgency_reason": decision_rationale
                    },
                    options=["approve", "modify", "reject", "defer"], priority="high" if ttf_days < settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS else "medium",
                    requester_agent_id=self.agent_id, correlation_id=getattr(event, 'correlation_id', None)
                )
                human_decision_event = HumanDecisionRequiredEvent(payload=decision_request, correlation_id=getattr(event, 'correlation_id', None))
                await self._publish_event_with_check(human_decision_event)
                # Set flag for pending approval
                await self._update_state(pending_approval_key, {"request_id": decision_request.request_id, "timestamp": datetime.now(timezone.utc).isoformat()})
            else:
                action_taken = "Published ScheduleMaintenanceCommand (Auto-Approved)"
                schedule_command = ScheduleMaintenanceCommand(
                    maintenance_data={
                        "equipment_id": equipment_id, "maintenance_type": event.maintenance_type,
                        "time_to_failure_days": ttf_days, "prediction_confidence": confidence,
                        "predicted_failure_date": event.predicted_failure_date.isoformat(),
                        "recommended_actions": event.recommended_actions,
                        "priority": "high" if ttf_days < very_urgent_threshold else ("medium" if ttf_days < settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS else "low")
                    },
                    urgency_level="high" if ttf_days < settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS else "medium",
                    auto_approved=True, source_prediction_event_id=str(_event_id_for_log),
                    correlation_id=getattr(event, 'correlation_id', None)
                )
                await self._publish_event_with_check(schedule_command)

            logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")
            
            await self._log_decision(
                decision_type="maintenance_approval_routing", trigger_event=f"{MaintenancePredictedEvent.__name__}:{_event_id_for_log}",
                decision_rationale=decision_rationale, action_taken=action_taken,
                context_data={
                    "equipment_id": equipment_id, "time_to_failure_days": ttf_days,
                    "prediction_confidence": confidence, "maintenance_type": event.maintenance_type,
                    "rules_applied": {
                        "urgent_days_threshold": settings.ORCHESTRATOR_URGENT_MAINTENANCE_DAYS,
                        "very_urgent_factor": settings.ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR,
                        "high_confidence_threshold": settings.ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD,
                        "moderate_confidence_threshold": settings.ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD,
                        "auto_approval_max_days_moderate_conf": settings.ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE,
                    }
                },
                correlation_id=getattr(event, 'correlation_id', None)
            )
            logger.info(f"OrchestratorAgent {self.agent_id} completed {_handler_name} for event ID {_event_id_for_log}")
        except SmartMaintenanceBaseException as app_exc:
            logger.error(f"OrchestratorAgent {self.agent_id}: App error in {_handler_name} for event ID {_event_id_for_log}: {app_exc}", exc_info=True)
        except Exception as e:
            logger.error(f"OrchestratorAgent {self.agent_id}: Generic error in {_handler_name} for event ID {_event_id_for_log}: {e}", exc_info=True)

    async def handle_human_decision_response(self, event: HumanDecisionResponseEvent) -> None:
        _handler_name = self.handle_human_decision_response.__name__

        if not event or not hasattr(event, 'payload') or not hasattr(event.payload, 'request_id'):
            logger.error(f"OrchestratorAgent {self.agent_id}: Invalid or incomplete HumanDecisionResponseEvent received.")
            raise WorkflowError("Invalid or incomplete HumanDecisionResponseEvent received.")

        _event_id_for_log = getattr(event, 'event_id', 'N/A')
        response = event.payload
        _request_id_for_log = response.request_id
        logger.info(f"OrchestratorAgent {self.agent_id} starting {_handler_name} for event ID {_event_id_for_log}, request ID {_request_id_for_log}")

        try:
            await self._update_state(f"human_decision_{_request_id_for_log}", {
                "request_id": _request_id_for_log, "decision": response.decision,
                "justification": response.justification, "operator_id": response.operator_id,
                "confidence": response.confidence, "timestamp": response.timestamp,
                "handled_at": datetime.now(timezone.utc)
            })
            
            action_taken = "No specific action taken"
            # Determine original equipment_id from prediction_data
            original_equipment_id = "unknown_equipment"
            prediction_event_id = _request_id_for_log.replace("maintenance_approval_", "")
            prediction_key = f"prediction_{prediction_event_id}"
            system_state = await self.get_system_state()
            prediction_data = system_state.get(prediction_key, {})

            if prediction_data and 'equipment_id' in prediction_data:
                original_equipment_id = prediction_data['equipment_id']
            else:
                logger.warning(f"Could not determine original equipment_id for request_id {_request_id_for_log} from prediction_data.")
                # This might be an issue, but we'll proceed with logging the decision.
                # A WorkflowError was raised if prediction_data itself was missing in the 'approve' block.

            if response.decision.lower() in ["approve", "approved"]:
                decision_rationale = f"Human approved maintenance request {_request_id_for_log}"
                action_taken = "Published ScheduleMaintenanceCommand"
                if not prediction_data: # Already checked and raised WorkflowError if missing for approval
                    raise WorkflowError(f"Critical error: Original prediction data not found for approved request {_request_id_for_log}")

                schedule_command = ScheduleMaintenanceCommand(
                    maintenance_data={
                        "equipment_id": prediction_data.get("equipment_id"),
                        "maintenance_type": prediction_data.get("maintenance_type"),
                        "time_to_failure_days": prediction_data.get("time_to_failure_days"),
                        "human_approved": True, "approval_justification": response.justification,
                        "operator_id": response.operator_id, "approval_confidence": response.confidence,
                        "priority": "high"
                    },
                    urgency_level="high", auto_approved=False,
                    source_prediction_event_id=prediction_event_id,
                    correlation_id=getattr(event, 'correlation_id', None)
                )
                await self._publish_event_with_check(schedule_command)
            else:
                decision_rationale = f"Human decision '{response.decision}' for request {_request_id_for_log} logged."
                action_taken = f"Logged decision: {response.decision}"
            logger.info(f"OrchestratorAgent {self.agent_id}: {decision_rationale}")

            # Clear the pending approval flag
            if original_equipment_id != "unknown_equipment":
                pending_approval_key_to_clear = f"pending_human_approval_{original_equipment_id}"
                await self._remove_state_key(pending_approval_key_to_clear)
            else:
                logger.warning(f"Could not reliably clear pending_human_approval flag for request_id {_request_id_for_log} due to missing original_equipment_id.")

            await self._log_decision(
                decision_type="human_decision_processing", trigger_event=f"{HumanDecisionResponseEvent.__name__}:{_event_id_for_log}",
                decision_rationale=decision_rationale, action_taken=action_taken,
                context_data={
                    "request_id": _request_id_for_log, "human_decision": response.decision,
                    "justification": response.justification, "operator_id": response.operator_id,
                    "confidence": response.confidence, "original_equipment_id": original_equipment_id
                },
                correlation_id=getattr(event, 'correlation_id', None)
            )
            logger.info(f"OrchestratorAgent {self.agent_id} completed {_handler_name} for event ID {_event_id_for_log}")
        except SmartMaintenanceBaseException as app_exc:
            logger.error(f"OrchestratorAgent {self.agent_id}: App error in {_handler_name} for event ID {_event_id_for_log}: {app_exc}", exc_info=True)
        except Exception as e:
            logger.error(f"OrchestratorAgent {self.agent_id}: Generic error in {_handler_name} for event ID {_event_id_for_log}: {e}", exc_info=True)

    async def _update_state(self, key: str, data: Dict[str, Any]) -> None:
        async with self._state_lock:
            self.system_state[key] = data
        logger.debug(f"OrchestratorAgent {self.agent_id}: Updated state key '{key}' to: {data}")

    async def _get_state(self, key: str) -> Optional[Dict[str, Any]]:
        async with self._state_lock:
            return self.system_state.get(key)

    async def _remove_state_key(self, key: str) -> None:
        """Safely removes a key from the system state."""
        async with self._state_lock:
            if key in self.system_state:
                del self.system_state[key]
                logger.debug(f"OrchestratorAgent {self.agent_id}: Removed state key '{key}'")
            else:
                logger.debug(f"OrchestratorAgent {self.agent_id}: Attempted to remove non-existent state key '{key}'")


    async def _log_decision( self, decision_type: str, trigger_event: str, decision_rationale: str, action_taken: str, context_data: Dict[str, Any], correlation_id: Optional[str] = None) -> None:
        decision_log_entry = DecisionLog(
            decision_type=decision_type, trigger_event=trigger_event, decision_rationale=decision_rationale,
            action_taken=action_taken, context_data=context_data, correlation_id=correlation_id
        )
        self.decision_log.append(decision_log_entry)
        logger.info(f"OrchestratorAgent {self.agent_id}: Decision logged - Type: {decision_type}, Action: {action_taken}")

    async def get_system_state(self) -> Dict[str, Any]:
        async with self._state_lock:
            return self.system_state.copy()

    async def get_decision_log(self) -> List[DecisionLog]:
        return self.decision_log.copy()

    async def get_health(self) -> Dict[str, Any]:
        base_health = await super().get_health()
        base_health.update({
            "state_entries": len(self.system_state), 
            "decision_log_entries": len(self.decision_log),
            "last_decision": self.decision_log[-1] if self.decision_log else None
        })
        return base_health
