"""Human Interface Agent for managing human-in-the-loop decision points."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Union

from core.base_agent_abc import AgentCapability, BaseAgent
from core.events.event_models import (
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
)
from data.schemas import DecisionRequest, DecisionResponse, DecisionType

logger = logging.getLogger(__name__)


class HumanInterfaceAgent(BaseAgent):
    """
    Human Interface Agent (HIA) manages simulated human-in-the-loop decision points.

    This agent listens for requests for decisions, simulates a human response,
    and publishes the decision back to the system. In a production environment,
    this would interface with a real human operator through a UI.
    """

    def __init__(self, agent_id: str = None, event_bus: Any = None):
        """
        Initialize the Human Interface Agent.

        Args:
            agent_id (str, optional): Unique identifier for the agent.
                Defaults to auto-generated.
            event_bus (Any): The event bus instance for inter-agent communication.
        """
        if agent_id is None:
            agent_id = f"human_interface_agent_{uuid.uuid4().hex[:8]}"

        super().__init__(agent_id, event_bus)
        self.simulated_operator_id = "sim_operator_001"
        self.decision_timeout = 30.0  # seconds
        self.thinking_time = 2.0  # simulate human thinking time

        logger.info(f"HumanInterfaceAgent {self.agent_id} initialized")

    async def register_capabilities(self) -> None:
        """Register the capabilities of the Human Interface Agent."""
        self.capabilities = [
            AgentCapability(
                name="human_decision_simulation",
                description="Simulates human decision-making for approval workflows",
                input_types=["HumanDecisionRequiredEvent"],
                output_types=["HumanDecisionResponseEvent"],
            ),
            AgentCapability(
                name="maintenance_approval",
                description="Handles maintenance approval decisions",
                input_types=["DecisionRequest"],
                output_types=["DecisionResponse"],
            ),
        ]

        logger.debug(
            f"Agent {self.agent_id}: Registered {len(self.capabilities)} capabilities"
        )

    async def start(self) -> None:
        """Start the Human Interface Agent and subscribe to relevant events."""
        logger.info(f"Starting HumanInterfaceAgent {self.agent_id}...")

        await super().start()

        # Subscribe to human decision required events
        if self.event_bus:
            await self.event_bus.subscribe(
                "HumanDecisionRequiredEvent", self.handle_decision_request
            )
            logger.info(
                f"Agent {self.agent_id} subscribed to HumanDecisionRequiredEvent"
            )
        else:
            logger.warning(
                f"Agent {self.agent_id}: No event bus available for subscription"
            )

    async def stop(self) -> None:
        """Stop the Human Interface Agent and clean up resources."""
        logger.info(f"Stopping HumanInterfaceAgent {self.agent_id}...")

        # Unsubscribe from events if needed
        if self.event_bus:
            # Note: Actual unsubscription would depend on event bus implementation
            logger.debug(
                f"Agent {self.agent_id}: Event unsubscription would occur here"
            )

        await super().stop()

    async def handle_decision_request(
        self,
        event_type_or_event: Union[str, HumanDecisionRequiredEvent],
        event_data: HumanDecisionRequiredEvent = None,
    ) -> None:
        """
        Handle a human decision request event.

        Args:
            event_type_or_event: Either event type string or the decision request
                event object
            event_data: Event data when called with event type string
        """
        # Support both calling patterns from EventBus
        if isinstance(event_type_or_event, str):
            event = event_data
        else:
            event = event_type_or_event

        try:
            decision_request = event.payload
            logger.info(
                f"Agent {self.agent_id} received decision request "
                f"{decision_request.request_id} of type "
                f"{decision_request.decision_type} "
                f"from {decision_request.requester_agent_id}. "
                f"Correlation ID: {event.correlation_id}"
            )

            # Log the decision context for transparency
            logger.debug(
                f"Decision request details - Priority: {decision_request.priority}, "
                f"Options: {decision_request.options}, "
                f"Context: {decision_request.context}"
            )

            # Simulate human thinking time
            logger.debug(f"Agent {self.agent_id}: Simulating human decision process...")
            await asyncio.sleep(self.thinking_time)

            # Simulate decision making based on decision type
            decision, justification = await self._simulate_human_decision(
                decision_request
            )

            # Create decision response
            decision_response = DecisionResponse(
                request_id=decision_request.request_id,
                decision=decision,
                justification=justification,
                operator_id=self.simulated_operator_id,
                timestamp=datetime.utcnow(),
                confidence=0.9,  # High confidence for simulation
                additional_notes=(
                    f"Decision made by simulated operator {self.simulated_operator_id}"
                ),
                correlation_id=event.correlation_id,
            )

            # Create and publish the response event
            response_event = HumanDecisionResponseEvent(
                payload=decision_response, correlation_id=event.correlation_id
            )

            await self.event_bus.publish("HumanDecisionResponseEvent", response_event)

            logger.info(
                f"Agent {self.agent_id} published decision response for request "
                f"{decision_request.request_id}: '{decision}'. "
                f"Correlation ID: {event.correlation_id}"
            )

        except Exception as e:
            logger.error(
                f"Agent {self.agent_id}: Error handling decision request: {e}",
                exc_info=True,
            )

            # Optionally publish an error event or retry mechanism could be
            # implemented here

    async def _simulate_human_decision(
        self, request: DecisionRequest
    ) -> tuple[str, str]:
        """
        Simulate a human decision based on the request type and context.

        Args:
            request (DecisionRequest): The decision request to process.

        Returns:
            tuple[str, str]: A tuple containing (decision, justification).
        """
        # Default to first option if available
        if not request.options:
            return "no_action", "No options available for decision"

        # Simple decision logic based on decision type
        if request.decision_type == DecisionType.MAINTENANCE_APPROVAL:
            # For maintenance approval, check priority and context
            if request.priority in ["high", "critical"]:
                decision = "approve"
                justification = (
                    f"Approved due to {request.priority} priority "
                    f"maintenance requirement"
                )
            elif "emergency" in str(request.context).lower():
                decision = "approve"
                justification = "Approved due to emergency maintenance situation"
            else:
                decision = "approve"  # Default to approve for simulation
                justification = "Standard maintenance approval granted"

        elif request.decision_type == DecisionType.EMERGENCY_RESPONSE:
            decision = "approve"
            justification = "Emergency response approved for immediate action"

        elif request.decision_type == DecisionType.BUDGET_APPROVAL:
            # Simple budget check simulation
            budget_amount = request.context.get("amount", 0)
            if budget_amount < 10000:
                decision = "approve"
                justification = f"Budget of ${budget_amount} approved within limits"
            else:
                decision = "reject"
                justification = f"Budget of ${budget_amount} exceeds approval threshold"

        else:
            # Default decision for other types
            decision = request.options[0] if request.options else "approve"
            justification = f"Default decision for {request.decision_type}"

        logger.debug(
            f"Agent {self.agent_id}: Simulated decision '{decision}' "
            f"with justification: '{justification}'"
        )

        return decision, justification

    async def process(self, data: Any) -> Any:
        """
        Main processing logic for the Human Interface Agent.

        Args:
            data (Any): The data to be processed.

        Returns:
            Any: Processing result.
        """
        logger.debug(f"Agent {self.agent_id}: Processing data of type {type(data)}")

        # If data is a decision request, handle it directly
        if isinstance(data, DecisionRequest):
            # Create a mock event for processing
            mock_event = HumanDecisionRequiredEvent(payload=data)
            await self.handle_decision_request(mock_event)
            return {"status": "processed", "request_id": data.request_id}

        return {"status": "no_processing_required", "data_type": str(type(data))}
