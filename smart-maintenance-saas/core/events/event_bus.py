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
        Subscriptions are stored in a defaultdict of lists, keyed by event type name (string).
        """
        self.subscriptions: DefaultDict[str, List[Callable[..., Coroutine[Any, Any, Any]]]] = defaultdict(list)
        logger.info("EventBus initialized.")

    async def subscribe(self, event_type_name: str, handler: Callable[..., Coroutine[Any, Any, Any]]):
        """
        Subscribes an asynchronous handler to a specific event type name.

        Args:
            event_type_name: The string name of the event type to subscribe to (e.g., "SensorDataReceivedEvent").
            handler: The asynchronous function (coroutine) to call when the event is published.
        """
        self.subscriptions[event_type_name].append(handler)
        logger.info(f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' subscribed to event '{event_type_name}'.")

    async def unsubscribe(self, event_type_name: str, handler: Callable[..., Coroutine[Any, Any, Any]]):
        """
        Unsubscribes an asynchronous handler from a specific event type name.

        Args:
            event_type_name: The string name of the event type to unsubscribe from.
            handler: The handler to remove.
        """
        if event_type_name in self.subscriptions:
            try:
                self.subscriptions[event_type_name].remove(handler)
                logger.info(f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' unsubscribed from event '{event_type_name}'.")
                if not self.subscriptions[event_type_name]:
                    del self.subscriptions[event_type_name]
                    logger.debug(f"Event type name '{event_type_name}' removed as no handlers are left.")
            except ValueError:
                logger.warning(
                    f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' not found for event '{event_type_name}' during unsubscribe."
                )
        else:
            logger.warning(f"No subscribers for event type name '{event_type_name}' during unsubscribe attempt.")

    async def publish(self, event: Any): # Removed 'data' param, event object should contain all data
        """
        Publishes an event object to all subscribed asynchronous handlers.
        The event's class name is used to find appropriate handlers.

        Args:
            event: The event object to publish. This object is passed directly to the handlers.
        """
        event_type_name = event.__class__.__name__  # Use the class name string as the key
        handler_name = 'unknown_handler'
        
        log_payload = str(event) # Log the event object itself
        if len(log_payload) > 200:
            log_payload = log_payload[:200] + "..."

        logger.info(f"Publishing event of type '{event_type_name}' with payload (preview): {log_payload}")

        if event_type_name in self.subscriptions:
            handlers_to_call = list(self.subscriptions[event_type_name])
            for handler in handlers_to_call:
                handler_name = getattr(handler, '__name__', 'unknown_handler')
                try:
                    logger.debug(f"Calling handler '{handler_name}' for event type '{event_type_name}'.")
                    await handler(event) # Pass the event object directly
                except Exception as e:
                    logger.error(
                        f"Error in event handler '{handler_name}' for event type '{event_type_name}' with payload (preview): {log_payload}.\\\\n"
                        f"Error: {e}\\\\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
        else:
            logger.debug(f"No subscribers for event type name '{event_type_name}'.")
