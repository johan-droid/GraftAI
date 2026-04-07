import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Any

from backend.services.redis_client import get_redis

logger = logging.getLogger(__name__)

@asynccontextmanager
async def acquire_lock(lock_key: str, timeout: int = 60):
    """
    Acquires an atomic distributed Redis lock.
    Perfect for debouncing background workers or calendar syncs.
    
    Usage:
        async with acquire_lock("sync:calendar:123") as locked:
            if not locked:
                logger.warning("Duplicate execution blocked by Redis Lock")
                return 
            # Heavy operation
    """
    redis = await get_redis()
    acquired = False
    
    try:
        # Atomic SET with Not Exists (NX)
        result = await redis.set(lock_key, "locked", ex=timeout, nx=True)
        # Redis client returns True, b"OK", "OK", or None depending on backend
        acquired = bool(result)
        yield acquired
    finally:
        if acquired:
            try:
                await redis.delete(lock_key)
            except Exception as e:
                logger.warning(f"Lock teardown failure for {lock_key}: {e}")
