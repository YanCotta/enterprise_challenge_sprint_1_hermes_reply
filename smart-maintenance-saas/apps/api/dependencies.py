import logging
from typing import Optional

from fastapi import Security, HTTPException, status, Depends
from fastapi.security import SecurityScopes
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import os
from core.config.settings import settings
from core.database.session import get_async_db
from core.redis_client import get_redis_client


def _load_allowed_api_keys() -> set[str]:
    """Return the configured set of allowed API keys."""
    allowed_keys: set[str] = set()

    primary_key = os.getenv("API_KEY", getattr(settings, "API_KEY", None))
    if primary_key:
        allowed_keys.add(primary_key)

    additional_keys = os.getenv("API_KEYS") or os.getenv("ALLOWED_API_KEYS")
    if additional_keys:
        for key in additional_keys.split(","):
            key = key.strip()
            if key:
                allowed_keys.add(key)

    return allowed_keys

API_KEY_NAME = "X-API-Key" # Ensure this matches the client-side header name
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: Optional[str] = Security(api_key_header)):
    """
    Simple API key authentication dependency that validates against environment variable.
    """
    if not api_key:
        if getattr(settings, "ALLOW_ANONYMOUS_API_ACCESS", True):
            logging.getLogger(__name__).debug(
                "API key missing but ALLOW_ANONYMOUS_API_ACCESS=True; continuing without key."
            )
            return None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing: X-API-KEY header is required"
        )

    allowed_keys = _load_allowed_api_keys()
    if not allowed_keys or api_key not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key

async def api_key_auth(
    security_scopes: SecurityScopes,
    api_key_header_value: Optional[str] = Security(api_key_header) # Corrected: api_key_header_value
):
    """
    FastAPI dependency to validate an API key and placeholder for RBAC scope checking.
    """
    # This is a basic API key check.
    # TODO: Enhance with actual RBAC, checking security_scopes against user/client permissions.
    if not api_key_header_value: # Corrected: check api_key_header_value
        if getattr(settings, "ALLOW_ANONYMOUS_API_ACCESS", True):
            logging.getLogger(__name__).debug(
                "Anonymous API access allowed; treating request as unauthenticated."
            )
            return {"api_key": None, "scopes": security_scopes.scopes}
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated: API key required." # Updated detail
        )

    allowed_keys = _load_allowed_api_keys()
    if not allowed_keys or api_key_header_value not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: Invalid API key." # Updated detail
        )

    # Placeholder for scope logging/awareness
    if security_scopes.scopes:
        # In a real app, you'd use a proper logger here
        print(f"Required scopes: {security_scopes.scopes}")
        # Here you would add logic to check if the token (API key) has these scopes.
        # For now, we just log them.

    # Return a dictionary that could be used by the endpoint if needed,
    # e.g., to access user details or validated scopes.
    return {"api_key": api_key_header_value, "scopes": security_scopes.scopes}


# Database dependency
async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    """
    async for session in get_async_db():
        yield session


# Redis dependency
async def get_redis_client_dep() -> Redis:
    """
    Dependency to get Redis client.
    """
    redis_client = await get_redis_client()
    async with redis_client.get_redis() as redis:
        yield redis
