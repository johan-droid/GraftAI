import os
import logging
from typing import Any, Optional
from dotenv import load_dotenv
from backend.utils.redis_singleton import get_redis_binary
from backend.utils.serialization import serializer

# Initialize logger
logger = logging.getLogger(__name__)

# Ensure .env is loaded before any env access
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

_redis = None
_fallback_cache: dict[str, bytes] = {}


async def _get_redis():
    global _redis
    if _redis is not None:
        return _redis

    try:
        client = await get_redis_binary()
        _redis = client
        return _redis
    except Exception as exc:
        logger.warning(f"⚠ Binary Redis unavailable — using in-memory cache fallback: {exc}")
        return None


async def set_cache(key: str, value: Any, expire_seconds: int = 300):
    payload = serializer.pack_for_cache(value)

    r = await _get_redis()
    if r:
        try:
            if expire_seconds and int(expire_seconds) > 0:
                await r.setex(key, int(expire_seconds), payload)
            else:
                await r.set(key, payload)
            return
        except Exception:
            pass

    # In-memory fallback
    _fallback_cache[key] = payload


async def get_cache(key: str):
    r = await _get_redis()
    if r:
        try:
            value = await r.get(key)
        except Exception:
            value = _fallback_cache.get(key)
    else:
        value = _fallback_cache.get(key)

    if value is None:
        return None

    if isinstance(value, bytes):
        try:
            return serializer.from_binary(value)
        except Exception:
            try:
                return value.decode("utf-8")
            except Exception:
                return value
    return value
