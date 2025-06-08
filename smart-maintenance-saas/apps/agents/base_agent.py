"""Base agent module providing core functionality for all AI agents in the system.

The core BaseAgent abstract class and AgentCapability dataclass have been moved to
smart-maintenance-saas.core.base_agent_abc to resolve circular dependencies.
This file is retained for any potential future app-specific base functionalities
or if it's used to re-export symbols.
"""

import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

# AgentCapability and BaseAgent definitions are now in core.base_agent_abc
# Ensure agents that previously imported from here now import from:
# from core.base_agent_abc import BaseAgent, AgentCapability
