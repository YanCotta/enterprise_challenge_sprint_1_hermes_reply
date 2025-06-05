import asyncio
import logging
import traceback
from collections import defaultdict
from typing import Any, Callable, Coroutine, DefaultDict, List, Dict

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
        self.subscriptions: DefaultDict[
            str, List[Callable[..., Coroutine[Any, Any, Any]]]
        ] = defaultdict(list)
        self._running = False
        logger.info("EventBus initialized.")

    async def start(self):
        """Start the EventBus."""
        self._running = True
        logger.info("EventBus started.")

    async def stop(self):
        """Stop the EventBus."""
        self._running = False
        logger.info("EventBus stopped.")

    @property
    def _subscribers(self) -> Dict[str, List[Callable]]:
        """Expose subscribers for testing purposes."""
        return dict(self.subscriptions)

    async def subscribe(
        self, event_type_name: str, handler: Callable[..., Coroutine[Any, Any, Any]]
    ):
        """
        Subscribes an asynchronous handler to a specific event type name.

        Args:
            event_type_name: The string name of the event type to subscribe to (e.g., "SensorDataReceivedEvent").
            handler: The asynchronous function (coroutine) to call when the event is published.
        """
        self.subscriptions[event_type_name].append(handler)
        logger.info(
            f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' subscribed to event '{event_type_name}'."
        )

    async def unsubscribe(
        self, event_type_name: str, handler: Callable[..., Coroutine[Any, Any, Any]]
    ):
        """
        Unsubscribes an asynchronous handler from a specific event type name.

        Args:
            event_type_name: The string name of the event type to unsubscribe from.
            handler: The handler to remove.
        """
        if event_type_name in self.subscriptions:
            try:
                self.subscriptions[event_type_name].remove(handler)
                logger.info(
                    f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' unsubscribed from event '{event_type_name}'."
                )
                if not self.subscriptions[event_type_name]:
                    del self.subscriptions[event_type_name]
                    logger.debug(
                        f"Event type name '{event_type_name}' removed as no handlers are left."
                    )
            except ValueError:
                logger.warning(
                    f"Handler '{getattr(handler, '__name__', 'unknown_handler')}' not found for event '{event_type_name}' during unsubscribe."
                )
        else:
            logger.warning(
                f"No subscribers for event type name '{event_type_name}' during unsubscribe attempt."
            )

    async def publish(self, event_type_or_object: Any, data: Any = None):
        """
        Publishes an event to all subscribed asynchronous handlers.
        
        Supports two calling patterns:
        1. publish(event_object) - event object contains all data, class name used as event type
        2. publish(event_type_string, data_dict) - explicit event type and data
        
        Args:
            event_type_or_object: Either an event object or event type string
            data: Optional data dict when using explicit event type
        """
        if data is None:
            # Pattern 1: event object
            event = event_type_or_object
            event_type_name = event.__class__.__name__
            handler_name = "unknown_handler"

            log_payload = str(event)  # Log the event object itself
            if len(log_payload) > 200:
                log_payload = log_payload[:200] + "..."

            logger.info(
                f"Publishing event of type '{event_type_name}' with payload (preview): {log_payload}"
            )

            if event_type_name in self.subscriptions:
                handlers_to_call = list(self.subscriptions[event_type_name])
                for handler in handlers_to_call:
                    handler_name = getattr(handler, "__name__", "unknown_handler")
                    try:
                        logger.debug(
                            f"Calling handler '{handler_name}' for event type '{event_type_name}'."
                        )
                        await handler(event)  # Pass the event object directly
                    except Exception as e:
                        logger.error(
                            f"Error in event handler '{handler_name}' for event type '{event_type_name}' with payload (preview): {log_payload}.\n"
                            f"Error: {e}\n"
                            f"Traceback: {traceback.format_exc()}"
                        )
            else:
                logger.debug(f"No subscribers for event type {event_type_name}")
        else:
            # Pattern 2: explicit event type and data
            event_type_name = str(event_type_or_object)
            handler_name = "unknown_handler"

            log_payload = str(data)
            if len(log_payload) > 200:
                log_payload = log_payload[:200] + "..."

            logger.info(
                f"Publishing event of type '{event_type_name}' with data (preview): {log_payload}"
            )

            if event_type_name in self.subscriptions:
                handlers_to_call = list(self.subscriptions[event_type_name])
                for handler in handlers_to_call:
                    handler_name = getattr(handler, "__name__", "unknown_handler")
                    try:
                        logger.debug(
                            f"Calling handler '{handler_name}' for event type '{event_type_name}'."
                        )
                        await handler(event_type_name, data)  # Pass event type and data
                    except Exception as e:
                        logger.error(
                            f"Error in event handler '{handler_name}' for event type '{event_type_name}' with data (preview): {log_payload}.\n"
                            f"Error: {e}\n"
                            f"Traceback: {traceback.format_exc()}"
                        )
            else:
                logger.debug(f"No subscribers for event type {event_type_name}")
