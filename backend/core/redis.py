"""
Redis configuration for caching, sessions, and job queues.
"""
import os
import json
from typing import Optional, Any
import redis.asyncio as redis

# Redis connection settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Redis client
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client connection."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
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
    await r.setex(key, expire, serialized)


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = await get_redis()
    value = await r.get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None


async def cache_delete(key: str):
    """Delete key from cache."""
    r = await get_redis()
    await r.delete(key)


async def cache_exists(key: str) -> bool:
    """Check if key exists in cache."""
    r = await get_redis()
    return await r.exists(key) > 0


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


# Session storage
async def store_session(session_id: str, data: dict, expire: int = 86400):
    """Store user session data."""
    r = await get_redis()
    await r.setex(f"session:{session_id}", expire, json.dumps(data))


async def get_session(session_id: str) -> Optional[dict]:
    """Retrieve user session data."""
    r = await get_redis()
    data = await r.get(f"session:{session_id}")
    return json.loads(data) if data else None


async def delete_session(session_id: str):
    """Delete user session."""
    r = await get_redis()
    await r.delete(f"session:{session_id}")


# Pub/Sub for real-time updates
async def publish_message(channel: str, message: dict):
    """Publish message to Redis channel."""
    r = await get_redis()
    await r.publish(channel, json.dumps(message))


# Queue operations for Celery
async def queue_task(queue_name: str, task_data: dict):
    """Add task to Redis queue."""
    r = await get_redis()
    await r.lpush(queue_name, json.dumps(task_data))


async def get_task(queue_name: str, timeout: int = 5) -> Optional[dict]:
    """Get task from Redis queue (blocking)."""
    r = await get_redis()
    result = await r.brpop(queue_name, timeout=timeout)
    if result:
        _, data = result
        return json.loads(data)
    return None
