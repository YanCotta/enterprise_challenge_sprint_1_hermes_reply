import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, call # Import call for checking arguments

from core.events.event_bus import EventBus

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
    event_type = "test_event_single"
    event_data = {"key": "value"}

    await event_bus.subscribe(event_type, mock_handler)
    assert event_type in event_bus.subscriptions
    assert mock_handler in event_bus.subscriptions[event_type]

    await event_bus.publish(event_type, event_data)

    mock_handler.assert_called_once_with(**event_data) # Use **event_data if data is dict
    logger.info("test_subscribe_and_publish_single_handler: PASSED")


@pytest.mark.asyncio
async def test_subscribe_and_publish_single_handler_non_dict_data():
    """Tests subscribing a single handler and publishing non-dict event data."""
    event_bus = EventBus()
    mock_handler = AsyncMock()
    event_type = "test_event_single_non_dict"
    event_data = "simple_string_data"

    await event_bus.subscribe(event_type, mock_handler)
    await event_bus.publish(event_type, event_data)

    mock_handler.assert_called_once_with(event_data)
    logger.info("test_subscribe_and_publish_single_handler_non_dict_data: PASSED")


@pytest.mark.asyncio
async def test_subscribe_and_publish_multiple_handlers():
    """Tests subscribing multiple handlers to the same event and publishing to them."""
    event_bus = EventBus()
    handler1 = AsyncMock(name="handler1")
    handler2 = AsyncMock(name="handler2")
    event_type = "test_event_multiple"
    event_data = {"message": "hello"}

    await event_bus.subscribe(event_type, handler1)
    await event_bus.subscribe(event_type, handler2)

    await event_bus.publish(event_type, event_data)

    handler1.assert_called_once_with(**event_data)
    handler2.assert_called_once_with(**event_data)
    logger.info("test_subscribe_and_publish_multiple_handlers: PASSED")


@pytest.mark.asyncio
async def test_publish_no_subscribers(caplog):
    """Tests publishing an event with no subscribers. Expects a debug log."""
    event_bus = EventBus()
    event_type = "unheard_event"
    event_data = {"info": "nothing_to_see_here"}

    # Capture logs at DEBUG level for this test
    caplog.set_level(logging.DEBUG, logger="core.events.event_bus")
    await event_bus.publish(event_type, event_data)
    # No assertion needed for handler calls, just that no error occurs
    # Check for the specific debug log message
    assert f"No subscribers for event '{event_type}'" in caplog.text
    logger.info("test_publish_no_subscribers: PASSED (verified via log)")


@pytest.mark.asyncio
async def test_unsubscribe_handler():
    """Tests unsubscribing a handler and ensuring it's not called afterwards."""
    event_bus = EventBus()
    mock_handler = AsyncMock()
    event_type = "test_event_unsubscribe"
    event_data = {"step": 1}

    await event_bus.subscribe(event_type, mock_handler)
    await event_bus.publish(event_type, event_data)
    mock_handler.assert_called_once_with(**event_data)

    mock_handler.reset_mock() # Reset call count for the next assertion

    await event_bus.unsubscribe(event_type, mock_handler)
    assert mock_handler not in event_bus.subscriptions.get(event_type, [])

    event_data_after_unsubscribe = {"step": 2}
    await event_bus.publish(event_type, event_data_after_unsubscribe)
    mock_handler.assert_not_called()
    logger.info("test_unsubscribe_handler: PASSED")


@pytest.mark.asyncio
async def test_unsubscribe_nonexistent_handler_or_event(caplog):
    """Tests that attempting to unsubscribe a non-existent handler or from a non-existent event type does not error."""
    event_bus = EventBus()
    mock_handler = AsyncMock(name="mock_handler_for_nonexistent")
    non_existent_event_type = "non_existent_event"
    actual_event_type = "actual_event"

    # Subscribe to an actual event to make sure the event type itself exists for one case
    await event_bus.subscribe(actual_event_type, AsyncMock(name="another_handler"))

    caplog.set_level(logging.WARNING) # EventBus logs warnings in these cases

    # Attempt to unsubscribe handler not subscribed to any event
    await event_bus.unsubscribe(actual_event_type, mock_handler)
    assert f"Handler '{mock_handler.name}' not found for event '{actual_event_type}' during unsubscribe." in caplog.text
    caplog.clear()

    # Attempt to unsubscribe handler from a non-existent event type
    await event_bus.unsubscribe(non_existent_event_type, mock_handler)
    assert f"No subscribers for event type '{non_existent_event_type}' during unsubscribe attempt." in caplog.text
    logger.info("test_unsubscribe_nonexistent_handler_or_event: PASSED (verified via log)")


@pytest.mark.asyncio
async def test_publish_handler_exception_graceful_handling(caplog):
    """
    Tests that EventBus handles exceptions in handlers gracefully and continues
    processing other handlers. Also checks for error logging.
    """
    event_bus = EventBus()
    handler1_raising_exception = AsyncMock(name="handler1_raiser", side_effect=Exception("Test Exception from Handler 1"))
    handler2_normal = AsyncMock(name="handler2_normal")
    event_type = "test_event_exception"
    event_data = {"critical_op": True}

    await event_bus.subscribe(event_type, handler1_raising_exception)
    await event_bus.subscribe(event_type, handler2_normal)

    caplog.set_level(logging.ERROR) # We expect an error log

    await event_bus.publish(event_type, event_data)

    handler1_raising_exception.assert_called_once_with(**event_data)
    handler2_normal.assert_called_once_with(**event_data) # Crucial: handler2 should still be called

    assert f"Error in event handler '{handler1_raising_exception.name}'" in caplog.text
    assert "Test Exception from Handler 1" in caplog.text
    assert "Traceback" in caplog.text # Check for traceback presence
    logger.info("test_publish_handler_exception_graceful_handling: PASSED (verified via log and handler calls)")


@pytest.mark.asyncio
async def test_unsubscribe_removes_event_type_if_empty(caplog):
    """
    Tests that an event type is removed from subscriptions if its last handler is unsubscribed.
    """
    event_bus = EventBus()
    mock_handler = AsyncMock()
    event_type = "event_a_to_empty"

    caplog.set_level(logging.DEBUG) # To see the debug log for event type removal

    await event_bus.subscribe(event_type, mock_handler)
    assert event_type in event_bus.subscriptions, "Event type should be in subscriptions after subscribe."

    await event_bus.unsubscribe(event_type, mock_handler)
    assert event_type not in event_bus.subscriptions, "Event type should be removed if no handlers are left."
    assert f"Event type '{event_type}' removed as no handlers are left." in caplog.text
    logger.info("test_unsubscribe_removes_event_type_if_empty: PASSED (verified via log and subscription state)")

@pytest.mark.asyncio
async def test_publish_with_dict_and_non_dict_data_to_same_event():
    """Tests publishing both dict and non-dict data to handlers for the same event type."""
    event_bus = EventBus()
    handler_for_dict = AsyncMock(name="handler_for_dict")
    handler_for_non_dict = AsyncMock(name="handler_for_non_dict")
    event_type = "mixed_data_event"

    # Subscribe both handlers to the same event type
    await event_bus.subscribe(event_type, handler_for_dict)
    await event_bus.subscribe(event_type, handler_for_non_dict)

    # Publish dict data
    dict_data = {"key": "value", "id": 123}
    await event_bus.publish(event_type, dict_data)
    handler_for_dict.assert_called_with(**dict_data) # Both called with dict
    handler_for_non_dict.assert_called_with(**dict_data)

    handler_for_dict.reset_mock()
    handler_for_non_dict.reset_mock()

    # Publish non-dict data
    non_dict_data = "This is a string payload"
    await event_bus.publish(event_type, non_dict_data)
    handler_for_dict.assert_called_with(non_dict_data) # Both called with non-dict
    handler_for_non_dict.assert_called_with(non_dict_data)

    logger.info("test_publish_with_dict_and_non_dict_data_to_same_event: PASSED")
