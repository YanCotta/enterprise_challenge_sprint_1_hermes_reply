import pytest
import asyncio
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.base_agent_abc import BaseAgent
from data.exceptions import WorkflowError, SmartMaintenanceBaseException, AgentProcessingError
from core.events.event_bus import EventBus
# Using a dictionary for generic event for testing to match BaseAgent.handle_event signature
# from core.events.event_models import BaseEvent # BaseEvent might not be directly publishable if it's abstract or too basic

# 1. Define a Test Agent
class TestErrorAgent(BaseAgent):
    def __init__(self, agent_id: str, event_bus: EventBus, error_to_raise: Optional[Exception] = None):
        super().__init__(agent_id, event_bus)
        self.error_to_raise = error_to_raise
        self.processed_data: Any = None
        self.custom_event_handled = False

    async def process(self, data: Any) -> Any:
        self.processed_data = data
        if self.error_to_raise:
            # Simulate some processing before error for realism if needed
            await asyncio.sleep(0.01)
            raise self.error_to_raise
        return "processed_successfully"

    async def register_capabilities(self) -> None: # Must implement abstract method
        # No specific capabilities needed for this test's focus
        pass

    # Specific handler for custom event type if BaseAgent.handle_event is overridden by a subclass
    # For this test, we are testing the generic BaseAgent.handle_event.
    # async def handle_custom_test_event(self, event_name: str, data: Dict[str, Any]):
    #     self.custom_event_handled = True
    #     await self.process(data)


# 2. Pytest fixtures for event_bus
@pytest.fixture
async def event_bus_for_error_test() -> EventBus:
    bus = EventBus()
    # EventBus.start() is not strictly necessary for subscriptions/publishing in current impl
    # but good practice if it were to manage resources or background tasks.
    # await bus.start()
    yield bus
    await bus.shutdown() # Ensure cleanup


# 3. Implement Test Cases
@pytest.mark.asyncio
async def test_agent_publishes_agent_exception_event_on_custom_error(event_bus_for_error_test: EventBus):
    """
    Tests that AgentExceptionEvent is published when agent's process() raises a SmartMaintenanceBaseException.
    """
    agent_id = "test_error_agent_custom"
    error_to_raise = WorkflowError("Test custom workflow error", original_exception=ValueError("Original cause"))
    test_agent = TestErrorAgent(agent_id, event_bus_for_error_test, error_to_raise=error_to_raise)
    await test_agent.start()

    captured_error_events: List[Dict[str, Any]] = []
    async def capture_agent_exception_event(event_name: str, event_data: Dict[str, Any]):
        # The EventBus publish method for (event_type, data) passes them as separate args
        if event_name == "AgentExceptionEvent":
            captured_error_events.append(event_data)

    await event_bus_for_error_test.subscribe("AgentExceptionEvent", capture_agent_exception_event)

    test_event_type = "TestSourceEventCustomError"
    test_event_data = {"key": "value", "id": str(uuid4())}

    # Agent needs to be subscribed to the event it's supposed to handle
    await event_bus_for_error_test.subscribe(test_event_type, test_agent.handle_event)

    # Publish the test event that will trigger the error in TestErrorAgent.process
    await event_bus_for_error_test.publish(test_event_type, test_event_data)
    await asyncio.sleep(0.1) # Allow time for event processing and publishing of error event

    assert len(captured_error_events) == 1, "AgentExceptionEvent was not published"
    error_payload = captured_error_events[0]

    assert error_payload["agent_id"] == agent_id
    assert error_payload["failed_event_type"] == test_event_type
    assert error_payload["error_class"] == error_to_raise.__class__.__name__ # "WorkflowError"
    assert error_payload["error_message"] == str(error_to_raise)
    assert error_payload["original_exception_class"] == ValueError.__name__
    assert error_payload["original_exception_message"] == "Original cause"

    await test_agent.stop()


@pytest.mark.asyncio
async def test_agent_publishes_agent_exception_event_on_generic_error(event_bus_for_error_test: EventBus):
    """
    Tests that AgentExceptionEvent is published when agent's process() raises a generic Python Exception.
    """
    agent_id = "test_error_agent_generic"
    error_to_raise = ValueError("Test generic value error in process") # Using ValueError as a sample generic Python error
    test_agent = TestErrorAgent(agent_id, event_bus_for_error_test, error_to_raise=error_to_raise)
    await test_agent.start()

    captured_error_events: List[Dict[str, Any]] = []
    async def capture_agent_exception_event(event_name: str, event_data: Dict[str, Any]):
        if event_name == "AgentExceptionEvent":
            captured_error_events.append(event_data)

    await event_bus_for_error_test.subscribe("AgentExceptionEvent", capture_agent_exception_event)

    test_event_type = "TestSourceEventGenericError"
    test_event_data = {"data_point": 123, "id": str(uuid4())}

    await event_bus_for_error_test.subscribe(test_event_type, test_agent.handle_event)

    await event_bus_for_error_test.publish(test_event_type, test_event_data)
    await asyncio.sleep(0.1)

    assert len(captured_error_events) == 1, "AgentExceptionEvent was not published for generic error"
    error_payload = captured_error_events[0]

    assert error_payload["agent_id"] == agent_id
    assert error_payload["failed_event_type"] == test_event_type
    assert error_payload["error_class"] == error_to_raise.__class__.__name__ # "ValueError"
    assert error_payload["error_message"] == str(error_to_raise)
    # For generic exceptions, original_exception fields in AgentExceptionEvent payload will be None
    assert error_payload.get("original_exception_class") is None
    assert error_payload.get("original_exception_message") is None

    await test_agent.stop()

@pytest.mark.asyncio
async def test_agent_no_error_event_if_process_succeeds(event_bus_for_error_test: EventBus):
    """
    Tests that NO AgentExceptionEvent is published if agent's process() completes successfully.
    """
    agent_id = "test_success_agent"
    # No error configured for the agent
    test_agent = TestErrorAgent(agent_id, event_bus_for_error_test, error_to_raise=None)
    await test_agent.start()

    captured_error_events: List[Dict[str, Any]] = []
    async def capture_agent_exception_event(event_name: str, event_data: Dict[str, Any]):
        if event_name == "AgentExceptionEvent":
            captured_error_events.append(event_data)

    await event_bus_for_error_test.subscribe("AgentExceptionEvent", capture_agent_exception_event)

    test_event_type = "TestSourceEventSuccess"
    test_event_data = {"info": "all_good", "id": str(uuid4())}

    await event_bus_for_error_test.subscribe(test_event_type, test_agent.handle_event)

    await event_bus_for_error_test.publish(test_event_type, test_event_data)
    await asyncio.sleep(0.1)

    assert len(captured_error_events) == 0, "AgentExceptionEvent should not be published on success"
    assert test_agent.processed_data == test_event_data # Verify process was actually called

    await test_agent.stop()
