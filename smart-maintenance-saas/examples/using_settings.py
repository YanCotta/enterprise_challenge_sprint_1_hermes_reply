"""
Example module demonstrating how to use settings in your application components.

This is a simple example showing best practices for importing and using the
settings module in your application.
"""

from fastapi import Depends, FastAPI

from core.config import get_settings, settings
from core.config.settings import Settings


# Example 1: Direct import of the settings singleton
def example_direct_import():
    """Example of direct import of settings."""
    print(f"Database URL: {settings.database_url}")
    print(f"API will run on: {settings.api_host}:{settings.api_port}")


# Example 2: Dependency injection with FastAPI
app = FastAPI()


@app.get("/settings")
def read_settings(config: Settings = Depends(get_settings)):
    """Example endpoint showing settings via dependency injection."""
    return {
        "database": config.database_url,
        "api_host": config.api_host,
        "api_port": config.api_port,
        "debug": config.debug,
    }


# Example 3: Using settings in a class
class DatabaseClient:
    """Example class using settings for configuration."""

    def __init__(self, config: Settings = None):
        """Initialize the database client with settings."""
        self.config = config or settings
        self.db_url = self.config.database_url
        print(f"Connecting to database: {self.db_url}")

    def connect(self):
        """Simulate connecting to the database."""
        return f"Connected to {self.db_url}"


if __name__ == "__main__":
    # Example usage
    example_direct_import()

    # Using in a class
    db_client = DatabaseClient()
    print(db_client.connect())
