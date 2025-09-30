import asyncio
import inspect
import logging
import traceback
from collections import defaultdict
from typing import Any, Callable, Coroutine, DefaultDict, List, Dict
import time # Added for retry delay, though asyncio.sleep is used
import json # Added for DLQ serialization
import os # Added for DLQ log directory

from tenacity import retry, stop_after_attempt, wait_exponential

from core.config.settings import settings
# from data.exceptions import EventHandlerError, SmartMaintenanceBaseException # Not strictly needed if not raising new exceptions yet

# Helper payload wrapper to support both attribute and dict-style access
class _EventPayload:
    def __init__(self, data: Dict[str, Any]):
        self._data = dict(data)

    def __getattr__(self, item: str) -> Any:
        try:
            return self._data[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __getitem__(self, item: str) -> Any:
        return self._data[item]

    def __contains__(self, item: str) -> bool:
        return item in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def items(self):
        return self._data.items()

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


# Set up a basic logger for the module
logger = logging.getLogger(__name__)

# DLQ Logger Setup
dlq_logger = None
if settings.DLQ_ENABLED:
    try:
        # Ensure log directory exists
        dlq_log_dir = os.path.dirname(settings.DLQ_LOG_FILE)
        if dlq_log_dir and not os.path.exists(dlq_log_dir):
            os.makedirs(dlq_log_dir, exist_ok=True)

        dlq_logger = logging.getLogger("dlq")
        # Check if handlers are already added to avoid duplication during reloads/tests
        if not dlq_logger.handlers:
            dlq_handler = logging.FileHandler(settings.DLQ_LOG_FILE)
            # Using a custom formatter that expects specific keys in the LogRecord's extra dict
            dlq_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - EventType: %(event_type)s - Handler: %(handler_name)s - Error: %(error)s - Trace: %(traceback)s - EventData: %(event_data)s"
            )
            dlq_handler.setFormatter(dlq_formatter)
            dlq_logger.addHandler(dlq_handler)
            dlq_logger.setLevel(settings.log_level.upper() if hasattr(settings, 'log_level') else logging.INFO)
            dlq_logger.propagate = False # Avoid duplicate logging
    except Exception as e:
        logger.error(f"Failed to initialize DLQ logger: {e}", exc_info=True)
        dlq_logger = None # Disable DLQ if setup fails


class EventBus:
    """
    An event bus for decoupled asynchronous communication between components.

    Handles subscription, unsubscription, and publication of events.
    Errors in event handlers are logged, retried, and potentially sent to a DLQ.
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

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=6),
        stop=stop_after_attempt(3)
    )
    async def publish(self, event_type_or_object: Any, data_payload_arg: Any = None):
        """
        Publishes an event to all subscribed asynchronous handlers.
        
        Supports two calling patterns:
        1. publish(event_object) - event object contains all data, class name used as event type
        2. publish(event_type_string, data_dict) - explicit event type and data
        
        Args:
            event_type_or_object: Either an event object or event type string
            data_payload_arg: Optional data dict when using explicit event type
        """
        event_obj = None
        data_dict_payload = None
        event_type_name: str

        if data_payload_arg is None:
            # Pattern 1: event object
            event_obj = event_type_or_object
            event_type_name = event_obj.__class__.__name__
        else:
            # Pattern 2: explicit event type and data
            event_type_name = str(event_type_or_object)
            data_dict_payload = data_payload_arg

        log_preview_payload = str(event_obj if event_obj else data_dict_payload)
        if len(log_preview_payload) > 200:
            log_preview_payload = log_preview_payload[:200] + "..."

        logger.info(
            f"Publishing event of type '{event_type_name}' with payload/data (preview): {log_preview_payload}"
        )

        if event_type_name in self.subscriptions:
            handlers_to_call = list(self.subscriptions[event_type_name])
            for handler in handlers_to_call:
                handler_name = getattr(handler, "__name__", "unknown_handler")

                for attempt in range(settings.EVENT_HANDLER_MAX_RETRIES + 1):
                    try:
                        logger.debug(
                            f"Calling handler '{handler_name}' for event type '{event_type_name}', attempt {attempt + 1}/{settings.EVENT_HANDLER_MAX_RETRIES + 1}."
                        )
                        if event_obj is not None:  # Pattern 1 (event object)
                            await handler(event_obj)
                        else:  # Pattern 2 (event_type, data_dict)
                            handler_signature = inspect.signature(handler)
                            param_count = len(handler_signature.parameters)

                            # Provide attribute-style access when handlers expect an object input
                            payload_arg: Any = data_dict_payload
                            if isinstance(payload_arg, dict):
                                payload_arg = _EventPayload(payload_arg)

                            if param_count >= 2:
                                await handler(event_type_name, data_dict_payload)
                            else:
                                await handler(payload_arg)

                        logger.info(f"Handler '{handler_name}' successfully processed event '{event_type_name}' on attempt {attempt + 1}.")
                        break  # Success, exit retry loop
                    except Exception as e:
                        current_traceback = traceback.format_exc()
                        logger.error(
                            f"Error in event handler '{handler_name}' for event type '{event_type_name}' (attempt {attempt + 1}/{settings.EVENT_HANDLER_MAX_RETRIES + 1}). Error: {e}\nTraceback: {current_traceback}"
                        )
                        if attempt == settings.EVENT_HANDLER_MAX_RETRIES:
                            logger.error(
                                f"Handler '{handler_name}' failed after {settings.EVENT_HANDLER_MAX_RETRIES + 1} attempts for event '{event_type_name}'. Sending to DLQ if enabled."
                            )
                            if dlq_logger and settings.DLQ_ENABLED:
                                event_content_for_dlq_str = ""
                                if event_obj is not None: # Pattern 1
                                    try:
                                        # Attempt to serialize. For complex objects, __dict__ is a start, but might need custom serialization.
                                        # Ensure it's JSON serializable.
                                        serializable_event_data = event_obj.__dict__ if hasattr(event_obj, '__dict__') else str(event_obj)
                                        event_content_for_dlq_str = json.dumps(serializable_event_data)
                                    except TypeError: # Handle non-serializable objects
                                        event_content_for_dlq_str = json.dumps(str(event_obj)) # Fallback to string representation
                                    except Exception as serialization_exc:
                                        event_content_for_dlq_str = f"Could not serialize event: {serialization_exc}"
                                else: # Pattern 2
                                    try:
                                        event_content_for_dlq_str = json.dumps(data_dict_payload)
                                    except TypeError: # Handle non-serializable objects
                                        event_content_for_dlq_str = json.dumps(str(data_dict_payload)) # Fallback to string representation
                                    except Exception as serialization_exc:
                                        event_content_for_dlq_str = f"Could not serialize data: {serialization_exc}"

                                dlq_logger.error(
                                    "Failed event sent to DLQ",  # This message string is not used by formatter, but good for console
                                    extra={
                                        "event_type": event_type_name,
                                        "handler_name": handler_name,
                                        "error": str(e),
                                        "traceback": current_traceback,
                                        "event_data": event_content_for_dlq_str
                                    }
                                )
                            # Break from retry loop, proceed to next handler or finish
                            break
                        else:
                            logger.info(f"Retrying handler '{handler_name}' for event '{event_type_name}' after {settings.EVENT_HANDLER_RETRY_DELAY_SECONDS}s delay.")
                            await asyncio.sleep(settings.EVENT_HANDLER_RETRY_DELAY_SECONDS)
        else:
            logger.debug(f"No subscribers for event type {event_type_name}")

    async def shutdown(self):
        """
        Shutdown the event bus and clear all subscriptions.
        
        This method is primarily used for cleanup in tests and shutdown scenarios.
        """
        self.subscriptions.clear()
        if dlq_logger:
            for handler in dlq_logger.handlers[:]: # Iterate over a copy
                handler.close()
                dlq_logger.removeHandler(handler)
            logging.getLogger("dlq").handlers.clear()


        logger.info("EventBus shutdown complete. All subscriptions cleared and DLQ handlers closed.")
