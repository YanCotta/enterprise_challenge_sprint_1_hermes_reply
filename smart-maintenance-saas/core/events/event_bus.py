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
        logger.info(f"Handler '{getattr(handler, 'name', getattr(handler, '__name__', 'unknown_handler'))}' subscribed to event '{event_type}'.")

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
                logger.info(f"Handler '{getattr(handler, 'name', getattr(handler, '__name__', 'unknown_handler'))}' unsubscribed from event '{event_type}'.")
                if not self.subscriptions[event_type]:
                    # Optional: remove event type from dict if no handlers left
                    del self.subscriptions[event_type]
                    logger.debug(f"Event type '{event_type}' removed as no handlers are left.")
            except ValueError:
                logger.warning(
                    f"Handler '{getattr(handler, 'name', getattr(handler, '__name__', 'unknown_handler'))}' not found for event '{event_type}' during unsubscribe."
                )
        else:
            logger.warning(f"No subscribers for event type '{event_type}' during unsubscribe attempt.")

    async def publish(self, event_type_or_object: Any, data: Any = None):
        """
        Publishes an event to all subscribed asynchronous handlers.

        Handlers are called sequentially. If a handler raises an exception,
        the error is logged, and the EventBus continues to call other handlers.

        Args:
            event_type_or_object: The event object to publish or its type name (string).
                                  If an object, its class name is used as the event type key.
                                  If a string, it's used directly as the event type key.
            data: Optional data payload. If event_type_or_object is a string, this is the payload.
                  If event_type_or_object is an object, this parameter is typically ignored,
                  and the object itself is the payload.
        """
        handler_name = 'unknown_handler' # This line will be updated by the next change

        if isinstance(event_type_or_object, str):
            event_type_key_str = event_type_or_object
            # If data is None, it implies the event_type_or_object was intended to be the event object itself.
            # This case should ideally not happen if following new publish(event_object) or publish("event_name", data_dict)
            # For robustness, we might log a warning or handle as per specific design if data is also None here.
            # For now, assume 'data' holds the payload if event_type_or_object is a string.
            payload_to_pass = data
        elif hasattr(event_type_or_object, '__class__'):
            event_type_key_str = event_type_or_object.__class__.__name__
            payload_to_pass = event_type_or_object # The object itself is the payload
        else:
            # Fallback or error for unexpected type
            logger.error(f"Cannot determine event type from {event_type_or_object}")
            return

        # Truncate data for logging if it's too long
        log_payload = str(payload_to_pass)
        if len(log_payload) > 200:
            log_payload = log_payload[:200] + "..."

        logger.info(f"Publishing event: {event_type_key_str} with payload (preview): {log_payload}")

        if event_type_key_str in self.subscriptions:
            # Create a copy of the list of handlers in case of modification during iteration
            handlers_to_call = list(self.subscriptions[event_type_key_str])
            for handler in handlers_to_call:
                handler_name = getattr(handler, 'name', getattr(handler, '__name__', 'unknown_handler'))
                try:
                    logger.debug(f"Calling handler '{handler_name}' for event type '{event_type_key_str}'.")
                    if data is not None and isinstance(event_type_or_object, str):
                        # This case means publish("EventTypeString", actual_data_payload)
                        # If actual_data_payload is a dict, unpack it.
                        if isinstance(data, dict):
                            await handler(**data)
                        else:
                            await handler(data)
                    else:
                        # This case means publish(MyEventObject) or publish("EventTypeString", None)
                        # In both these scenarios, payload_to_pass holds the correct thing (the event object, or None)
                        if isinstance(payload_to_pass, dict): # If the event object itself is a dict (e.g. Pydantic model's dict())
                             await handler(**payload_to_pass)
                        else:
                             await handler(payload_to_pass)
                except Exception as e:
                    logger.error(
                        f"Error in event handler '{handler_name}' for event type '{event_type_key_str}' with payload (preview): {log_payload}.\\n"
                        f"Error: {e}\\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
        else:
            logger.debug(f"No subscribers for event type {event_type_key_str}")
