
import os
import redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            _client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=10,
            )
            _client.ping()
            logger.info("Redis connected (singleton pool)")
        except Exception as exc:
            logger.warning(
                f"Redis unavailable ({type(exc).__name__}) — falling back to in-process cache"
            )
            _client = None
            raise
    return _client


# ── In-process fallback (single worker only, good enough for Render free tier) ──
_mem: dict[str, str] = {}


def safe_get(key: str) -> Optional[str]:
    try:
        return get_redis().get(key)
    except Exception:
        return _mem.get(key)


def safe_set(key: str, value: str, ex: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
    ttl = ex if ex is not None else ttl_seconds
    try:
        r = get_redis()
        if ttl is not None:
            r.setex(key, ttl, value)
        else:
            r.set(key, value)
    except Exception:
        _mem[key] = value


def safe_delete(*keys: str) -> None:
    try:
        get_redis().delete(*keys)
    except Exception:
        for k in keys:
            _mem.pop(k, None)


def safe_exists(key: str) -> bool:
    try:
        return bool(get_redis().exists(key))
    except Exception:
        return key in _mem
