import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client: Optional[Redis] = None
# No process-local in-memory fallback — rely on Redis for distributed
# rate limiting. If Redis is unavailable, behavior is:
# - Sensitive endpoints (login/register): fail-closed (block requests)
# - Non-critical endpoints: fail-open (allow requests)

RATE_LIMIT_LUA = r"""
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count >= max_requests then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local reset = window
    if oldest[2] then
        reset = math.max(0, oldest[2] + window - now)
    end
    return {0, count, reset}
end

redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, window + 5)
return {1, count + 1, window}
"""


async def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


# local fallback removed


@dataclass
class RateLimitResult:
    success: bool
    count: int
    remaining: int
    reset_seconds: int


# local fallback removed


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

            result = await redis.eval(
                RATE_LIMIT_LUA,
                1,
                key,
                now,
                self.window_seconds,
                self.max_requests,
                member,
            )

            success = bool(result[0])
            count = int(result[1])
            reset = int(result[2])
            remaining = max(0, self.max_requests - count) if success else 0

            return RateLimitResult(
                success=success,
                count=count,
                remaining=remaining,
                reset_seconds=reset,
            )
        except (RedisError, ConnectionError) as exc:
            # Redis unavailable — do not use process-local dict fallback.
            # For sensitive endpoints (login/register) we fail-closed
            # to avoid allowing credential brute-force. For others, allow.
            logging.warning("Redis rate limiter unavailable: %s", exc)

            if self.name in {"login", "register"}:
                return RateLimitResult(
                    success=False,
                    count=0,
                    remaining=0,
                    reset_seconds=self.window_seconds,
                )

            return RateLimitResult(
                success=True,
                count=0,
                remaining=self.max_requests,
                reset_seconds=self.window_seconds,
            )


api_limits = {
    "public_booking": RateLimit("public_booking", max_requests=10, window_seconds=3600),
    "availability": RateLimit("availability", max_requests=10, window_seconds=60),
    "create_event": RateLimit("create_event", max_requests=100, window_seconds=3600),
    "webhooks": RateLimit("webhooks", max_requests=100, window_seconds=60),
    "login": RateLimit(
        "login", max_requests=5, window_seconds=300
    ),  # 5 attempts per 5 minutes
    "register": RateLimit(
        "register", max_requests=3, window_seconds=3600
    ),  # 3 registrations per hour
    "oauth_callback": RateLimit(
        "oauth_callback", max_requests=10, window_seconds=300
    ),  # 10 per 5 minutes
}


async def rate_limit(identifier: str, limit: RateLimit) -> RateLimitResult:
    if not identifier:
        identifier = "anonymous"
    result = await limit.limit(identifier)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please slow down.",
            headers={"Retry-After": str(result.reset_seconds)},
        )
    return result
