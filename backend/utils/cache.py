import json
import logging
from typing import Any, Optional

from backend.utils.redis_singleton import get_redis
from backend.utils.l1_cache import l1_cache

logger = logging.getLogger(__name__)


async def get_redis_client():
    """Returns a singleton Redis client instance."""
    try:
        return await get_redis()
    except Exception:
        return None

async def set_cache(key: str, value: Any, ttl_seconds: int = 300):
    """Stores a value in Redis with an expiration time."""
    client = await get_redis_client()
    if not client:
        return False
    try:
        # 1. Update L1 (In-Memory)
        l1_cache.set(key, value)
        
        # 2. Update L2 (Redis)
        if not isinstance(value, str):
            value = json.dumps(value)
        await client.setex(key, ttl_seconds, value)
        return True
    except Exception as e:
        logger.warning(f"⚠ Cache set failed for key {key}: {e}")
        return False


async def get_cache(key: str) -> Optional[Any]:
    """Fetches a value from cache, preferring L1 memory over Redis."""

    # 1. Try L1 (Memory)
    val = l1_cache.get(key)
    if val is not None:
        return val

    # 2. Fallback to L2 (Redis)
    client = await get_redis_client()
    if not client:
        return None
    try:
        data = await client.get(key)
        if data:
            try:
                parsed = json.loads(data)
                # Populate L1 for subsequent zero-latency hits
                l1_cache.set(key, parsed)
                return parsed
            except json.JSONDecodeError:
                l1_cache.set(key, data)
                return data
        return None
    except Exception as e:
        logger.warning(f"⚠ Cache get failed for key {key}: {e}")
        return None

async def invalidate_user_calendar_cache(user_id: str):
    """
    Purges all calendar event cache keys for a specific user.
    Uses SCAN to find and delete range-based keys efficiently.
    """
    client = await get_redis_client()
    if not client:
        return False
    try:
        # Invalidate local first
        l1_cache.invalidate(f"calendar:user_{user_id}:")
        
        # Then Redis
        pattern = f"calendar:user_{user_id}:*"
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
        logger.info(f"[CACHE] 🗑 Cache invalidated for user {user_id} (Pattern: {pattern})")
        return True
    except Exception as e:
        logger.warning(f"[CACHE] ⚠ Cache invalidation failed for user {user_id}: {e}")
        return False

async def acquire_lock(lock_name: str, ttl_seconds: int = 600):
    """
    Attempts to acquire an atomic lock in Redis.
    """
    client = await get_redis_client()
    if not client:
        return False
    try:
        return bool(await client.set(f"lock:{lock_name}", "locked", ex=ttl_seconds, nx=True))
    except Exception as e:
        logger.error(f"[CACHE] ❌ Failed to acquire lock {lock_name}: {e}")
        return False

async def release_lock(lock_name: str):
    """Releases a previously held lock."""
    client = await get_redis_client()
    if not client:
        return False
    try:
        await client.delete(f"lock:{lock_name}")
        return True
    except Exception as e:
        logger.warning(f"[CACHE] ⚠ Failed to release lock {lock_name}: {e}")
        return False

def get_calendar_cache_key(user_id: str, start: Any, end: Any):
    """Generates a unique cache key based on user and time range."""
    start_str = start.isoformat() if hasattr(start, 'isoformat') else str(start)
    end_str = end.isoformat() if hasattr(end, 'isoformat') else str(end)
    return f"calendar:user_{user_id}:range:{start_str}_{end_str}"
