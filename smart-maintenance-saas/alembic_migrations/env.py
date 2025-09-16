import asyncio
import logging
import os
import sys

# Add the project root directory to the Python path
# This allows Alembic to find your 'smart_maintenance_saas' package
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from core.config.settings import settings

# Import your Base and your application settings
# Adjust the import path as per your project structure
from core.database.orm_models import Base

# Set the target metadata for autogenerate support
target_metadata = Base.metadata

# Load database URL from environment
db_url = os.environ.get("DATABASE_URL")

# Fallback to local settings if not in production
if not db_url and os.environ.get("ENV") != "production":
    logger.warning("DATABASE_URL not set, falling back to local alembic.ini config.")
    db_url = config.get_main_option("sqlalchemy.url")
elif not db_url:
    raise ValueError("DATABASE_URL environment variable not set for production-like environment.")

# --- CRITICAL FIX FOR ASYNC DRIVER ---
# Alembic is synchronous and doesn't understand the 'asyncpg' driver.
# We must replace it with a standard 'postgresql' string for migrations.
# The app (running uvicorn) will still use the original async URL from the .env.
sync_db_url = db_url.replace("+asyncpg", "")
# --- END CRITICAL FIX ---

# Set the sqlalchemy.url for Alembic
config.set_main_option("sqlalchemy.url", sync_db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=sync_db_url,  # Use the synchronous URL for offline migrations
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # compare_type=True, # Uncomment if you want to compare types during autogenerate
        # include_schemas=True, # If you have multiple schemas
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using synchronous engine.

    For cloud deployment, we use synchronous connections to avoid
    async driver issues during migrations.

    """
    # Use synchronous engine for migrations
    from sqlalchemy import create_engine
    
    connectable = create_engine(
        sync_db_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # compare_type=True, # Uncomment if you want to compare types during autogenerate
        # include_schemas=True, # If you have multiple schemas
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using synchronous engine.

    For cloud deployment, we use synchronous connections to avoid
    async driver issues during migrations.

    """
    # Use synchronous engine for migrations
    from sqlalchemy import create_engine
    
    connectable = create_engine(
        sync_db_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
