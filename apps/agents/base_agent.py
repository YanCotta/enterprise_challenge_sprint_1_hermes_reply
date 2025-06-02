import asyncio
import logging
from typing import Callable, Any, Optional, Dict, List  # Added List


class BaseAgent:
    def __init__(
        self, agent_id: str, event_bus: Any, specific_settings: Optional[Dict] = None
    ):
        self.agent_id = agent_id
        self.event_bus = event_bus  # Should be an instance of an EventBus class
        self.specific_settings = (
            specific_settings if specific_settings is not None else {}
        )
        self.logger = logging.getLogger(f"agent.{self.agent_id}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:  # Add a default handler if none are configured
            stream_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

        self._is_running = False
        self._tasks: List[asyncio.Task] = (
            []
        )  # To keep track of background tasks, added type hint for _tasks

    async def register_capabilities(self) -> None:
        """
        Agents should override this method to register their capabilities
        or subscriptions with the event bus or other central services.
        This method is called before start().
        """
        self.logger.info(f"Agent {self.agent_id} registering capabilities (if any).")
        # Example: await self.event_bus.register_agent_capabilities(self.agent_id, self.get_capabilities())

    async def start(self) -> None:
        """
        Starts the agent's operations.
        This typically involves setting up subscriptions or starting periodic tasks.
        """
        if self._is_running:
            self.logger.warning(f"Agent {self.agent_id} is already running.")
            return

        self.logger.info(f"Agent {self.agent_id} starting...")
        await self.register_capabilities()  # Ensure capabilities are registered before main start logic
        self._is_running = True
        # Subclasses will add their specific startup logic here,
        # often involving subscribing to event types.

    async def stop(self) -> None:
        """
        Stops the agent's operations.
        This involves cleaning up resources, unsubscribing from events,
        and ensuring graceful shutdown of any running tasks.
        """
        self.logger.info(f"Agent {self.agent_id} stopping...")
        self._is_running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(
            *self._tasks, return_exceptions=True
        )  # Wait for tasks to cancel
        self._tasks = []
        # Example: await self.event_bus.unsubscribe_all(self.agent_id)
        self.logger.info(f"Agent {self.agent_id} stopped.")

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribes to a specific event type on the event bus.
        The handler will be called when an event of this type is published.
        """
        if not self.event_bus or not hasattr(self.event_bus, "subscribe"):
            self.logger.error(
                "Event bus not available or does not support 'subscribe' method."
            )
            return

        self.logger.info(
            f"Agent {self.agent_id} subscribing to event type: {event_type}"
        )
        # The actual subscription mechanism depends on the event_bus implementation.
        # This might involve creating a task that listens on a queue.
        # For simplicity, we'll assume event_bus.subscribe handles the async listening.
        # If event_bus.subscribe itself is a coroutine that sets up a listener:
        # await self.event_bus.subscribe(event_type, handler, agent_id=self.agent_id)
        # Or if it's synchronous and we need to wrap the handler:
        # self.event_bus.subscribe(event_type, lambda event: asyncio.create_task(handler(event)))

        # For this example, let's assume subscribe can take an async handler directly
        # and the event bus manages running it.
        # A more robust implementation would involve task management here.
        # Example:
        # async def event_listener_task():
        #    await self.event_bus.subscribe_and_listen(event_type, handler)
        # task = asyncio.create_task(event_listener_task())
        # self._tasks.append(task) # Make sure self._tasks is typed List[asyncio.Task]

        # Simplified: assume event_bus handles this.
        # This is a placeholder for actual event bus interaction.
        await self.event_bus.subscribe(event_type, handler)

    async def publish_event(self, event: Any) -> None:
        """
        Publishes an event to the event bus.
        """
        if not self.event_bus or not hasattr(self.event_bus, "publish"):
            self.logger.error(
                "Event bus not available or does not support 'publish' method."
            )
            return

        self.logger.debug(
            f"Agent {self.agent_id} publishing event: {event.event_type if hasattr(event, 'event_type') else type(event)}"
        )
        await self.event_bus.publish(event)

    def is_running(self) -> bool:
        return self._is_running


# Example (Illustrative) EventBus
class MockEventBus:
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger("MockEventBus")

    async def subscribe(
        self, event_type: str, handler: Callable, agent_id: Optional[str] = None
    ):
        self.logger.info(
            f"Handler subscribed to {event_type} (Agent: {agent_id or 'Unknown'})"
        )
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)

    async def publish(self, event: Any):
        event_type = getattr(event, "event_type", type(event).__name__)
        self.logger.info(f"Publishing event of type {event_type}")
        if event_type in self.subscriptions:
            for handler in self.subscriptions[event_type]:
                # In a real bus, you'd handle sync/async handlers appropriately
                # and potentially run them in separate tasks.
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    try:
                        handler(event)  # For sync handlers, though agents use async
                    except Exception as e:
                        self.logger.error(
                            f"Error in sync handler for {event_type}: {e}"
                        )
        else:
            self.logger.warning(f"No subscribers for event type {event_type}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    async def example_event_handler(event):
        print(f"Example handler received event: {event}")

    async def main():
        bus = MockEventBus()
        agent1 = BaseAgent(agent_id="test_agent_1", event_bus=bus)

        await agent1.start()
        # In a real scenario, subscribe would be called within start or by a capability registration
        await bus.subscribe(
            "TestEvent", example_event_handler
        )  # Manual subscribe for test

        await bus.publish({"event_type": "TestEvent", "data": "Hello World"})
        await asyncio.sleep(0.1)  # Give time for event to be processed

        await agent1.stop()

    asyncio.run(main())
