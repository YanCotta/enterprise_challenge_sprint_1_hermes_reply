import asyncio
import importlib

import pytest

from core.events.event_models import SensorDataReceivedEvent


@pytest.mark.asyncio
async def test_event_bus_retries_failed_handler(monkeypatch):
    event_bus = importlib.import_module("core.events.event_bus")
    monkeypatch.setattr(event_bus.settings, "EVENT_HANDLER_MAX_RETRIES", 2, raising=False)
    monkeypatch.setattr(event_bus.settings, "EVENT_HANDLER_RETRY_DELAY_SECONDS", 0.0, raising=False)

    bus = event_bus.EventBus()
    await bus.start()

    call_count = {"value": 0}

    async def flaky_handler(event):
        call_count["value"] += 1
        if call_count["value"] <= event_bus.settings.EVENT_HANDLER_MAX_RETRIES:
            raise RuntimeError("simulated handler failure")

    await bus.subscribe("SensorDataReceivedEvent", flaky_handler)

    event = SensorDataReceivedEvent(raw_data={"value": 42}, sensor_id="sensor-1")

    await bus.publish(event)

    assert call_count["value"] == event_bus.settings.EVENT_HANDLER_MAX_RETRIES + 1


@pytest.mark.asyncio
async def test_event_bus_logs_dlq_after_max_failures(monkeypatch):
    event_bus = importlib.import_module("core.events.event_bus")
    monkeypatch.setattr(event_bus.settings, "EVENT_HANDLER_MAX_RETRIES", 1, raising=False)
    monkeypatch.setattr(event_bus.settings, "EVENT_HANDLER_RETRY_DELAY_SECONDS", 0.0, raising=False)

    class DummyDLQLogger:
        def __init__(self):
            self.calls = []

        def error(self, message, *, extra=None):
            self.calls.append((message, extra))

    dummy_logger = DummyDLQLogger()
    monkeypatch.setattr(event_bus, "dlq_logger", dummy_logger, raising=False)

    bus = event_bus.EventBus()
    await bus.start()

    async def failing_handler(event):
        raise RuntimeError("always failing")

    await bus.subscribe("SensorDataReceivedEvent", failing_handler)

    event = SensorDataReceivedEvent(raw_data={"value": 99}, sensor_id="sensor-99")

    await bus.publish(event)

    assert dummy_logger.calls, "DLQ logger should record the failed event"
