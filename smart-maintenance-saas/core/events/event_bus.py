"""
Event Bus for inter-agent communication in Smart Maintenance SaaS.

This module provides a simple, in-memory event bus for asynchronous communication
between different components and agents in the system. Events are published by
type and can be subscribed to by multiple handlers.
"""

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[Any], Any]


class EventBus:
    """
    A simple in-memory event bus for asynchronous inter-agent communication.
    
    This implementation supports:
    - Subscribing handlers to specific event types
    - Publishing events to all subscribed handlers
    - Asynchronous event handling
    - Basic error handling and logging
    
    Future enhancements will include Redis/Kafka integration.
    """
    
    def __init__(self):
        """Initialize the EventBus with an empty subscribers dictionary."""
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe a handler to a specific event type.
        
        Args:
            event_type: The type of event to subscribe to (string identifier)
            handler: Callable that will be invoked when the event is published
        """
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            # Avoid duplicate subscriptions
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
                logger.info(f"Handler subscribed to event type: {event_type}")
    
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """
        Unsubscribe a handler from a specific event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove from subscribers
            
        Returns:
            bool: True if handler was removed, False otherwise
        """
        async with self._lock:
            if event_type in self._subscribers and handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.info(f"Handler unsubscribed from event type: {event_type}")
                return True
            return False
    
    async def publish(self, event_type: str, data: Any = None) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event_type: The type of event being published
            data: The event data to be passed to handlers
        """
        if event_type not in self._subscribers:
            logger.debug(f"No subscribers found for event type: {event_type}")
            return
        
        # Get handlers while holding the lock, then release for execution
        handlers = []
        async with self._lock:
            handlers = self._subscribers[event_type].copy()
        
        # Create tasks for all handlers
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._call_handler(handler, data))
            tasks.append(task)
        
        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f"Published event {event_type} to {len(tasks)} handlers")
    
    async def _call_handler(self, handler: EventHandler, data: Any) -> None:
        """
        Call a handler with the given data, handling async and sync functions appropriately.
        
        Args:
            handler: The handler function to call
            data: The data to pass to the handler
        """
        try:
            if inspect.iscoroutinefunction(handler):
                # Handler is async, await it
                await handler(data)
            else:
                # Handler is sync, run in thread pool
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: handler(data))
        except Exception as e:
            logger.error(f"Error in event handler: {str(e)}", exc_info=True)


# Singleton instance for application-wide use
event_bus = EventBus()


# Example usage
async def example_usage():
    """Example demonstrating how to use the EventBus."""
    # Example handler functions
    async def async_handler(data):
        print(f"Async handler received: {data}")
    
    def sync_handler(data):
        print(f"Sync handler received: {data}")
    
    # Subscribe handlers to events
    await event_bus.subscribe("maintenance.alert", async_handler)
    await event_bus.subscribe("maintenance.alert", sync_handler)
    await event_bus.subscribe("sensor.data", sync_handler)
    
    # Publish events
    await event_bus.publish("maintenance.alert", {"machine_id": "M123", "severity": "high"})
    await event_bus.publish("sensor.data", {"machine_id": "M123", "temperature": 85.6})
    
    # Unsubscribe a handler
    await event_bus.unsubscribe("maintenance.alert", sync_handler)


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())
