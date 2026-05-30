import logging
import os
import time
import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client: Redis | None = None
RATE_LIMIT_LUA = "\nlocal key = KEYS[1]\nlocal now = tonumber(ARGV[1])\nlocal window = tonumber(ARGV[2])\nlocal max_requests = tonumber(ARGV[3])\nlocal member = ARGV[4]\n\nredis.call('ZREMRANGEBYSCORE', key, 0, now - window)\nlocal count = redis.call('ZCARD', key)\nif count >= max_requests then\n    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')\n    local reset = window\n    if oldest[2] then\n        reset = math.max(0, oldest[2] + window - now)\n    end\n    return {0, count, reset}\nend\n\nredis.call('ZADD', key, now, member)\nredis.call('EXPIRE', key, window + 5)\nreturn {1, count + 1, window}\n"

async def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

@dataclass
class RateLimitResult:
    success: bool
    count: int
    remaining: int
    reset_seconds: int

class RateLimit:

    def __init__(self, name: str, max_requests: int, window_seconds: int):
        self.name = name
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def limit(self, identifier: str) -> RateLimitResult:
        try:
            redis = await get_redis_client()
            key = f"rate_limit:{self.name}:{identifier}"
            now = int(time.time())
            member = f"{now}-{uuid.uuid4().hex}"
            result = await redis.eval(RATE_LIMIT_LUA, 1, key, now, self.window_seconds, self.max_requests, member)
            success = bool(result[0])
            count = int(result[1])
            reset = int(result[2])
            remaining = max(0, self.max_requests - count) if success else 0
            return RateLimitResult(success=success, count=count, remaining=remaining, reset_seconds=reset)
        except (RedisError, ConnectionError) as exc:
            logging.warning("Redis rate limiter unavailable: %s", exc)
            if self.name in {"login", "register"}:
                return RateLimitResult(success=False, count=0, remaining=0, reset_seconds=self.window_seconds)
            return RateLimitResult(success=True, count=0, remaining=self.max_requests, reset_seconds=self.window_seconds)
api_limits = {"public_booking": RateLimit("public_booking", max_requests=10, window_seconds=3600), "availability": RateLimit("availability", max_requests=10, window_seconds=60), "create_event": RateLimit("create_event", max_requests=100, window_seconds=3600), "webhooks": RateLimit("webhooks", max_requests=100, window_seconds=60), "login": RateLimit("login", max_requests=3, window_seconds=60), "register": RateLimit("register", max_requests=1, window_seconds=3600), "oauth_callback": RateLimit("oauth_callback", max_requests=10, window_seconds=300), "oauth_exchange": RateLimit("oauth_exchange", max_requests=15, window_seconds=300), "password_reset": RateLimit("password_reset", max_requests=3, window_seconds=3600)}

async def rate_limit(identifier: str, limit: RateLimit) -> RateLimitResult:
    if not identifier:
        identifier = "anonymous"
    result = await limit.limit(identifier)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests, please slow down.", headers={"Retry-After": str(result.reset_seconds)})
    return result
