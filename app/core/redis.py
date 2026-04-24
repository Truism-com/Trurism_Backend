"""
Redis Utilities Module

Provides async Redis client and health checks for the application.
"""

import logging
from typing import Optional, AsyncGenerator, Dict, Any
import redis.asyncio as aioredis
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> Optional[aioredis.Redis]:
    """Get or initialize global Redis client."""
    global _redis_client
    if _redis_client is None and settings.redis_url and settings.redis_url.lower() != "none":
        try:
            _redis_client = aioredis.from_url(
                settings.redis_url, 
                encoding="utf-8", 
                decode_responses=True,
                max_connections=20,
                socket_connect_timeout=5,  # Azure: add timeout to prevent hanging
                socket_keepalive=True  # Keep connection alive
            )
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            _redis_client = None
    return _redis_client


async def get_redis() -> AsyncGenerator[Optional[aioredis.Redis], None]:
    """FastAPI dependency for Redis client."""
    client = get_redis_client()
    yield client


async def check_redis_health(redis_url: str) -> bool:
    """
    Check Redis connectivity.

    Args:
        redis_url: Redis connection URL

    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        client = aioredis.from_url(redis_url, decode_responses=True)
        await client.ping()
        await client.aclose()
        return True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False

async def get_tenant_cache(tenant_key: str) -> Optional[Dict[str, Any]]:
    """Get cached tenant data."""
    client = get_redis_client()
    if not client:
        return None
    try:
        data = await client.get(f"tenant:{tenant_key}")
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Redis get_tenant_cache error: {e}")
        return None

async def set_tenant_cache(tenant_key: str, tenant_data: Dict[str, Any], ttl: int = 3600):
    """Cache tenant data."""
    client = get_redis_client()
    if not client:
        return
    try:
        await client.setex(f"tenant:{tenant_key}", ttl, json.dumps(tenant_data))
    except Exception as e:
        logger.error(f"Redis set_tenant_cache error: {e}")

async def set_wallet_hold(hold_id: str, hold_data: Dict[str, Any], ttl: int = 1800):
    """Persist wallet hold details."""
    client = get_redis_client()
    if not client:
        return
    try:
        await client.setex(f"hold:{hold_id}", ttl, json.dumps(hold_data))
    except Exception as e:
        logger.error(f"Redis set_wallet_hold error: {e}")

async def get_wallet_hold(hold_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve wallet hold details."""
    client = get_redis_client()
    if not client:
        return None
    try:
        data = await client.get(f"hold:{hold_id}")
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Redis get_wallet_hold error: {e}")
        return None
