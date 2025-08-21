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
    """Create an instance of the default event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    
    # Set the loop as the current loop for this thread
    asyncio.set_event_loop(loop)
    
    try:
        yield loop
    finally:
        # Clean up properly
        if not loop.is_closed():
            # Cancel any remaining tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Wait for cancellation to complete
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            loop.close()
        
        # Reset the event loop policy
        asyncio.set_event_loop(None)


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
        username=settings.db_user,
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

    Args:
        postgres_container: A running PostgreSQL container fixture, if being used

    Returns:
        str: A database URL string configured for asyncpg

    Raises:
        ValueError: If the database URL scheme is not supported for async operations
    """
    # Get the raw URL based on the test configuration
    raw_url = None
    if postgres_container:
        raw_url = postgres_container.get_connection_url()
    elif "PYTEST_DIRECT_DB" in os.environ:
        # Use explicit test database URL from environment or settings
        raw_url = os.environ.get(
            "DATABASE_TEST_URL",
            getattr(
                settings,
                "test_database_url",
                str(settings.database_url).replace(
                    settings.db_name, f"{settings.db_name}_test"
                ),
            ),
        )
    else:
        # Default to a test database on the development server
        raw_url = str(settings.database_url).replace(
            settings.db_name, f"{settings.db_name}_test"
        )

    # Convert raw_url to string if it's not already
    raw_url = str(raw_url)

    # Handle different URL schemes to ensure asyncpg is used
    if raw_url.startswith("postgresql+asyncpg://"):
        return raw_url
    elif raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql+psycopg2://"):
        return raw_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    else:
        raise ValueError(
            f"Unsupported database URL scheme for async operations: {raw_url}. "
            "URL must start with 'postgresql://' or 'postgresql+psycopg2://' "
            "to be converted to asyncpg, or already be 'postgresql+asyncpg://'."
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
def test_settings() -> Generator[Dict, None, None]:
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
