import asyncio
from collections import defaultdict
from typing import Callable, Any, DefaultDict, List, Coroutine
import logging
import traceback

# Set up a basic logger for the module
logger = logging.getLogger(__name__)
# Configure logging (e.g., to console with a specific format)
# This basic configuration can be done here for simplicity, or managed globally in the application
if not logger.handlers: # Avoid adding multiple handlers if this module is reloaded
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO) # Default level, can be configured as needed


class EventBus:
    """
    An event bus for decoupled asynchronous communication between components.

    Handles subscription, unsubscription, and publication of events.
    Errors in event handlers are logged without interrupting other handlers.
    """

    def __init__(self):
        """
        Initializes the EventBus.
        Subscriptions are stored in a defaultdict of lists.
        """
        self.subscriptions: DefaultDict[str, List[Callable[..., Coroutine[Any, Any, Any]]]] = defaultdict(list)
        logger.info("EventBus initialized.")

    async def subscribe(self, event_type: str, handler: Callable[..., Coroutine[Any, Any, Any]]):
        """
        Subscribes an asynchronous handler to a specific event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: The asynchronous function (coroutine) to call when the event is published.
        """
        self.subscriptions[event_type].append(handler)
        logger.info(f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' subscribed to event '{event_type}'.")

    async def unsubscribe(self, event_type: str, handler: Callable[..., Coroutine[Any, Any, Any]]):
        """
        Unsubscribes an asynchronous handler from a specific event type.

        Args:
            event_type: The type of event to unsubscribe from.
            handler: The handler to remove.
        """
        if event_type in self.subscriptions:
            try:
                self.subscriptions[event_type].remove(handler)
                logger.info(f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' unsubscribed from event '{event_type}'.")
                if not self.subscriptions[event_type]:
                    # Optional: remove event type from dict if no handlers left
                    del self.subscriptions[event_type]
                    logger.debug(f"Event type '{event_type}' removed as no handlers are left.")
            except ValueError:
                logger.warning(
                    f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' not found for event '{event_type}' during unsubscribe."
                )
        else:
            logger.warning(f"No subscribers for event type '{event_type}' during unsubscribe attempt.")

    async def publish(self, event_type: str, data: Any = None):
        """
        Publishes an event to all subscribed asynchronous handlers.

        Handlers are called sequentially. If a handler raises an exception,
        the error is logged, and the EventBus continues to call other handlers.

        Args:
            event_type: The type of event to publish.
            data: The data to pass to the event handlers. The data is passed as keyword arguments
                  if it's a dictionary, otherwise as a positional argument.
        """
        handler_name = 'unknown_handler'
        # Truncate data for logging if it's too long
        log_data = str(data)
        if len(log_data) > 200:
            log_data = log_data[:200] + "..."

        logger.info(f"Publishing event '{event_type}' with data (preview): {log_data}")

        if event_type in self.subscriptions:
            # Create a copy of the list of handlers in case of modification during iteration (e.g., unsubscribe within a handler)
            handlers_to_call = list(self.subscriptions[event_type])
            for handler in handlers_to_call:
                handler_name = getattr(handler, '__name__', 'unknown_handler')
                try:
                    logger.debug(f"Calling handler '{handler_name}' for event '{event_type}'.")
                    if isinstance(data, dict):
                        await handler(**data)
                    else:
                        await handler(data)
                except Exception as e:
                    logger.error(
                        f"Error in event handler '{handler_name}' for event '{event_type}' with data (preview): {log_data}.\n"
                        f"Error: {e}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
        else:
            logger.debug(f"No subscribers for event '{event_type}'.")
