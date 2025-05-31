"""
Test configuration for the Smart Maintenance SaaS application.

This module provides configurations and fixtures for tests, particularly
for handling test database connections.
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, Generator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from core.config import settings
from core.database.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """
    Start a PostgreSQL container with TimescaleDB for testing.
    
    This fixture is used for integration tests that require a real database.
    The container is started once per test session and is stopped after all tests.
    """
    # Only start container for integration tests
    if "PYTEST_DIRECT_DB" in os.environ:
        # Skip container creation and use direct connection
        yield None
        return

    postgres = PostgresContainer(
        "timescale/timescaledb:latest-pg15",
        user=settings.db_user,
        password=settings.db_password,
        dbname=settings.db_name,
    )
    postgres.start()

    # Set environment variables for tests to use
    os.environ["DATABASE_URL"] = postgres.get_connection_url()
    
    yield postgres
    
    postgres.stop()


@pytest.fixture(scope="session")
def test_db_url(postgres_container) -> str:
    """
    Get the database URL for tests.
    
    If using a test container, this will be the container's URL.
    Otherwise, it will use the DATABASE_TEST_URL from settings.
    """
    if postgres_container:
        return postgres_container.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
    elif "PYTEST_DIRECT_DB" in os.environ:
        # Use a direct connection to an existing test database
        return os.environ.get("DATABASE_TEST_URL", settings.database_url.replace(
            settings.db_name, f"{settings.db_name}_test"
        ))
    else:
        # Default to a test database on the development server
        return settings.database_url.replace(
            settings.db_name, f"{settings.db_name}_test"
        )


@pytest.fixture(scope="session")
async def db_engine(test_db_url) -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(test_db_url, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup - drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session for each test.
    
    This fixture uses nested transactions for test isolation.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()
    
    session_maker = async_sessionmaker(
        connection, expire_on_commit=False, autoflush=False
    )
    session = session_maker()
    
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
def test_settings() -> Dict:
    """
    Override settings for tests.
    
    This fixture lets tests override specific settings temporarily.
    """
    # Store original values
    original_values = {}
    
    def _override_settings(**kwargs):
        for key, value in kwargs.items():
            if hasattr(settings, key):
                original_values[key] = getattr(settings, key)
                setattr(settings, key, value)
            else:
                raise ValueError(f"Setting {key} does not exist")
        return settings
    
    yield _override_settings
    
    # Restore original values
    for key, value in original_values.items():
        setattr(settings, key, value)
