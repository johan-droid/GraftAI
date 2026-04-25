"""
Redis configuration for caching, sessions, and job queues.
"""

import logging
import os
import time
import json
from typing import Optional, Any
from urllib.parse import urlparse
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Redis connection settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ENV = os.getenv("ENV", "development").lower()
REDIS_FALLBACK_ENABLED = ENV != "production"

# Initialize Redis client
redis_client: Optional[redis.Redis] = None
_fallback_cache: dict[str, tuple[str, float]] = {}


def _redis_connection_advice(redis_url: str) -> str:
    parsed = urlparse(redis_url)
    host = parsed.hostname or ""
    port = parsed.port or 6379
    if host == "redis":
        return (
            f"REDIS_URL={redis_url} uses hostname 'redis', which is only resolvable "
            "inside Docker Compose. If you are running backend code locally, either "
            "start Redis with `docker-compose up redis` or set "
            "REDIS_URL=redis://127.0.0.1:6379/0."
        )

    if host in {"localhost", "127.0.0.1"}:
        return (
            f"REDIS_URL={redis_url} points at local Redis on port {port}. "
            "Please ensure Redis is running and accessible from this process."
        )

    return (
        f"Unable to connect to Redis at {redis_url}. Verify the REDIS_URL environment "
        "variable and that the Redis host is reachable from this machine."
    )


def _cleanup_fallback_cache() -> None:
    now = time.time()
    expired_keys = [key for key, (_, expires_at) in _fallback_cache.items() if expires_at and expires_at <= now]
    for key in expired_keys:
        _fallback_cache.pop(key, None)


def _fallback_store(key: str, value: Any, expire: int = 0) -> None:
    serialized = json.dumps(value) if not isinstance(value, str) else value
    expires_at = time.time() + expire if expire and expire > 0 else 0
    _fallback_cache[key] = (serialized, expires_at)


def _fallback_retrieve(key: str) -> Optional[str]:
    _cleanup_fallback_cache()
    item = _fallback_cache.get(key)
    return item[0] if item else None


def _fallback_delete(key: str) -> None:
    _fallback_cache.pop(key, None)


def _fallback_exists(key: str) -> bool:
    _cleanup_fallback_cache()
    return key in _fallback_cache


async def get_redis() -> Optional[redis.Redis]:
    """Get or create Redis client connection."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            REDIS_URL, encoding="utf-8", decode_responses=True
        )
        try:
            await redis_client.ping()
        except redis.exceptions.ConnectionError as exc:
            redis_client = None
            advice = _redis_connection_advice(REDIS_URL)
            logger.error("Redis connection failed: %s | %s", exc, advice)
            if REDIS_FALLBACK_ENABLED:
                logger.warning("Redis unavailable; falling back to in-memory cache for development.")
                return None
            raise RuntimeError(
                f"Redis connection failed for REDIS_URL={REDIS_URL}. {advice}"
            ) from exc
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


# Cache operations
async def cache_set(key: str, value: Any, expire: int = 3600):
    """Set value in cache with expiration (seconds)."""
    r = await get_redis()
    serialized = json.dumps(value) if not isinstance(value, str) else value
    if r:
        await r.setex(key, expire, serialized)
        return
    _fallback_store(key, serialized, expire)


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = await get_redis()
    if r:
        value = await r.get(key)
    else:
        value = _fallback_retrieve(key)

    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None


async def cache_delete(key: str):
    """Delete key from cache."""
    r = await get_redis()
    if r:
        await r.delete(key)
    else:
        _fallback_delete(key)


async def cache_exists(key: str) -> bool:
    """Check if key exists in cache."""
    r = await get_redis()
    if r:
        return await r.exists(key) > 0
    return _fallback_exists(key)


# Rate limiting
async def check_rate_limit(key: str, limit: int, window: int = 60) -> bool:
    """
    Check if request is within rate limit.

    Args:
        key: Rate limit identifier (e.g., "rate_limit:192.168.1.1")
        limit: Max requests allowed
        window: Time window in seconds

    Returns:
        True if within limit, False if exceeded
    """
    r = await get_redis()
    if r:
        current = await r.get(key)

        if current is None:
            # First request in window
            await r.setex(key, window, 1)
            return True

        count = int(current)
        if count >= limit:
            return False

        # Increment counter
        await r.incr(key)
        return True

    # Fallback local rate limiting is not supported in this helper.
    raise RuntimeError("Rate limiting requires Redis in the current environment.")


# Session storage
async def store_session(session_id: str, data: dict, expire: int = 86400):
    """Store user session data."""
    r = await get_redis()
    if r:
        await r.setex(f"session:{session_id}", expire, json.dumps(data))
        return
    _fallback_store(f"session:{session_id}", json.dumps(data), expire)


async def get_session(session_id: str) -> Optional[dict]:
    """Retrieve user session data."""
    r = await get_redis()
    if r:
        data = await r.get(f"session:{session_id}")
    else:
        data = _fallback_retrieve(f"session:{session_id}")
    return json.loads(data) if data else None


async def delete_session(session_id: str):
    """Delete user session."""
    r = await get_redis()
    if r:
        await r.delete(f"session:{session_id}")
    else:
        _fallback_delete(f"session:{session_id}")


# Pub/Sub for real-time updates
async def publish_message(channel: str, message: dict):
    """Publish message to Redis channel."""
    r = await get_redis()
    if r:
        await r.publish(channel, json.dumps(message))
    else:
        logger.warning("Redis unavailable; publish_message is a no-op in dev fallback.")


# Queue operations for Celery
async def queue_task(queue_name: str, task_data: dict):
    """Add task to Redis queue."""
    r = await get_redis()
    if r:
        await r.lpush(queue_name, json.dumps(task_data))
    else:
        logger.warning("Redis unavailable; queue_task is a no-op in dev fallback.")


async def get_task(queue_name: str, timeout: int = 5) -> Optional[dict]:
    """Get task from Redis queue (blocking)."""
    r = await get_redis()
    if not r:
        return None
    result = await r.brpop(queue_name, timeout=timeout)
    if result:
        _, data = result
        return json.loads(data)
    return None
