import os
import json
import logging
from typing import Optional, Any

from backend.utils.redis_singleton import get_redis

logger = logging.getLogger(__name__)


def get_redis_client():
    """Returns a singleton Redis client instance."""
    try:
        return get_redis()
    except Exception:
        return None

def set_cache(key: str, value: Any, ttl_seconds: int = 300):
    """Stores a value in Redis with an expiration time."""
    client = get_redis_client()
    if not client:
        return False
    try:
        # Pydantic models must be dumped to JSON first outside this call
        # but for simple types we can just use json.dumps here if it's not a string
        if not isinstance(value, str):
            value = json.dumps(value)
        client.setex(key, ttl_seconds, value)
        return True
    except Exception as e:
        logger.warning(f"⚠ Cache set failed for key {key}: {e}")
        return False

def get_cache(key: str):
    """Retrieves a value from Redis."""
    client = get_redis_client()
    if not client:
        return None
    try:
        data = client.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return None
    except Exception as e:
        logger.warning(f"⚠ Cache get failed for key {key}: {e}")
        return None

def invalidate_user_calendar_cache(user_id: str):
    """
    Purges all calendar event cache keys for a specific user.
    Uses SCAN to find and delete range-based keys efficiently.
    """
    client = get_redis_client()
    if not client:
        return False
    try:
        pattern = f"calendar:user_{user_id}:*"
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
        logger.info(f"[CACHE] 🗑 Cache invalidated for user {user_id} (Pattern: {pattern})")
        return True
    except Exception as e:
        logger.warning(f"[CACHE] ⚠ Cache invalidation failed for user {user_id}: {e}")
        return False

def acquire_lock(lock_name: str, ttl_seconds: int = 600):
    """
    Attempts to acquire an atomic lock in Redis.
    Returns True if the lock was acquired, False otherwise.
    """
    client = get_redis_client()
    if not client:
        return False
    try:
        # NX=True ensures the key is only set if it doesn't exist
        # This is an atomic compare-and-set operation
        return bool(client.set(f"lock:{lock_name}", "locked", ex=ttl_seconds, nx=True))
    except Exception as e:
        logger.error(f"[CACHE] ❌ Failed to acquire lock {lock_name}: {e}")
        return False

def release_lock(lock_name: str):
    """Releases a previously held lock."""
    client = get_redis_client()
    if not client:
        return False
    try:
        client.delete(f"lock:{lock_name}")
        return True
    except Exception as e:
        logger.warning(f"[CACHE] ⚠ Failed to release lock {lock_name}: {e}")
        return False

def get_calendar_cache_key(user_id: str, start: Any, end: Any):
    """Generates a unique cache key based on user and time range."""
    # Ensure start/end are stringified consistently
    start_str = start.isoformat() if hasattr(start, 'isoformat') else str(start)
    end_str = end.isoformat() if hasattr(end, 'isoformat') else str(end)
    return f"calendar:user_{user_id}:range:{start_str}_{end_str}"
