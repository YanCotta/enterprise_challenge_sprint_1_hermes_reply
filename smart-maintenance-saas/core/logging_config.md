# Structured JSON Logging

This module provides structured JSON logging for the Smart Maintenance SaaS application. It configures the Python standard logging system to output logs in JSON format with consistent fields, making them easier to parse and analyze with log management systems.

## Key Features

- **JSON Format**: All logs are formatted as JSON objects for easier parsing and indexing
- **Standard Fields**: Every log entry includes timestamp, level, message, logger name, file, line number
- **Service Information**: Service name and hostname are included in each log entry
- **Request Tracking**: Support for correlation IDs to track requests across services
- **Extra Fields**: Support for adding custom fields to log entries
- **Async Support**: Works well with FastAPI and other async frameworks

## Usage

### Basic Setup

```python
from core.logging_config import setup_logging, get_logger

# Initialize logging at application startup
setup_logging()

# Get a module-level logger
logger = get_logger(__name__)

# Log messages
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
```

### Logging with Extra Fields

```python
logger.info(
    "User performed action",
    extra={
        "user_id": 123,
        "action": "login",
        "duration_ms": 120,
    },
)
```

### Class-based Logging

```python
class UserService:
    def __init__(self):
        self.logger = get_logger(f"{__name__}.UserService")
    
    def authenticate(self, username):
        self.logger.info("Authenticating user", extra={"username": username})
        # ...
```

### Exception Logging

```python
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
```

### Request Context Logging

The `RequestContextFilter` class can be used to add request context (like request IDs) to all logs during a request:

```python
@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_filter = RequestContextFilter(request_id)
    logger.addFilter(request_filter)
    
    try:
        # Process request
        response = await call_next(request)
        return response
    finally:
        # Always remove the filter
        logger.removeFilter(request_filter)
```

## Log Format

Each log entry includes:

- `timestamp`: ISO8601 format timestamp (UTC)
- `level`: Log level (INFO, WARNING, ERROR, etc.)
- `name`: Logger name
- `message`: Log message
- `service`: Service name
- `hostname`: Host identifier
- `file`: Source file
- `line`: Line number
- `process` and `process_name`: Process info
- `thread` and `thread_name`: Thread info
- `correlation_id`: Request ID (when available)
- Any additional fields passed via `extra`

## Example Output

```json
{
  "timestamp": "2025-05-28T12:30:38.161550Z",
  "level": "INFO",
  "name": "api",
  "message": "User authenticated successfully",
  "service": "smart-maintenance-saas",
  "hostname": "server-01",
  "file": "user_service.py",
  "line": 56,
  "process": 123456,
  "process_name": "MainProcess",
  "thread": 140123456789,
  "thread_name": "MainThread",
  "correlation_id": "44f05c3e-6723-4b97-a208-3d874a3c50c7",
  "username": "john.doe",
  "roles": ["user", "admin"],
  "auth_method": "password"
}
```
