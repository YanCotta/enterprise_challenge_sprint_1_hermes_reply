import logging  # For basic logging if setup_logging is not yet fully integrated

from fastapi import Depends, FastAPI, HTTPException
from apps.api.routers import data_ingestion, reporting, human_decision
from sqlalchemy import select  # Import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    yield

    # Shutdown
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


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


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
    reporting.router,
    prefix="/api/v1/reports",
    tags=["Reporting"]
)

app.include_router(
    human_decision.router,
    prefix="/api/v1/decisions",
    tags=["Human Decisions"]
)

# Root endpoint (optional)
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {app.title} v{app.version}"}


# If you want to run this directly with uvicorn for testing (though poetry script is better for prod-like)
# if __name__ == "__main__":
#     pass
