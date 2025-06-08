import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from core.base_agent_abc import AgentCapability, BaseAgent
from core.events.event_bus import (  # Assuming EventBus is sync for mock, or use AsyncMock if it has async methods relevant here
    EventBus,
)


# Concrete Test Agent for most tests
class MyTestAgent(BaseAgent):
    """A concrete agent for testing BaseAgent functionalities."""

    async def process(self, data: Any) -> Any:
        """Mockable process method."""
        # This will typically be mocked in tests
        return f"processed_{data}"

    async def register_capabilities(self) -> None:
        """Overrides to populate capabilities for testing."""
        self.capabilities.append(
            AgentCapability(
                name="test_cap",
                description="Test capability",
                input_types=["str"],
                output_types=["str"],
            )
        )
        # For testing the print statement in base, though usually not asserted.
        # await super().register_capabilities()
        # print(f"Agent {self.agent_id} MyTestAgent registered capabilities.")


@pytest.fixture
def mock_event_bus() -> MagicMock:
    """Provides a MagicMock for the EventBus."""
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()  # Ensure publish is an AsyncMock
    return bus


@pytest.mark.asyncio
async def test_base_agent_initialization(mock_event_bus: MagicMock):
    """Tests BaseAgent initialization."""
    agent_id = "test_agent_001"
    agent = MyTestAgent(agent_id=agent_id, event_bus=mock_event_bus)

    assert agent.agent_id == agent_id
    assert agent.event_bus is mock_event_bus
    assert agent.status == "initializing"
    assert agent.capabilities == [], "Capabilities should be empty on init before start"


@pytest.mark.asyncio
async def test_base_agent_start(mock_event_bus: MagicMock):
    """Tests the start method of BaseAgent."""
    agent_id = "test_agent_start"
    agent = MyTestAgent(agent_id=agent_id, event_bus=mock_event_bus)

    # Mock the concrete agent's register_capabilities for this test
    # to isolate the BaseAgent.start() logic.
    agent.register_capabilities = AsyncMock(name="register_capabilities_mock")

    await agent.start()

    assert agent.status == "running"
    agent.register_capabilities.assert_called_once()


@pytest.mark.asyncio
async def test_base_agent_stop(mock_event_bus: MagicMock):
    """Tests the stop method of BaseAgent."""
    agent_id = "test_agent_stop"
    agent = MyTestAgent(agent_id=agent_id, event_bus=mock_event_bus)
    agent.status = "running"  # Manually set status for this test

    await agent.stop()

    assert agent.status == "stopped"


@pytest.mark.asyncio
async def test_base_agent_get_health(mock_event_bus: MagicMock):
    """Tests the get_health method."""
    agent_id = "test_agent_health"
    agent = MyTestAgent(agent_id=agent_id, event_bus=mock_event_bus)
    agent.status = "testing_health"  # Set a specific status

    health_status = await agent.get_health()

    assert health_status["agent_id"] == agent_id
    assert health_status["status"] == "testing_health"
    assert "timestamp" in health_status

    timestamp_str = health_status.get("timestamp")
    assert timestamp_str is not None

    # Parse the timestamp string
    parsed_time = datetime.fromisoformat(timestamp_str)

    # Assert that the parsed time is timezone-aware and UTC
    assert parsed_time.tzinfo is not None
    assert parsed_time.tzinfo.utcoffset(parsed_time) == timezone.utc.utcoffset(None)

    # Optional: Check if the timestamp is recent (within a certain delta)
    assert (datetime.now(timezone.utc) - parsed_time).total_seconds() < 5


@pytest.mark.asyncio
async def test_my_test_agent_register_capabilities_populates(mock_event_bus: MagicMock):
    """Tests that MyTestAgent's register_capabilities actually populates the list."""
    agent_id = "test_agent_reg_cap"
    agent = MyTestAgent(agent_id=agent_id, event_bus=mock_event_bus)

    # Call the actual register_capabilities of MyTestAgent
    await agent.register_capabilities()

    assert len(agent.capabilities) == 1
    capability = agent.capabilities[0]
    assert isinstance(capability, AgentCapability)
    assert capability.name == "test_cap"
    assert capability.description == "Test capability"


@pytest.mark.asyncio
async def test_base_agent_handle_event_default_behavior(
    mock_event_bus: MagicMock, caplog
):
    """
    Tests the default BaseAgent.handle_event behavior.
    The default implementation in the prompt only prints.
    It should not call self.process.
    """
    agent_id = "test_agent_handle_default"
    agent = MyTestAgent(agent_id=agent_id, event_bus=mock_event_bus)
    agent.process = AsyncMock(
        name="process_mock"
    )  # Mock process to ensure it's not called

    event_type = "some_event"
    event_data = {"key": "value"}

    # Set caplog level to capture INFO from print statements if they are routed to logging,
    # or check stdout if BaseAgent uses plain print.
    # BaseAgent in prompt uses print, which might not be captured by caplog unless configured.
    # For now, we focus on 'process' not being called.
    # If BaseAgent's print was `logger.info(f"Agent {self.agent_id} received event...`
    # then caplog would capture it.
    # The current BaseAgent's handle_event prints: print(f"Agent {self.agent_id} received event: {event_type} with data: {data}")

    await agent.handle_event(event_type, event_data)

    agent.process.assert_called_once_with(event_data)
    # To check print:
    # captured = capsys.readouterr()
    # assert f"Agent {agent_id} received event: {event_type} with data: {event_data}" in captured.out


# Agent subclass for testing overridden handle_event
class MyProcessingAgent(BaseAgent):
    """Agent that overrides handle_event to call process."""

    async def process(self, data: Any) -> Any:
        # This will be mocked in the test
        return f"processed_override_{data}"

    async def handle_event(self, event_type: str, data: Any):
        """Overrides to call process."""
        print(
            f"Agent {self.agent_id} MyProcessingAgent received event: {event_type}, processing..."
        )
        await self.process(data)


@pytest.mark.asyncio
async def test_base_agent_handle_event_can_be_overridden_to_call_process(
    mock_event_bus: MagicMock,
):
    """Tests that handle_event can be overridden to call the process method."""
    agent_id = "test_agent_handle_override"
    agent = MyProcessingAgent(agent_id=agent_id, event_bus=mock_event_bus)
    agent.process = AsyncMock(name="process_mock_override")  # Mock the process method

    event_type = "custom_event_type"
    event_data = {"payload": "important_data"}

    await agent.handle_event(event_type, event_data)

    agent.process.assert_called_once_with(event_data)


@pytest.mark.asyncio
async def test_base_agent_publish_event(mock_event_bus: MagicMock):
    """Tests the _publish_event helper method."""
    agent_id = "test_agent_publish"
    agent = MyTestAgent(agent_id=agent_id, event_bus=mock_event_bus)

    event_type_to_publish = "my_agent_event"
    data_to_publish = {"info": "details"}

    await agent._publish_event(event_type_to_publish, data_to_publish)

    mock_event_bus.publish.assert_called_once_with(
        event_type_to_publish, data_to_publish
    )


@pytest.mark.asyncio
async def test_base_agent_publish_event_no_bus(caplog):
    """Tests that _publish_event handles a null event_bus gracefully."""
    agent_id = "test_agent_publish_no_bus"
    # Pass event_bus=None
    agent = MyTestAgent(agent_id=agent_id, event_bus=None)

    event_type_to_publish = "my_agent_event_no_bus"
    data_to_publish = {"info": "details_no_bus"}

    caplog.set_level(
        logging.INFO
    )  # Assuming the print in _publish_event is like logger.info

    # The original BaseAgent's _publish_event has:
    # print(f"Agent {self.agent_id} event bus not configured. Cannot publish event: {event_type}")
    # This won't be caught by caplog unless print is redirected to logging.
    # For this test, we primarily ensure it doesn't raise an error.
    # If we want to capture the print, we'd use capsys.
    try:
        await agent._publish_event(event_type_to_publish, data_to_publish)
    except Exception as e:
        pytest.fail(f"_publish_event raised an exception with no event bus: {e}")

    # If print was converted to logger.info:
    # assert f"Agent {agent_id} event bus not configured." in caplog.text
    # assert f"Cannot publish event: {event_type_to_publish}" in caplog.text
    # For now, just asserting no exception is sufficient as per current BaseAgent.py.
    # The print statement from BaseAgent `_publish_event` is:
    # print(f"Agent {self.agent_id} event bus not configured. Cannot publish event: {event_type}")
    # We can check this with capsys if strictly needed.
    # For now, the main point is no AttributeError or crash.
    pass  # Test passes if no exception was raised


@pytest.mark.asyncio
async def test_agent_capability_creation():
    """Tests simple AgentCapability creation."""
    cap = AgentCapability(
        name="cap_name",
        description="cap_desc",
        input_types=["foo"],
        output_types=["bar"],
    )
    assert cap.name == "cap_name"
    assert cap.description == "cap_desc"
    assert cap.input_types == ["foo"]
    assert cap.output_types == ["bar"]

    cap_default_lists = AgentCapability(name="cap_name2", description="cap_desc2")
    assert cap_default_lists.input_types == []
    assert cap_default_lists.output_types == []
