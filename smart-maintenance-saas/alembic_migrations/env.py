import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your Base and your application settings
# Adjust the import path as per your project structure
from smart_maintenance_saas.core.database.orm_models import Base
from smart_maintenance_saas.core.config.settings import settings

# Set the target metadata for autogenerate support
target_metadata = Base.metadata

# Get the database URL from your application settings
# Ensure this URL is for an async driver (e.g., postgresql+asyncpg://)
db_url = settings.database_url

# You can override the sqlalchemy.url from alembic.ini if needed,
# or simply rely on this db_url. For simplicity, we'll use db_url directly.
# config.set_main_option('sqlalchemy.url', db_url)


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
        url=db_url,  # Use the URL from settings
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


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create an async engine from the URL in settings
    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool, # Recommended for Alembic async
        future=True # Use SQLAlchemy 2.0 features
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
