# Configuration Management

## 📚 Documentation Links

- **[Backend README](../../README.md)** - Main documentation and Docker deployment
- **[System Screenshots](../../docs/SYSTEM_SCREENSHOTS.md)** - Complete visual system walkthrough with screenshots
- **[System Architecture](../../docs/SYSTEM_AND_ARCHITECTURE.md)** - Complete system overview
- **[Future Roadmap](../../docs/FUTURE_ROADMAP.md)** - Strategic vision and planned enhancements
- **[Deployment Status](../../docs/DEPLOYMENT_STATUS.md)** - Current system status
- **[API Documentation](../../docs/api.md)** - Complete REST API reference and usage examples
- **[Test Documentation](../../tests/README.md)** - Test organization and execution guide
- **[Project Overview](../../../README.md)** - High-level project information

---

This module provides a centralized configuration system for the Smart Maintenance SaaS application using Pydantic's `BaseSettings`.

## Usage

### Basic Import

```python
from core.config import settings

# Use settings directly
database_url = settings.database_url
api_port = settings.api_port
```

### Dependency Injection (FastAPI)

```python
from fastapi import Depends
from core.config import get_settings, Settings

@app.get("/items")
def read_items(settings: Settings = Depends(get_settings)):
    return {"database": settings.database_url, "debug": settings.debug}
```

### Class-based Usage

```python
from core.config import settings

class DatabaseService:
    def __init__(self):
        self.connection_string = settings.database_url
        # Use other settings as needed
```

## Environment Variables

Configuration can be set via environment variables or a `.env` file. The `.env.example` file in the project root shows all available configuration options.

For Docker Compose setups, use service names (e.g., `db`) instead of `localhost`.

## Available Settings

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers
- `API_HOST`: Host to bind the API server
- `API_PORT`: Port for the API server
- `DEBUG`: Debug mode flag
- `SECRET_KEY`: Secret key for security features
- `LOG_LEVEL`: Logging level
- And many others as defined in the `Settings` class

## Adding New Settings

To add new settings:

1. Add the setting to the `Settings` class in `settings.py`
2. Add a default value
3. Update the `.env.example` file
4. Use the setting in your application via `settings.your_new_setting`
