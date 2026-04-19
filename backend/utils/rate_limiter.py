"""
Rate limiting implementation for GraftAI backend.
Uses Redis for distributed rate limiting across multiple workers.
"""

import time
from typing import Optional, Callable, Dict
from functools import wraps
from enum import Enum

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""

    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """
    Distributed rate limiter using Redis.
    Supports multiple rate limiting strategies.
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        default_limit: int = 100,
        default_window: int = 60,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    ):
        self.redis = redis_client
        self.default_limit = default_limit
        self.default_window = default_window
        self.strategy = strategy

        # In-memory fallback
        self._memory_store: Dict[str, Dict[str, float]] = {}

        # Rate limit configurations per endpoint
        self.endpoint_limits: Dict[str, Dict] = {
            # Strict limits for auth endpoints
            "/api/v1/auth/login": {"limit": 5, "window": 60},
            "/api/v1/auth/register": {"limit": 3, "window": 300},
            "/api/v1/auth/forgot-password": {"limit": 3, "window": 3600},
            "/api/v1/auth/reset-password": {"limit": 3, "window": 3600},
            "/api/v1/auth/verify-email": {"limit": 5, "window": 3600},
            # API key endpoints
            "/api/v1/api-keys": {"limit": 10, "window": 60},
            # AI endpoints (higher limits for chat)
            "/api/v1/ai/chat": {"limit": 60, "window": 60},  # 1 per second
            "/api/v1/ai/conversations": {"limit": 100, "window": 60},
            # Standard API endpoints
            "/api/v1/bookings": {"limit": 100, "window": 60},
            "/api/v1/events": {"limit": 100, "window": 60},
            "/api/v1/users": {"limit": 50, "window": 60},
        }

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client."""
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key}"

        # Check for authenticated user
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate Redis key for rate limiting."""
        client_id = self._get_client_identifier(request)
        endpoint = request.url.path
        return f"rate_limit:{endpoint}:{client_id}"

    def _get_endpoint_limit(self, path: str) -> tuple[int, int]:
        """Get rate limit for specific endpoint."""
        # Check exact match
        if path in self.endpoint_limits:
            config = self.endpoint_limits[path]
            return config["limit"], config["window"]

        # Check prefix matches
        for prefix, config in self.endpoint_limits.items():
            if path.startswith(prefix):
                return config["limit"], config["window"]

        # Return defaults
        return self.default_limit, self.default_window

    async def is_allowed(self, request: Request) -> tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.
        Returns: (allowed, remaining, retry_after)
        """
        key = self._get_rate_limit_key(request)
        limit, window = self._get_endpoint_limit(request.url.path)
        now = int(time.time())

        # Clean memory store periodically (approximate)
        if hasattr(self, '_memory_store') and len(self._memory_store) > 10000:
            current_time = time.time()
            keys_to_delete = []
            for k, data in self._memory_store.items():
                if data.get("expiration", current_time) <= current_time:
                    keys_to_delete.append(k)
            for k in keys_to_delete:
                del self._memory_store[k]

        if not self.redis:
            # In-memory fallback (fixed window)
            return self._memory_fixed_window_check(key, limit, window, now)

        try:
            if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._sliding_window_check(key, limit, window, now)
            elif self.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await self._fixed_window_check(key, limit, window, now)
            else:  # TOKEN_BUCKET
                return await self._token_bucket_check(key, limit, window, now)
        except redis.RedisError:
            # Fallback to in-memory on redis failure
            return self._memory_fixed_window_check(key, limit, window, now)

    def _memory_fixed_window_check(
        self, key: str, limit: int, window: int, now: int
    ) -> tuple[bool, int, int]:
        """In-memory fixed window fallback."""
        if not hasattr(self, '_memory_store'):
            self._memory_store = {}
            
        window_key = f"{key}:{now // window}"
        
        entry = self._memory_store.get(window_key)
        if entry is None or entry.get("expiration", 0) <= now:
            entry = {"count": 0, "expiration": now + window}
            
        entry["count"] += 1
        self._memory_store[window_key] = entry
        
        current_count = entry["count"]
        if current_count > limit:
            retry_after = window - (now % window)
            return False, 0, retry_after

        remaining = limit - current_count
        return True, remaining, 0

    async def _sliding_window_check(
        self, key: str, limit: int, window: int, now: int
    ) -> tuple[bool, int, int]:

        """Sliding window rate limiting using Redis sorted sets."""
        pipe = self.redis.pipeline()

        # Remove requests outside the window
        window_start = now - window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiration
        pipe.expire(key, window + 1)

        results = await pipe.execute()
        current_count = results[1]

        # Check if limit exceeded
        if current_count >= limit:
            # Get oldest request time for retry calculation
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window - now)
            else:
                retry_after = window
            return False, 0, max(1, retry_after)

        remaining = limit - current_count - 1
        return True, remaining, 0

    async def _fixed_window_check(
        self, key: str, limit: int, window: int, now: int
    ) -> tuple[bool, int, int]:
        """Fixed window rate limiting using Redis counters."""
        window_key = f"{key}:{now // window}"

        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window)

        results = await pipe.execute()
        current_count = results[0]

        if current_count > limit:
            retry_after = window - (now % window)
            return False, 0, retry_after

        remaining = limit - current_count
        return True, remaining, 0

    async def _token_bucket_check(
        self, key: str, limit: int, window: int, now: int
    ) -> tuple[bool, int, int]:
        """Token bucket rate limiting."""
        bucket_key = f"{key}:bucket"
        last_update_key = f"{key}:last_update"

        # Get current state
        pipe = self.redis.pipeline()
        pipe.get(bucket_key)
        pipe.get(last_update_key)

        results = await pipe.execute()
        tokens = float(results[0]) if results[0] else limit
        last_update = int(results[1]) if results[1] else now

        # Calculate tokens to add
        time_passed = now - last_update
        rate = limit / window
        new_tokens = min(limit, tokens + time_passed * rate)

        if new_tokens < 1:
            retry_after = int((1 - new_tokens) / rate) + 1
            return False, 0, retry_after

        # Consume token
        new_tokens -= 1

        # Update state
        pipe = self.redis.pipeline()
        pipe.set(bucket_key, str(new_tokens))
        pipe.set(last_update_key, str(now))
        pipe.expire(bucket_key, window * 2)
        pipe.expire(last_update_key, window * 2)
        await pipe.execute()

        return True, int(new_tokens), 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    Automatically applies rate limits to all incoming requests.
    """

    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        default_limit: int = 100,
        default_window: int = 60,
        strategy: str = "sliding_window",
        skip_paths: Optional[list] = None,
    ):
        super().__init__(app)

        # Initialize Redis client
        redis_client = None
        if redis_url:
            try:
                redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                import logging

                logging.warning(f"Failed to connect to Redis: {e}")

        self.limiter = RateLimiter(
            redis_client=redis_client,
            default_limit=default_limit,
            default_window=default_window,
            strategy=RateLimitStrategy(strategy),
        )

        # Paths to skip (health checks, etc.)
        self.skip_paths = set(
            skip_paths or ["/health", "/", "/docs", "/redoc", "/openapi.json"]
        )

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for certain paths
        if request.url.path in self.skip_paths:
            response = await call_next(request)
            return response

        # Check rate limit
        allowed, remaining, retry_after = await self.limiter.is_allowed(request)

        if not allowed:
            raise RateLimitExceeded(retry_after)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limiter.default_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


def rate_limit(limit: int = 100, window: int = 60, key_func: Optional[Callable] = None):
    """
    Decorator for endpoint-specific rate limiting.

    Usage:
        @app.post("/api/login")
        @rate_limit(limit=5, window=60)
        async def login(request: Request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break

            if request:
                # Get or create rate limiter
                app = request.app

                if not hasattr(app.state, "rate_limiter"):
                    # Initialize rate limiter
                    import os

                    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                    app.state.rate_limiter = RateLimiter()
                    try:
                        app.state.rate_limiter.redis = redis.from_url(
                            redis_url, decode_responses=True
                        )
                    except Exception:
                        app.state.rate_limiter.redis = None

                limiter = app.state.rate_limiter
                limiter.default_limit = limit
                limiter.default_window = window

                allowed, remaining, retry_after = await limiter.is_allowed(request)

                if not allowed:
                    raise RateLimitExceeded(retry_after)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Global rate limiter instance
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter(
    redis_url: Optional[str] = None, default_limit: int = 100, default_window: int = 60
) -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter_instance

    if _rate_limiter_instance is None:
        redis_client = None
        if redis_url:
            try:
                redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception:
                pass

        _rate_limiter_instance = RateLimiter(
            redis_client=redis_client,
            default_limit=default_limit,
            default_window=default_window,
        )

    return _rate_limiter_instance
