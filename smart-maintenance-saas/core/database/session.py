from typing import AsyncGenerator  # Import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config.settings import settings  # Corrected import path

# declarative_base is usually in orm_models.py now, so not typically needed here directly
# from sqlalchemy.ext.declarative import declarative_base


# If Base is defined in orm_models.py and truly needed here (e.g., for a utility script part of this file)
# from core.database.orm_models import Base # Corrected import path

# Construct the asynchronous database URL.
# It's assumed that settings.database_url is compatible with asyncpg (e.g., "postgresql+asyncpg://...").
# If settings.database_url was "postgresql://...", it would need to be adjusted.
# For example:
# async_db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1) # if settings.database_url.startswith("postgresql://") else settings.database_url
# We will proceed assuming settings.database_url is already correctly formatted for asyncpg.

SQLALCHEMY_DATABASE_URL = str(
    settings.database_url
)  # Ensure it's a string for manipulation

if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql+psycopg2://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://", 1
    )
# else: SQLALCHEMY_DATABASE_URL remains as is, assuming it's correct or a different DB type

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.debug,  # Log SQL statements if debug mode is on
    future=True,  # Use SQLAlchemy 2.0 style execution
)

# Configure an async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for FastAPI dependencies
    autocommit=False,
    autoflush=False,
)


# Async dependency for FastAPI to get a database session
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:  # Corrected return type
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Example utility function (optional, Alembic is preferred for schema management)
# async def init_db():
#     # Import Base from your orm_models.py where it's defined
#     from core.database.orm_models import Base
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all) # Use with caution
#         await conn.run_sync(Base.metadata.create_all)

# if __name__ == "__main__":
#     import asyncio
#     # Example of running the init_db utility
#     # asyncio.run(init_db())
