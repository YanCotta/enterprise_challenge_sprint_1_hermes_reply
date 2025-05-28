"""
Example module demonstrating how to use the JSON logging system.

This module shows various examples of using the logging system
in different parts of the application.
"""

import logging
import time
from typing import Dict

from core.logging_config import get_logger, setup_logging

# Example 1: Basic logging in a module
logger = get_logger(__name__)


def basic_logging_example():
    """Demonstrate basic logging functionality."""
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")


# Example 2: Logging with extra fields
def logging_with_extra_fields(user_id: int, action: str):
    """Demonstrate logging with additional contextual information."""
    logger.info(
        f"User performed action: {action}",
        extra={
            "user_id": user_id,
            "action": action,
            "duration_ms": 120,
        },
    )


# Example 3: Logging in a class
class UserService:
    """Example service class with logging."""
    
    def __init__(self):
        """Initialize with a class-specific logger."""
        self.logger = get_logger(f"{__name__}.UserService")
    
    def authenticate(self, username: str) -> Dict:
        """Simulate user authentication with logging."""
        self.logger.info(f"Authenticating user", extra={"username": username})
        
        # Simulate some work
        time.sleep(0.1)
        
        # Log success with extra fields
        self.logger.info(
            "User authenticated successfully",
            extra={
                "username": username,
                "roles": ["user", "admin"],
                "auth_method": "password",
            },
        )
        
        return {"username": username, "authenticated": True}


# Example 4: Logging exceptions
def exception_example():
    """Demonstrate exception logging."""
    try:
        result = 1 / 0  # This will raise a ZeroDivisionError
    except Exception as e:
        logger.exception(
            "Error during calculation",
            extra={
                "operation": "division",
                "error_type": type(e).__name__,
            },
        )


# Example 5: Performance logging
def performance_logging_example():
    """Demonstrate logging performance metrics."""
    start_time = time.time()
    
    # Simulate some work
    time.sleep(0.5)
    
    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(
        "Operation completed",
        extra={
            "operation": "data_processing",
            "duration_ms": elapsed_ms,
            "records_processed": 1000,
        },
    )


def main():
    """Run all the examples."""
    # Initialize logging
    setup_logging()
    
    logger.info("Starting logging examples")
    
    # Run all examples
    basic_logging_example()
    logging_with_extra_fields(user_id=123, action="login")
    
    user_service = UserService()
    user_service.authenticate("john.doe")
    
    exception_example()
    performance_logging_example()
    
    logger.info("Logging examples completed")


if __name__ == "__main__":
    main()
