import asyncio
from collections import defaultdict
from typing import Callable, Any, DefaultDict, List, Coroutine
import logging
import traceback

# Set up a basic logger for the module
logger = logging.getLogger(__name__)
# Configure logging (e.g., to console with a specific format)
# This basic configuration can be done here for simplicity, or managed globally in the application


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

    async def publish(self, event: Any, data: Any = None):  # Changed event_type to event
        """
        Publishes an event to all subscribed asynchronous handlers.

        Handlers are called sequentially. If a handler raises an exception,
        the error is logged, and the EventBus continues to call other handlers.

        Args:
            event: The event object to publish. The type of this object (event.__class__)
                   is used to find subscribed handlers.
            data: The data to pass to the event handlers. If None, the event object itself
                  is passed. If data is provided, it's passed as keyword arguments
                  if it's a dictionary, otherwise as a positional argument.
                  Typically, the event object itself contains all necessary data.
        """
        event_type_key = event.__class__ # Use the class of the event object as the key
        handler_name = 'unknown_handler'
        
        # Determine what to pass to the handler
        payload_to_pass = data if data is not None else event

        # Truncate data for logging if it's too long
        log_payload = str(payload_to_pass)
        if len(log_payload) > 200:
            log_payload = log_payload[:200] + "..."

        logger.info(f"Publishing event of type '{event_type_key.__name__}' with payload (preview): {log_payload}")

        if event_type_key in self.subscriptions:
            # Create a copy of the list of handlers in case of modification during iteration
            handlers_to_call = list(self.subscriptions[event_type_key])
            for handler in handlers_to_call:
                handler_name = getattr(handler, '__name__', 'unknown_handler')
                try:
                    logger.debug(f"Calling handler '{handler_name}' for event type '{event_type_key.__name__}'.")
                    if isinstance(payload_to_pass, dict) and data is not None: # Only unpack if data was explicitly provided as a dict
                        await handler(**payload_to_pass)
                    else:
                        await handler(payload_to_pass) # Pass the event object or explicit non-dict data
                except Exception as e:
                    logger.error(
                        f"Error in event handler '{handler_name}' for event type '{event_type_key.__name__}' with payload (preview): {log_payload}.\\n"
                        f"Error: {e}\\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
        else:
            logger.debug(f"No subscribers for event type '{event_type_key.__name__}'.") # Corrected event_type to event_type_key.__name__
