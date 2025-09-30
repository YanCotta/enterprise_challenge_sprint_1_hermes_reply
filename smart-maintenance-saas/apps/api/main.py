import logging  # For basic logging if setup_logging is not yet fully integrated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apps.api.routers import data_ingestion, reporting, human_decision, sensor_readings, decisions, maintenance
from apps.api.middleware.request_id import RequestIDMiddleware
from sqlalchemy import select, text  # Import text for raw SQL
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from data.schemas import HealthStatus  # Import the new schema
from apps.api.dependencies import get_db, get_redis_client_dep  # Import new dependencies

# Import setup_logging from your logging configuration
try:
    from core.logging_config import setup_logging

    setup_logging()  # Call it to configure logging
except ImportError:
    logging.basicConfig(level=logging.INFO)  # Basic fallback logging
    logging.info("setup_logging not found, using basicConfig for logging.")

from contextlib import asynccontextmanager # Added import
from apps.system_coordinator import SystemCoordinator # Added import

from core.config.settings import settings

# Import the get_async_db dependency and settings
from core.database.session import (
    engine as async_engine,  # Import engine if needed for lifespan
)
from core.database.session import get_async_db
from core.redis_client import init_redis_client, close_redis_client
from core.security.api_keys import API_KEY_HEADER_NAME

# Rate limiting configuration
def get_api_key_identifier(request: Request):
    """Get rate limiting identifier from X-API-Key header, fallback to IP address."""
    api_key = request.headers.get(API_KEY_HEADER_NAME)
    if api_key:
        return f"api_key:{api_key}"
    return get_remote_address(request)

# Initialize rate limiter with in-memory store and API key identification
limiter = Limiter(key_func=get_api_key_identifier)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return rate limit errors in the FastAPI-standard format."""
    response = JSONResponse(
        {"detail": f"Rate limit exceeded: {exc.detail}"},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )
    response = request.app.state.limiter._inject_headers(  # type: ignore[attr-defined]
        response,
        request.state.view_rate_limit,
    )
    return response


def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Normalize FastAPI validation errors to a single detail string."""
    errors = []
    for err in exc.errors():
        loc = " → ".join(str(part) for part in err.get("loc", [])) or "payload"
        msg = err.get("msg", "Invalid input")
        errors.append(f"{loc}: {msg}")

    max_items = 5
    truncated = len(errors) > max_items
    summary = "; ".join(errors[:max_items]) if errors else "Request validation failed"
    if truncated:
        summary = f"{summary}; (+{len(errors) - max_items} more validation issues)"

    logging.warning("Request validation error on %s: %s", request.url.path, summary)
    return JSONResponse(
        {"detail": f"Request validation failed: {summary}"},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

# Optional: Import routers if you have them (e.g., for Task 7)
# from .routers import sensor_readings_router

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Application startup: Initializing SystemCoordinator...")
    coordinator = SystemCoordinator()
    app.state.coordinator = coordinator
    try:
        await coordinator.startup_system()
        logging.info("SystemCoordinator started successfully.")
    except Exception as e:
        logging.error(f"Error during SystemCoordinator startup: {e}", exc_info=True)
        # Optionally, re-raise or handle to prevent app startup if critical

    # Initialize Redis client
    logging.info("Initializing Redis client...")
    try:
        redis_client = await init_redis_client()
        app.state.redis_client = redis_client
        logging.info("Redis client initialized successfully.")
    except Exception as e:
        logging.error(f"Error during Redis client initialization: {e}", exc_info=True)
        # Continue without Redis - graceful degradation

    # Expose the /metrics endpoint
    instrumentator.expose(app, include_in_schema=False)
    logging.info("Prometheus metrics endpoint exposed at /metrics")

    yield

    # Shutdown
    logging.info("Application shutdown: Shutting down Redis client...")
    try:
        await close_redis_client()
        logging.info("Redis client shutdown successfully.")
    except Exception as e:
        logging.error(f"Error during Redis client shutdown: {e}", exc_info=True)

    logging.info("Application shutdown: Shutting down SystemCoordinator...")
    if hasattr(app.state, 'coordinator') and app.state.coordinator:
        try:
            await app.state.coordinator.shutdown_system()
            logging.info("SystemCoordinator shutdown successfully.")
        except Exception as e:
            logging.error(f"Error during SystemCoordinator shutdown: {e}", exc_info=True)
    else:
        logging.warning("SystemCoordinator not found on app.state during shutdown.")
    logging.info("Application shutdown sequence complete.")


# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME
    if hasattr(settings, "PROJECT_NAME")
    else "Smart Maintenance SaaS API",
    version=settings.VERSION if hasattr(settings, "VERSION") else "0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
    if hasattr(settings, "API_V1_STR")
    else "/openapi.json",
    lifespan=lifespan  # Add this
)

# Set up rate limiting state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

# Instrument the app with default metrics (latency, requests, etc.)
instrumentator = Instrumentator().instrument(app)

# Middleware
app.add_middleware(RequestIDMiddleware)


# Comprehensive health check endpoint
@app.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Endpoint de health check que verifica a conectividade com dependências críticas.
    
    Retorna:
    - HTTP 200 OK se todas as dependências estiverem funcionando
    - HTTP 503 Service Unavailable se alguma dependência falhar
    
    Verifica:
    - Conexão com o banco de dados TimescaleDB
    - Conexão com o Redis
    """
    db_status = "ok"
    redis_status = "ok"
    overall_status = "ok"
    http_status = 200
    
    # Verificar conexão com o banco de dados
    try:
        async for db in get_async_db():
            await db.execute(text("SELECT 1"))
            break  # Just need one session to test
        db_status = "ok"
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        db_status = "failed"
        overall_status = "degraded"
        http_status = 503
    
    # Verificar conexão com o Redis
    try:
        # Try to get Redis client from app state first, fallback to dependency
        if hasattr(app.state, 'redis_client') and app.state.redis_client:
            async with app.state.redis_client.get_redis() as redis:
                await redis.ping()
        else:
            # Fallback - try to create a temporary connection
            from core.redis_client import get_redis_client
            redis_client = await get_redis_client()
            async with redis_client.get_redis() as redis:
                await redis.ping()
        redis_status = "ok"
    except Exception as e:
        logging.error(f"Redis health check failed: {e}")
        redis_status = "failed"
        overall_status = "degraded"
        http_status = 503
    
    response = HealthStatus(
        status=overall_status,
        database=db_status,
        redis=redis_status
    )
    
    # Se houver falhas, retornar com código de status apropriado
    if http_status != 200:
        if getattr(settings, "HEALTHCHECK_ENFORCE_DEPENDENCIES", False):
            raise HTTPException(status_code=http_status, detail=response.dict())
        return response

    return response


# Database health check endpoint
@app.get("/health/db", tags=["Health"])
async def health_check_db(db: AsyncSession = Depends(get_async_db)):
    try:
        # Execute a simple query to check DB connection
        result = await db.execute(select(1))
        if result.scalar_one() == 1:
            return {"db_status": "connected"}
        else:
            # This case should ideally not happen if execute itself doesn't error
            raise HTTPException(
                status_code=503,
                detail="Database connectivity check failed: Unexpected result.",
            )
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503, detail=f"Database connection error: {str(e)}"
        )


# Redis health check endpoint
@app.get("/health/redis", tags=["Health"])
async def health_check_redis():
    """Check Redis connectivity and basic stats."""
    try:
        from core.redis_client import get_redis_client
        redis_client = await get_redis_client()
        health_info = await redis_client.health_check()
        
        if health_info["status"] in ["healthy"]:
            return health_info
        else:
            raise HTTPException(
                status_code=503, 
                detail=f"Redis health check failed: {health_info}"
            )
    except Exception as e:
        logging.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=503, detail=f"Redis connection error: {str(e)}"
        )


# Include routers (example for optional Task 7)
# app.include_router(
#     sensor_readings_router.router,
#     prefix="/api/v1/sensor-readings", # Or use settings.API_V1_STR
#     tags=["Sensor Readings"]
# )

# Include API V1 routers
app.include_router(
    data_ingestion.router,
    prefix="/api/v1/data",
    tags=["Data Ingestion"]
)

app.include_router(
    sensor_readings.router,
    prefix="/api/v1/sensors",
    tags=["Sensor Readings"]
)

app.include_router(
    reporting.router,
    prefix="/api/v1/reports",
    tags=["Reporting"]
)

app.include_router(
    maintenance.router,
    prefix="/api/v1/maintenance",
    tags=["Maintenance"]
)

app.include_router(
    human_decision.router,
    prefix="/api/v1/decisions",
    tags=["Human Decisions"]
)

# Decision Log (audit) endpoint - read-only historical maintenance/decision records
app.include_router(
    decisions.router,
)

# Include ML endpoints router for Day 12
from apps.api.routers import ml_endpoints
app.include_router(
    ml_endpoints.router,
    prefix="/api/v1/ml",
    tags=["Machine Learning"]
)

# Include simulation router for Day 2 live demo
from apps.api.routers import simulate, demo
app.include_router(
    simulate.router,
    tags=["Live Demo Simulation"]
)

app.include_router(
    demo.router,
)

# Root endpoint (optional)
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {app.title} v{app.version}"}


# If you want to run this directly with uvicorn for testing (though poetry script is better for prod-like)
# if __name__ == "__main__":
#     pass
