import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client: Optional[Redis] = None
# Local in-memory fallback used only when Redis is unavailable.
# This is intentionally simple and process-local — used as a last-resort
# fail-closed mechanism for sensitive endpoints (login/register).
_LOCAL_FALLBACK_CACHE_TTL_SECONDS = 3600
_LOCAL_FALLBACK_CACHE_MAX_ENTRIES = 1000
_local_fallback_cache: dict[str, dict[str, Any]] = {}

RATE_LIMIT_LUA = r'''
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
'''


async def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def _prune_local_fallback_cache(now: float) -> None:
    stale_keys = [
        key
        for key, entry in _local_fallback_cache.items()
        if now - entry.get("last_access", 0) > _LOCAL_FALLBACK_CACHE_TTL_SECONDS
    ]
    for key in stale_keys:
        _local_fallback_cache.pop(key, None)

    if len(_local_fallback_cache) > _LOCAL_FALLBACK_CACHE_MAX_ENTRIES:
        oldest = sorted(
            _local_fallback_cache.items(),
            key=lambda item: item[1].get("last_access", 0),
        )
        for key, _ in oldest[: len(_local_fallback_cache) - _LOCAL_FALLBACK_CACHE_MAX_ENTRIES]:
            _local_fallback_cache.pop(key, None)


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
            # Redis unavailable — use a conservative, local fallback.
            # For sensitive endpoints (login/register) fail-closed using
            # a simple in-memory token bucket sliding window. For other
            # endpoints we degrade gracefully (fail-open) to avoid blocking
            # non-critical operations.
            logging.warning(
                "Redis rate limiter unavailable, using local fallback: %s",
                exc,
            )

            # STRICT fallback for sensitive endpoints.
            # When Redis is unavailable, deny requests instead of allowing per-replica local enforcement.
            if self.name in {"login", "register"}:
                return RateLimitResult(
                    success=False,
                    count=0,
                    remaining=0,
                    reset_seconds=self.window_seconds,
                )

            # Non-critical endpoints: fail-open (allow)
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
    "login": RateLimit("login", max_requests=5, window_seconds=300),  # 5 attempts per 5 minutes
    "register": RateLimit("register", max_requests=3, window_seconds=3600),  # 3 registrations per hour
    "oauth_callback": RateLimit("oauth_callback", max_requests=10, window_seconds=300),  # 10 per 5 minutes
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
