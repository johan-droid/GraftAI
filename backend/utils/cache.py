"""Compatibility cache helpers for modules importing `backend.utils.cache`.

This module provides lightweight async `get_cache`/`set_cache`, lock helpers
and a `get_redis_client` shim. It delegates to `backend.services.cache` or
`backend.services.redis_client` when available, and otherwise falls back to
in-memory implementations suitable for local development.
"""
from __future__ import annotations

import asyncio
import fnmatch
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)
try:
    from backend.utils.serialization import serializer
except Exception:
    import json

    class _SimpleSerializer:

        @staticmethod
        def pack_for_cache(obj: Any) -> bytes:
            return json.dumps(obj, default=str).encode("utf-8")

        @staticmethod
        def from_binary(b: bytes) -> Any:
            try:
                return json.loads(b.decode("utf-8"))
            except Exception:
                return b
    serializer = _SimpleSerializer()
_fallback_cache: dict[str, tuple[bytes, float | None]] = {}
_locks_map: dict[str, float] = {}
_locks_map_guard = asyncio.Lock()

async def set_cache(key: str, value: Any, expire_seconds: int=300) -> None:
    """Set a value in cache. Delegates to services.cache if available."""
    try:
        import importlib
        svc = importlib.import_module("backend.services.cache")
        if hasattr(svc, "set_cache"):
            return await svc.set_cache(key, value, expire_seconds)
    except Exception:
        pass
    payload = serializer.pack_for_cache(value)
    expire_at = time.time() + int(expire_seconds) if expire_seconds and int(expire_seconds) > 0 else None
    _fallback_cache[key] = (payload, expire_at)
    return None

async def get_cache(key: str) -> Any | None:
    """Get a value from cache. Delegates to services.cache if available."""
    try:
        import importlib
        svc = importlib.import_module("backend.services.cache")
        if hasattr(svc, "get_cache"):
            return await svc.get_cache(key)
    except Exception:
        pass
    entry = _fallback_cache.get(key)
    if not entry:
        return None
    payload, expire_at = entry
    if expire_at and time.time() > expire_at:
        _fallback_cache.pop(key, None)
        return None
    try:
        return serializer.from_binary(payload)
    except Exception:
        try:
            return payload.decode("utf-8")
        except Exception:
            return payload

async def invalidate_user_calendar_cache(user_id: str) -> None:
    """Invalidate calendar-related cache keys for a user."""
    try:
        import importlib
        svc = importlib.import_module("backend.services.cache")
        if hasattr(svc, "invalidate_user_calendar_cache"):
            return await svc.invalidate_user_calendar_cache(user_id)
    except Exception:
        pass
    patterns = [f"calendar:events:{user_id}", f"calendar:list:{user_id}", f"calendar:summary:{user_id}"]
    for k in patterns:
        _fallback_cache.pop(k, None)
    return None

async def acquire_lock(key: str, ttl_seconds: int=60) -> bool:
    """Attempt to acquire a short-lived lock. Returns True if acquired."""
    try:
        import importlib
        svc = importlib.import_module("backend.services.cache")
        if hasattr(svc, "acquire_lock"):
            return await svc.acquire_lock(key, ttl_seconds)
    except Exception:
        pass
    now = time.time()
    async with _locks_map_guard:
        exp = _locks_map.get(key)
        if exp and exp > now:
            return False
        _locks_map[key] = now + float(ttl_seconds)
        return True

async def delete_cache(key: str) -> None:
    """Delete a cache key if it exists."""
    try:
        import importlib
        svc = importlib.import_module("backend.services.cache")
        if hasattr(svc, "delete_cache"):
            return await svc.delete_cache(key)
    except Exception:
        pass
    _fallback_cache.pop(key, None)
    return None

async def delete_cache_pattern(pattern: str) -> None:
    """Delete cache keys matching a pattern."""
    try:
        import importlib
        svc = importlib.import_module("backend.services.cache")
        if hasattr(svc, "delete_cache_pattern"):
            return await svc.delete_cache_pattern(pattern)
    except Exception:
        pass
    keys_to_delete = [k for k in list(_fallback_cache.keys()) if fnmatch.fnmatch(k, pattern)]
    for k in keys_to_delete:
        _fallback_cache.pop(k, None)
    return None

async def invalidate_user_cache_pattern(user_id: str, prefix: str) -> None:
    """Invalidate cache keys for a user with a given prefix."""
    pattern = f"{prefix}:{user_id}:*"
    try:
        import importlib
        svc = importlib.import_module("backend.services.cache")
        if hasattr(svc, "delete_cache_pattern"):
            return await svc.delete_cache_pattern(pattern)
    except Exception:
        pass
    keys_to_delete = [k for k in list(_fallback_cache.keys()) if fnmatch.fnmatch(k, pattern)]
    for k in keys_to_delete:
        _fallback_cache.pop(k, None)
    return None

async def get_or_renew(key: str, ttl: int, fetch_func, stale_ttl: int | None = None, lock_timeout: int = 10, retry_delay: float = 0.05, max_retries: int = 5):
    """
    Cache-aside with stampede protection.

    Attempts fast-path cache read. On miss, uses `cache_set_if_not_exists` (SETNX)
    to acquire a regeneration lock. Only the lock holder calls `fetch_func` to
    recompute the value. Other callers wait and retry, or return stale data if
    `stale_ttl` is provided.

    Args:
        key: Cache key.
        ttl: TTL for fresh cache entry.
        fetch_func: Async callable that returns the value to cache.
        stale_ttl: If set, allow returning stale data while regeneration is in progress.
        lock_timeout: Seconds before the regeneration lock auto-releases.
        retry_delay: Seconds to wait between retries.
        max_retries: Maximum number of retries before falling through to fetch_func.

    Returns:
        The cached or freshly-computed value.
    """
    cached = await cache_get(key)
    if cached is not None:
        return cached

    # Attempt to acquire regeneration lock via SETNX
    lock_key = f"renew_lock:{key}"
    if await cache_set_if_not_exists(lock_key, "1", expire=lock_timeout):
        try:
            value = await fetch_func()
            await cache_set(key, value, expire=ttl)
            return value
        except Exception:
            raise
        finally:
            await cache_delete(lock_key)

    # Lock held by another worker — retry with optional stale fallback
    for attempt in range(max_retries):
        await asyncio.sleep(retry_delay * (attempt + 1))
        cached = await cache_get(key)
        if cached is not None:
            return cached
        if stale_ttl and attempt == max_retries - 1:
            stale = _fallback_retrieve(key)
            if stale is not None:
                try:
                    return json.loads(stale)
                except json.JSONDecodeError:
                    return stale

    # Timeout — call fetch_func directly (degraded but safe)
    value = await fetch_func()
    await cache_set(key, value, expire=ttl)
    return value


async def get_redis_client():
    """Attempt to return an async redis client from available helpers, else None."""
    try:
        import importlib
        svc = importlib.import_module("backend.services.redis_client")
        if hasattr(svc, "get_redis_client"):
            return await svc.get_redis_client()
    except Exception:
        pass
    try:
        import importlib
        svc = importlib.import_module("backend.utils.redis_singleton")
        if hasattr(svc, "get_redis_binary"):
            return await svc.get_redis_binary()
    except Exception:
        pass
    return None
