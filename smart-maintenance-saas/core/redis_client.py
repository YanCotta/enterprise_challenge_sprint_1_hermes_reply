"""
Redis client for distributed caching and idempotency management.

This module provides a clean, async interface for Redis operations,
specifically designed for idempotency checks using Redis's atomic operations.
"""

import asyncio
import logging
import os
from typing import Optional, Union
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client for distributed caching and idempotency management.
    
    Provides high-level operations for idempotency checking using Redis's
    atomic SET command with NX (not exists) and EX (expire) options.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var or redis service)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self._redis: Optional[Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
    
    async def connect(self) -> None:
        """
        Establish connection pool to Redis server.
        
        Raises:
            redis.ConnectionError: If unable to connect to Redis
        """
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                encoding="utf-8",
                max_connections=10,
                retry_on_timeout=True,
                retry_on_error=[redis.ConnectionError, redis.TimeoutError],
            )
            
            self._redis = Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._redis.ping()
            logger.info(f"Successfully connected to Redis at {self.redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {self.redis_url}: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection pool."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
        
        if self._connection_pool:
            await self._connection_pool.aclose()
            self._connection_pool = None
        
        logger.info("Disconnected from Redis")
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis client is connected."""
        return self._redis is not None
    
    async def check_idempotency(
        self, 
        idempotency_key: str, 
        value: str, 
        ttl_seconds: int = 600
    ) -> tuple[bool, Optional[str]]:
        """
        Atomic idempotency check using Redis SET NX EX.
        
        This method atomically checks if an idempotency key exists and sets it
        if it doesn't exist, preventing race conditions in distributed systems.
        
        Args:
            idempotency_key: Unique key for idempotency check
            value: Value to store (typically event_id or operation_id)
            ttl_seconds: TTL for the key in seconds (default: 10 minutes)
        
        Returns:
            tuple: (is_new_operation, existing_value)
                - is_new_operation: True if this is a new operation, False if duplicate
                - existing_value: The existing value if duplicate, None if new
        
        Raises:
            redis.RedisError: If Redis operation fails
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        
        try:
            # Use SET with NX (not exists) and EX (expire) for atomic operation
            # Returns True if key was set (new operation), False if key already exists
            key = f"idempotency:{idempotency_key}"
            was_set = await self._redis.set(key, value, nx=True, ex=ttl_seconds)
            
            if was_set:
                # New operation - key was successfully set
                logger.debug(f"New idempotency key set: {idempotency_key}")
                return True, None
            else:
                # Duplicate operation - key already exists, get existing value
                existing_value = await self._redis.get(key)
                logger.debug(f"Duplicate idempotency key detected: {idempotency_key}")
                return False, existing_value
                
        except redis.RedisError as e:
            logger.error(f"Redis error during idempotency check: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during idempotency check: {e}")
            raise
    
    async def get_idempotency_value(self, idempotency_key: str) -> Optional[str]:
        """
        Get the value associated with an idempotency key.
        
        Args:
            idempotency_key: The idempotency key to look up
        
        Returns:
            The stored value or None if key doesn't exist
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        
        try:
            key = f"idempotency:{idempotency_key}"
            return await self._redis.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis error getting idempotency value: {e}")
            raise
    
    async def delete_idempotency_key(self, idempotency_key: str) -> bool:
        """
        Delete an idempotency key (for testing/cleanup purposes).
        
        Args:
            idempotency_key: The idempotency key to delete
        
        Returns:
            True if key was deleted, False if key didn't exist
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        
        try:
            key = f"idempotency:{idempotency_key}"
            result = await self._redis.delete(key)
            return result > 0
        except redis.RedisError as e:
            logger.error(f"Redis error deleting idempotency key: {e}")
            raise
    
    async def health_check(self) -> dict:
        """
        Perform Redis health check.
        
        Returns:
            dict: Health check results including connectivity and basic stats
        """
        if not self._redis:
            return {"status": "disconnected", "error": "Redis client not connected"}
        
        try:
            # Test basic connectivity
            ping_result = await self._redis.ping()
            
            # Get basic info
            info = await self._redis.info("memory")
            
            return {
                "status": "healthy",
                "ping": ping_result,
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", "unknown"),
            }
        except redis.RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during Redis health check: {e}")
            return {"status": "error", "error": str(e)}

    @asynccontextmanager
    async def get_redis(self):
        """
        Context manager to get Redis client instance.
        
        Yields:
            Redis: The Redis client instance
            
        Raises:
            RuntimeError: If client is not connected
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        
        yield self._redis


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """
    Get the global Redis client instance.
    
    Returns:
        RedisClient: The global Redis client instance
    
    Raises:
        RuntimeError: If Redis client is not initialized
    """
    global _redis_client
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis_client() first.")
    return _redis_client


async def init_redis_client(redis_url: Optional[str] = None) -> RedisClient:
    """
    Initialize the global Redis client.
    
    Args:
        redis_url: Redis connection URL (defaults to REDIS_URL env var)
    
    Returns:
        RedisClient: The initialized Redis client
    """
    global _redis_client
    _redis_client = RedisClient(redis_url)
    await _redis_client.connect()
    return _redis_client


async def close_redis_client() -> None:
    """Close the global Redis client."""
    global _redis_client
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None