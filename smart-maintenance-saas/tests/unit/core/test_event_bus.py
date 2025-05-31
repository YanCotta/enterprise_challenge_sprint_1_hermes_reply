import logging
from unittest.mock import AsyncMock, call

import pytest

from core.events.event_bus import EventBus
from core.events.event_models import BaseEventModel

# Configure logging for testing purposes to see EventBus logs if needed
# This can be helpful for debugging tests, though tests themselves will use caplog
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_event_bus_initialization():
    """Tests that EventBus initializes with an empty subscriptions dictionary."""
    event_bus = EventBus()
    assert not event_bus.subscriptions, "EventBus subscriptions should be empty on initialization."
    logger.info("test_event_bus_initialization: PASSED")


@pytest.mark.asyncio
async def test_subscribe_and_publish_single_handler():
    """Tests subscribing a single handler and publishing an event to it."""
    event_bus = EventBus()
    mock_handler = AsyncMock()
    mock_event = BaseEventModel(correlation_id="test-correlation-id")

    await event_bus.subscribe(BaseEventModel.__name__, mock_handler)
    assert BaseEventModel.__name__ in event_bus.subscriptions
    assert mock_handler in event_bus.subscriptions[BaseEventModel.__name__]

    await event_bus.publish(mock_event)

    mock_handler.assert_called_once_with(mock_event)
    logger.info("test_subscribe_and_publish_single_handler: PASSED")


@pytest.mark.asyncio
async def test_subscribe_and_publish_multiple_handlers():
    """Tests subscribing multiple handlers to the same event and publishing to them."""
    event_bus = EventBus()
    handler1 = AsyncMock(name="handler1")
    handler2 = AsyncMock(name="handler2")
    mock_event = BaseEventModel(correlation_id="test-multi-handlers")

    await event_bus.subscribe(BaseEventModel.__name__, handler1)
    await event_bus.subscribe(BaseEventModel.__name__, handler2)

    await event_bus.publish(mock_event)

    handler1.assert_called_once_with(mock_event)
    handler2.assert_called_once_with(mock_event)
    logger.info("test_subscribe_and_publish_multiple_handlers: PASSED")


@pytest.mark.asyncio
async def test_publish_no_subscribers(caplog):
    """Tests publishing an event with no subscribers. Expects a debug log."""
    event_bus = EventBus()
    mock_event = BaseEventModel(correlation_id="test-no-subscribers")

    # Capture logs at DEBUG level for this test
    caplog.set_level(logging.DEBUG, logger="core.events.event_bus")
    await event_bus.publish(mock_event)
    # Check for the specific debug log message
    assert f"No subscribers for event type {BaseEventModel.__name__}" in caplog.text
    logger.info("test_publish_no_subscribers: PASSED (verified via log)")


@pytest.mark.asyncio
async def test_unsubscribe_handler():
    """Tests unsubscribing a handler and ensuring it's not called afterwards."""
    event_bus = EventBus()
    mock_handler = AsyncMock()
    mock_event = BaseEventModel(correlation_id="test-unsubscribe")

    await event_bus.subscribe(BaseEventModel.__name__, mock_handler)
    await event_bus.publish(mock_event)
    mock_handler.assert_called_once_with(mock_event)

    mock_handler.reset_mock()  # Reset call count for the next assertion

    await event_bus.unsubscribe(BaseEventModel.__name__, mock_handler)
    assert mock_handler not in event_bus.subscriptions.get(BaseEventModel.__name__, [])

    mock_event_after = BaseEventModel(correlation_id="test-unsubscribe-after")
    await event_bus.publish(mock_event_after)
    mock_handler.assert_not_called()
    logger.info("test_unsubscribe_handler: PASSED")


@pytest.mark.asyncio
async def test_unsubscribe_nonexistent_handler_or_event(caplog):
    """Tests that attempting to unsubscribe a non-existent handler or from a non-existent event type does not error."""
    event_bus = EventBus()
    mock_handler = AsyncMock(name="mock_handler_for_nonexistent")
    non_existent_event_type = "non_existent_event"

    # Subscribe a different handler to BaseEventModel to make sure the event type exists for one case
    await event_bus.subscribe(BaseEventModel.__name__, AsyncMock(name="another_handler"))

    caplog.set_level(logging.WARNING)  # EventBus logs warnings in these cases

    # Attempt to unsubscribe handler not subscribed to any event
    await event_bus.unsubscribe(BaseEventModel.__name__, mock_handler)
    assert f"Handler '{mock_handler.name}' not found for event '{BaseEventModel.__name__}' during unsubscribe." in caplog.text
    caplog.clear()

    # Attempt to unsubscribe handler from a non-existent event type
    await event_bus.unsubscribe(non_existent_event_type, mock_handler)
    assert f"No subscribers for event type '{non_existent_event_type}' during unsubscribe attempt." in caplog.text
    logger.info("test_unsubscribe_nonexistent_handler_or_event: PASSED (verified via log)")


@pytest.mark.asyncio
async def test_publish_handler_exception_graceful_handling(caplog):
    """Tests that EventBus handles exceptions in handlers gracefully and continues processing other handlers."""
    event_bus = EventBus()
    error_msg = "Simulated handler error"

    async def failing_handler(event):
        raise ValueError(error_msg)

    working_handler = AsyncMock()
    mock_event = BaseEventModel(correlation_id="test-exception-handling")

    await event_bus.subscribe(BaseEventModel.__name__, failing_handler)
    await event_bus.subscribe(BaseEventModel.__name__, working_handler)

    caplog.set_level(logging.ERROR)
    await event_bus.publish(mock_event)

    # Verify the error was logged
    assert error_msg in caplog.text
    # Verify the working handler was still called
    working_handler.assert_called_once_with(mock_event)
    logger.info("test_publish_handler_exception_graceful_handling: PASSED")


@pytest.mark.asyncio
async def test_unsubscribe_removes_event_type_if_empty(caplog):
    """Tests that event type is removed from subscriptions when last handler is unsubscribed."""
    event_bus = EventBus()
    mock_handler = AsyncMock()
    
    await event_bus.subscribe(BaseEventModel.__name__, mock_handler)
    assert BaseEventModel.__name__ in event_bus.subscriptions
    
    await event_bus.unsubscribe(BaseEventModel.__name__, mock_handler)
    assert BaseEventModel.__name__ not in event_bus.subscriptions
    
    caplog.set_level(logging.DEBUG)
    assert f"Event type name '{BaseEventModel.__name__}' removed as no handlers are left" in caplog.text
    logger.info("test_unsubscribe_removes_event_type_if_empty: PASSED")
