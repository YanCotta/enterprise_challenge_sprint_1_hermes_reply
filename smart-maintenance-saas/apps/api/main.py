import logging  # For basic logging if setup_logging is not yet fully integrated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select  # Import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import setup_logging from your logging configuration
try:
    from core.logging_config import setup_logging

    setup_logging()  # Call it to configure logging
except ImportError:
    logging.basicConfig(level=logging.INFO)  # Basic fallback logging
    logging.info("setup_logging not found, using basicConfig for logging.")


from core.config.settings import settings

# Import the get_async_db dependency and settings
from core.database.session import (
    engine as async_engine,  # Import engine if needed for lifespan
)
from core.database.session import get_async_db

# Optional: Import routers if you have them (e.g., for Task 7)
# from .routers import sensor_readings_router

# Lifespan context manager for startup/shutdown events (optional, but good for resources)
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup: e.g., connect to DB, load ML models
#     logging.info("Application startup...")
#     # Example: You might want to check DB connection on startup, though /health/db is more for on-demand checks
#     # try:
#     #     async with async_engine.connect() as connection:
#     #         await connection.execute(select(1))
#     #     logging.info("Database connection successful on startup.")
#     # except Exception as e:
#     #     logging.error(f"Database connection failed on startup: {e}")
#     yield
#     # Shutdown: e.g., close DB connections gracefully
#     logging.info("Application shutdown...")
#     if async_engine:
#         await async_engine.dispose()


# Create FastAPI app instance
# app = FastAPI(title="Smart Maintenance SaaS API", version="0.1.0", lifespan=lifespan)
app = FastAPI(
    title=settings.PROJECT_NAME
    if hasattr(settings, "PROJECT_NAME")
    else "Smart Maintenance SaaS API",
    version=settings.VERSION if hasattr(settings, "VERSION") else "0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
    if hasattr(settings, "API_V1_STR")
    else "/openapi.json",
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


# Root endpoint (optional)
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {app.title} v{app.version}"}


# If you want to run this directly with uvicorn for testing (though poetry script is better for prod-like)
# if __name__ == "__main__":
#     pass
