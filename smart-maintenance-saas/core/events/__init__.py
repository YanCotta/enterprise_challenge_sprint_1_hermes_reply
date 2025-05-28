"""
Core events package for the Smart Maintenance SaaS platform.

This package provides event-driven communication infrastructure used throughout
the application.
"""

from core.events.event_bus import event_bus, EventBus

__all__ = ['event_bus', 'EventBus']
