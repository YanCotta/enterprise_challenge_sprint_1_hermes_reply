"""
Example of integrating the JSON logging system with FastAPI.

This module demonstrates how to properly set up logging in a FastAPI application,
including request context logging.
"""

import logging
import uuid
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import settings
from core.logging_config import RequestContextFilter, get_logger, setup_logging

# Set up logging at application startup
setup_logging()

# Get a module-level logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Smart Maintenance SaaS API",
    description="API for Smart Maintenance SaaS platform",
    version="0.1.0",
)


@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    """
    Middleware to add request context to all logs during a request.
    
    This middleware:
    1. Extracts or generates a request ID
    2. Adds a filter to the logger for this request context
    3. Logs request details
    4. Processes the request
    5. Logs response details
    6. Cleans up the logger filter
    """
    # Extract request ID from headers or generate a new one
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Create a request-specific logger filter
    request_filter = RequestContextFilter(request_id)
    logger.addFilter(request_filter)
    
    # Add request ID to response headers
    response = None
    
    # Log the incoming request
    logger.info(
        f"Request received: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_host": request.client.host if request.client else None,
            "client_port": request.client.port if request.client else None,
        },
    )
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Log the response
        logger.info(
            f"Request completed: {response.status_code}",
            extra={
                "status_code": response.status_code,
                "processing_time_ms": None,  # Could add timing logic here
            },
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
    
    except Exception as e:
        # Log any unhandled exceptions
        logger.exception(
            f"Unhandled exception during request processing: {str(e)}",
            extra={
                "error_type": type(e).__name__,
            },
        )
        
        # Return a 500 error
        error_response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
        error_response.headers["X-Request-ID"] = request_id
        return error_response
    
    finally:
        # Always remove the filter to avoid memory leaks
        logger.removeFilter(request_filter)


@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    logger.info("Root endpoint called")
    return {"message": "Welcome to Smart Maintenance SaaS API"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    """
    Example endpoint that demonstrates logging with context.
    
    Args:
        item_id: The ID of the item to retrieve
        q: An optional query parameter
    """
    logger.info(
        f"Item requested: {item_id}",
        extra={
            "item_id": item_id,
            "query_param": q,
        },
    )
    
    return {"item_id": item_id, "query": q}


@app.post("/maintenance/alert")
async def create_alert(alert_data: dict):
    """
    Example endpoint for creating a maintenance alert.
    
    Args:
        alert_data: Alert details
    """
    logger.info(
        f"Maintenance alert created",
        extra={
            "machine_id": alert_data.get("machine_id"),
            "severity": alert_data.get("severity"),
            "alert_type": alert_data.get("type"),
        },
    )
    
    return {"status": "alert_created", "id": str(uuid.uuid4())}


if __name__ == "__main__":
    # Log application startup
    logger.info(
        f"Starting Smart Maintenance SaaS API",
        extra={
            "host": settings.api_host,
            "port": settings.api_port,
            "debug": settings.debug,
        },
    )
    
    # Start Uvicorn server
    uvicorn.run(
        "examples.fastapi_logging_example:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_config=None,  # Disable Uvicorn's default logging
    )
