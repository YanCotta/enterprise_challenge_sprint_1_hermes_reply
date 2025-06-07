import pytest
import asyncio
import logging # Import logging for patching
from unittest.mock import patch, MagicMock # AsyncMock not needed if logger.error is not async
from uuid import uuid4

from core.events.event_bus import EventBus
from core.events.event_models import BaseEvent
from core.config import settings as global_settings

# 1. Define a Test Event
class TestDLQEvent(BaseEvent): # Simple event for testing
    def __init__(self, data: str, event_id: str = None, correlation_id: str = None, timestamp: str = None):
        super().__init__(event_id=event_id or str(uuid4()),
                         correlation_id=correlation_id,
                         timestamp=timestamp)
        self.data = data

    # The __str__ representation is sometimes used in logging, make it informative.
    def __str__(self):
        return f"TestDLQEvent(id='{self.event_id}', data='{self.data}')"

# 2. Failing event handler
async def consistently_failing_handler_for_dlq(event: TestDLQEvent):
    """A handler that always fails, to test DLQ functionality."""
    raise ValueError(f"Simulated handler failure for DLQ test with event data: {event.data}")

# 3. Implement the Test Case
@pytest.mark.asyncio
async def test_event_logged_to_dlq_after_retries(monkeypatch):
    """
    Tests that an event is logged to the DLQ after all retry attempts fail.
    """
    # Temporarily modify global settings for this test
    monkeypatch.setattr(global_settings, 'EVENT_HANDLER_MAX_RETRIES', 1)
    monkeypatch.setattr(global_settings, 'EVENT_HANDLER_RETRY_DELAY_SECONDS', 0.01) # Short delay for quick test
    monkeypatch.setattr(global_settings, 'DLQ_ENABLED', True)
    # Optional: monkeypatch DLQ_LOG_FILE if you want to ensure it's not writing to a real file,
    # but since we mock the logger, it won't write anyway.
    # monkeypatch.setattr(global_settings, 'DLQ_LOG_FILE', "logs/test_dlq_events.log")

    # IMPORTANT: Create EventBus instance *after* monkeypatching settings,
    # so it initializes its DLQ logger (if any part of it is conditional on settings)
    # with the patched settings.
    # The dlq_logger in event_bus.py is module-level, but its handlers might be added
    # based on DLQ_ENABLED when the module is first imported or when an EventBus is created.
    # To be safe, we'll patch where it's used or where it's created.
    # The current event_bus.py initializes dlq_logger at module level based on settings.
    # If settings change, that logger instance might not reflect it unless re-imported or re-configured.
    # For this test, we will patch 'logging.getLogger' to control the logger instance handed to the event_bus module.

    mock_dlq_specific_logger = MagicMock(spec=logging.Logger)

    # Patch 'logging.getLogger' specifically for the "dlq" logger name.
    # When event_bus.py calls logging.getLogger("dlq"), it will get our mock.
    with patch('logging.getLogger', lambda name: mock_dlq_specific_logger if name == "dlq" else logging.getLogger(name)):
        # We also need to ensure that the dlq_logger setup within event_bus.py
        # (like adding handlers) doesn't fail or get bypassed due to the mock not having expected methods.
        # If dlq_logger.addHandler is called, our mock_dlq_specific_logger needs to handle it.
        # A simpler approach is to mock the .error method directly on the *actual* dlq logger if possible.
        # Let's try patching the `error` method of the logger instance that `event_bus.py` will use.

        # To ensure the event_bus module uses the patched settings for its dlq_logger setup,
        # we might need to reload it or ensure the bus is created after patches.
        # For simplicity, assume EventBus() will correctly use the patched settings for DLQ enablement for now.
        # The dlq_logger is set up at the module level in event_bus.py.
        # A robust way is to patch the `dlq_logger.error` directly in the `core.events.event_bus` module.

        # Re-creating bus to ensure it's using the patched settings for DLQ logic
        bus = EventBus()
        # No need to await bus.start() as it does nothing in current EventBus

        # Patch the 'error' method of the module-level 'dlq_logger' in 'core.events.event_bus'
        with patch('core.events.event_bus.dlq_logger.error', new_callable=MagicMock) as mock_actual_dlq_error_method:

            await bus.subscribe(TestDLQEvent.__name__, consistently_failing_handler_for_dlq)

            test_event = TestDLQEvent(data="event_data_for_dlq_test")

            # Publish the event that will cause the handler to fail
            await bus.publish(test_event) # Pass the event object directly

            # Wait for retries (1 retry) and DLQ processing
            # Total time: initial attempt + 0.01s delay + 2nd attempt.
            # Add a buffer for processing.
            await asyncio.sleep(0.1)

            # Assertions
            mock_actual_dlq_error_method.assert_called_once()

            # Check the arguments of the call to dlq_logger.error
            # The first positional argument is the message string.
            # The 'extra' kwarg contains the structured log data.
            args, kwargs = mock_actual_dlq_error_method.call_args

            assert args[0] == "Failed event sent to DLQ" # The main log message

            extra_info = kwargs.get('extra')
            assert extra_info is not None, "Structured 'extra' data was not logged to DLQ"

            assert extra_info.get('event_type') == TestDLQEvent.__name__
            # Handler name might include module path, so check for substring
            assert "consistently_failing_handler_for_dlq" in extra_info.get('handler_name', "")
            assert "Simulated handler failure" in extra_info.get('error', "")
            # Event data in DLQ log is JSON stringified
            assert '"data": "event_data_for_dlq_test"' in extra_info.get('event_data', "")
            assert f'"event_id": "{test_event.event_id}"' in extra_info.get('event_data', "")

        await bus.stop() # Clean up the locally created bus
