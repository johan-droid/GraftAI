import os
import json
import logging
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

# Ensure .env is loaded before any env access
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

_redis = None
_fallback_cache: dict[str, str] = {}


def _get_redis():
    global _redis
    if _redis is not None:
        return _redis

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("⚠ REDIS_URL not set — using in-memory cache fallback")
        return None

    try:
        from redis import Redis as RedisPy
        _redis = RedisPy.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
        _redis.ping()
        return _redis
    except Exception as e:
        logger.warning(f"⚠ Redis connection failed ({type(e).__name__}) — using in-memory cache fallback")
        _redis = None
        return None


def set_cache(key: str, value, expire_seconds: int = 300):
    stored = value
    if not isinstance(value, (str, bytes, int, float, bool)):
        stored = json.dumps(value)

    r = _get_redis()
    if r:
        try:
            if expire_seconds and int(expire_seconds) > 0:
                r.set(key, stored, ex=int(expire_seconds))
            else:
                r.set(key, stored)
            return
        except Exception:
            pass

    # In-memory fallback
    _fallback_cache[key] = stored


def get_cache(key: str):
    r = _get_redis()
    if r:
        try:
            value = r.get(key)
        except Exception:
            value = _fallback_cache.get(key)
    else:
        value = _fallback_cache.get(key)

    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
