import os
import redis.asyncio as redis
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

_client_decoded: Optional[redis.Redis] = None
_client_binary: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    """Standard Redis client with decode_responses=True (legacy/strings)."""
    global _client_decoded
    if _client_decoded is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            _client_decoded = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20, 
            )
            await _client_decoded.ping()
            logger.info("Redis connected (Decoded Singleton Pool)")
        except Exception as exc:
            logger.warning(f"Decoded Redis unavailable ({type(exc).__name__})")
            raise
    return _client_decoded

async def get_redis_binary() -> redis.Redis:
    """High-performance Redis client with decode_responses=False for MsgPack binary data."""
    global _client_binary
    if _client_binary is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            _client_binary = redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=10,
                retry_on_timeout=True,
                max_connections=50,
            )
            await _client_binary.ping()
            logger.info("Redis connected (Binary Singleton Pool)")
        except Exception as exc:
            logger.error(f"Binary Redis unavailable: {exc}")
            raise
    return _client_binary

# ── In-process fallback ──
_mem: dict[str, Any] = {}

async def safe_get(key: str, binary: bool = False) -> Optional[Any]:
    try:
        r = await get_redis_binary() if binary else await get_redis()
        return await r.get(key)
    except Exception:
        return _mem.get(key)

async def safe_set(key: str, value: Any, ex: Optional[int] = None, ttl_seconds: Optional[int] = None, binary: bool = False) -> None:
    ttl = ex if ex is not None else ttl_seconds
    try:
        r = await get_redis_binary() if binary else await get_redis()
        if ttl is not None:
            await r.setex(key, ttl, value)
        else:
            await r.set(key, value)
    except Exception:
        _mem[key] = value

async def safe_delete(*keys: str) -> None:
    try:
        r = await get_redis_binary()
        await r.delete(*keys)
    except Exception:
        for k in keys:
            _mem.pop(k, None)

async def safe_exists(key: str) -> bool:
    try:
        r = await get_redis_binary()
        return bool(await r.exists(key))
    except Exception:
        return key in _mem
