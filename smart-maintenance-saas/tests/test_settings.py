"""
Test script for verifying settings configuration.

This script imports and prints out the settings to verify they're loading correctly.
"""

from core.config.settings import settings


def main():
    """Print out the current settings."""
    print("Smart Maintenance SaaS - Current Settings")
    print("----------------------------------------")
    print(f"Database URL: {settings.database_url}")
    print(f"API Host: {settings.api_host}")
    print(f"API Port: {settings.api_port}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    print(f"Agent Communication Timeout: {settings.agent_communication_timeout}")
    print(f"Model Registry Path: {settings.model_registry_path}")
    print("----------------------------------------")


if __name__ == "__main__":
    main()
