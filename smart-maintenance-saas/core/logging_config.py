"""
Logging configuration for the Smart Maintenance SaaS application.

This module provides a structured JSON logging setup that can be easily integrated
with log aggregation and analysis tools. It configures the Python standard logging
system to output logs in JSON format with consistent fields.
"""

import inspect
import logging
import logging.config
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds additional fields to log records.

    This formatter extends the standard JsonFormatter to add:
    - timestamp in ISO format
    - service name
    - correlation_id for request tracing
    - hostname for identifying the source
    """

    def __init__(self, *args, **kwargs):
        """Initialize the formatter with desired attributes."""
        super().__init__(*args, **kwargs)
        self.service_name = "smart-maintenance-saas"
        self.hostname = os.uname().nodename

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """
        Add custom fields to the log record.

        Args:
            log_record: The log record being built
            record: The original LogRecord
            message_dict: Additional fields from the log message
        """
        super().add_fields(log_record, record, message_dict)

        # Add ISO format timestamp
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        log_record["timestamp"] = now

        # Add service info
        log_record["service"] = self.service_name
        log_record["hostname"] = self.hostname

        # Add file and line info
        log_record["file"] = record.filename
        log_record["line"] = record.lineno

        # Ensure correlation_id is set
        correlation_id = getattr(record, "correlation_id", None)
        if not correlation_id and "correlation_id" in message_dict:
            correlation_id = message_dict.get("correlation_id")

        log_record["correlation_id"] = correlation_id if correlation_id else None

        # Add process and thread info
        log_record["process"] = record.process
        log_record["process_name"] = record.processName
        log_record["thread"] = record.thread
        log_record["thread_name"] = record.threadName


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure the logging system to use JSON formatting.

    Args:
        log_level: Optional override for the log level, defaults to settings.log_level
    """
    level = log_level or settings.log_level

    # Create formatter
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")

    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(console_handler)

    # Log startup message
    logging.info(
        "Logging system initialized",
        extra={
            "log_level": level,
            "format": "json",
        },
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: The name for the logger. If None, will use the caller's module name.

    Returns:
        A Logger instance
    """
    if name is None:
        # If no name provided, use the caller's module name
        frame = inspect.currentframe().f_back
        mod = inspect.getmodule(frame)
        name = mod.__name__ if mod else "unknown"

    return logging.getLogger(name)


class RequestContextFilter(logging.Filter):
    """
    A filter that adds request context to log records.

    This filter is useful for web applications to track request-specific
    information across log messages.
    """

    def __init__(self, request_id: Optional[str] = None):
        """Initialize with an optional request ID."""
        super().__init__()
        self.request_id = request_id or str(uuid.uuid4())

    def filter(self, record):
        """Add request_id to the log record."""
        record.correlation_id = self.request_id
        return True


# Example usage in a FastAPI application middleware:
#
# @app.middleware("http")
# async def add_request_id(request: Request, call_next):
#     request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
#     logger = logging.getLogger("api")
#
#     # Add filter for this request
#     request_filter = RequestContextFilter(request_id)
#     logger.addFilter(request_filter)
#
#     # Log the request
#     logger.info(f"Request received", extra={
#         "method": request.method,
#         "path": request.url.path,
#         "client_host": request.client.host if request.client else None,
#     })
#
#     try:
#         response = await call_next(request)
#         logger.info(f"Request completed", extra={
#             "status_code": response.status_code,
#         })
#         return response
#     finally:
#         # Remove the filter when done
#         logger.removeFilter(request_filter)
