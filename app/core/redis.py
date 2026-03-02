"""
Redis Utilities Module

Provides async Redis health check for the application health endpoint.
"""

import logging
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


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
