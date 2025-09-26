import asyncio
import logging
import os
import sys
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

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

def _build_sync_db_url(raw_url: str) -> str:
    """Return a psycopg2-compatible URL for migrations.

    Steps:
      1. Strip +asyncpg driver (Alembic operates synchronously).
      2. Convert query parameter 'ssl=' (asyncpg style) to 'sslmode=' (psycopg2 style) if present.
      3. Leave existing 'sslmode=' untouched.
    """
    if not raw_url:
        raise ValueError("Empty database URL passed to _build_sync_db_url")

    sync_url = raw_url.replace("+asyncpg", "")

    try:
        parsed = urlparse(sync_url)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        query_dict = dict(query_pairs)

        # Transform asyncpg 'ssl=require' -> psycopg2 'sslmode=require'
        if "ssl" in query_dict and "sslmode" not in query_dict:
            query_dict["sslmode"] = query_dict.pop("ssl")

        new_query = urlencode(query_dict)
        rebuilt = urlunparse(parsed._replace(query=new_query))
        return rebuilt
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to normalize database URL for Alembic; falling back to raw URL")
        return sync_url


sync_db_url = _build_sync_db_url(db_url)

# Log the transformation for visibility (without credentials)
def _redact(url: str) -> str:
    if not url:
        return url
    try:
        p = urlparse(url)
        netloc = p.netloc
        if "@" in netloc:
            userinfo, hostpart = netloc.split("@", 1)
            if ":" in userinfo:
                user, _pw = userinfo.split(":", 1)
                redacted_netloc = f"{user}:***@{hostpart}"
            else:
                redacted_netloc = f"{userinfo}@{hostpart}"
            p = p._replace(netloc=redacted_netloc)
        return urlunparse(p)
    except Exception:
        return url

logger.info("Alembic using sync DB URL: %s", _redact(sync_db_url))

# Set the sqlalchemy.url for Alembic (important for script output and context)
config.set_main_option("sqlalchemy.url", sync_db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode with a URL only."""
    context.configure(
        url=sync_db_url,
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
        # compare_type=True,  # Enable if needed
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using a synchronous SQLAlchemy Engine."""
    from sqlalchemy import create_engine

    connectable = create_engine(sync_db_url, poolclass=pool.NullPool)
    try:
        with connectable.connect() as connection:
            do_run_migrations(connection)
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
