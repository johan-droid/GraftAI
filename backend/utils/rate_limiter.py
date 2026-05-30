"""
Rate limiting implementation for GraftAI backend.
Uses Redis for distributed rate limiting across multiple workers.
"""
import logging
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"

class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""

    def __init__(self, retry_after: int):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Rate limit exceeded. Retry after {retry_after} seconds.", headers={"Retry-After": str(retry_after)})

class RateLimiter:
    """
    Distributed rate limiter using Redis.
    Supports multiple rate limiting strategies.
    """

    def __init__(self, redis_client: redis.Redis | None=None, default_limit: int=100, default_window: int=60, strategy: RateLimitStrategy=RateLimitStrategy.SLIDING_WINDOW):
        self.redis = redis_client
        self.default_limit = default_limit
        self.default_window = default_window
        self.strategy = strategy
        self._memory_store: dict[str, dict] = {}
        # In-memory cache mapping API key -> tier (populated lazily from DB)
        self.api_key_tiers: dict[str, str] = {}
        # Prefix index: prefix -> list of (key_hash, tier) to speed verification
        self.api_key_prefix_index: dict[str, list[tuple[str, str]]] = {}
        # Pluggable hash function for API keys. Default: sha256 hex digest.
        import hashlib
        self.api_key_hash_func = lambda key: hashlib.sha256(key.encode("utf-8")).hexdigest()
        # Common endpoint-specific rate limits. Added both /api/v1/ and /ai/ prefixes
        self.endpoint_limits: dict[str, dict] = {
            "/api/v1/auth/login": {"limit": 5, "window": 60},
            "/api/v1/auth/register": {"limit": 3, "window": 300},
            "/api/v1/auth/forgot-password": {"limit": 3, "window": 3600},
            "/api/v1/auth/reset-password": {"limit": 3, "window": 3600},
            "/api/v1/auth/verify-email": {"limit": 5, "window": 3600},
            "/api/v1/api-keys": {"limit": 10, "window": 60},
            "/api/v1/ai/chat": {"limit": 60, "window": 60},
            "/api/v1/ai/conversations": {"limit": 100, "window": 60},
            "/api/v1/bookings": {"limit": 100, "window": 60},
            "/api/v1/events": {"limit": 100, "window": 60},
            "/api/v1/users": {"limit": 50, "window": 60},
            # Support legacy /ai prefix used by some routes
            "/ai/chat": {"limit": 60, "window": 60},
            "/ai/conversations": {"limit": 100, "window": 60},
        }

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client."""
        # Determine API key (if provided) and map to client identifier
        api_key = request.headers.get("X-API-Key")
        tier = self._get_tier(request)
        if api_key:
            # include tier in identifier so different tiers are rate-limited separately
            return f"tier:{tier}:apikey:{api_key}"
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "id", getattr(request.state.user, "user_id", None))
            return f"tier:{tier}:user:{user_id}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        return f"tier:{tier}:ip:{client_ip}"

    def _get_tier(self, request: Request) -> str:
        """Resolve user tier from request state or API key mapping.

        Resolution order:
        - If `X-API-Key` header present and `self.api_key_tiers` mapping set, use that.
        - If `request.state.user.tier` present, use that.
        - Otherwise return 'free' as a conservative default.
        """
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Fast in-memory cache hit
            tier = self.api_key_tiers.get(api_key)
            if tier:
                return tier
        if hasattr(request.state, "user") and request.state.user:
            tier = getattr(request.state.user, "tier", None)
            if tier:
                return tier
        return "free"

    async def resolve_api_key_tier(self, api_key: str, db_session=None) -> str | None:
        """Async lookup to resolve an API key's owner tier from the database.

        Stores the discovered tier in `self.api_key_tiers` cache and returns it.
        This intentionally uses a simple key-prefix matching strategy so it is
        tolerant of stored hashed keys or prefixed keys. If DB lookup fails
        it returns None and leaves the cache unchanged.
        """
        if not api_key:
            return None
        if api_key in self.api_key_tiers:
            return self.api_key_tiers[api_key]
        try:
            # Lazy import to avoid hard dependency at module import time
            from backend.utils.db import get_db_context
            from sqlalchemy import text
        except Exception:
            return None
        # Use prefix heuristic: migration has a `key_prefix` column (index),
        # so match on the first 20 chars of the provided key.
        prefix = api_key[:20]
        async def _query(session):
            sql = text("SELECT u.tier FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.key_prefix = :prefix AND ak.is_active = true LIMIT 1")
            res = await session.execute(sql.bindparams(prefix=prefix))
            row = res.first()
            return row[0] if row else None
        try:
            # Fast path: if we have prefix-indexed hashes in memory, compare locally
            prefix = api_key[:20]
            api_hash = self.api_key_hash_func(api_key)
            candidates = self.api_key_prefix_index.get(prefix)
            if candidates:
                for key_hash, tier in candidates:
                    if key_hash == api_hash:
                        self.api_key_tiers[api_key] = tier
                        return tier
            # Fallback to DB lookup: fetch rows matching prefix and verify hash
            if db_session is None:
                async with get_db_context() as sess:
                    rows = await sess.execute(text("SELECT ak.key_hash, u.tier FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.key_prefix = :prefix AND ak.is_active = true" ).bindparams(prefix=prefix))
                    results = rows.all()
            else:
                rows = await db_session.execute(text("SELECT ak.key_hash, u.tier FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.key_prefix = :prefix AND ak.is_active = true" ).bindparams(prefix=prefix))
                results = rows.all()
            for row in results:
                stored_hash = row[0]
                tier = row[1]
                # populate prefix index
                self.api_key_prefix_index.setdefault(prefix, []).append((stored_hash, tier))
                if stored_hash == api_hash:
                    self.api_key_tiers[api_key] = tier
                    return tier
        except Exception:
            logger.exception("Failed to resolve API key tier from DB")
        return None

    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate Redis key for rate limiting."""
        client_id = self._get_client_identifier(request)
        endpoint = request.url.path
        return f"rate_limit:{endpoint}:{client_id}"

    def _get_endpoint_limit(self, path: str, tier: str | None = None) -> tuple[int, int]:
        """Get rate limit for specific endpoint."""
        # Normalize tier
        tier = tier or "free"
        # First check explicit endpoint mapping
        if path in self.endpoint_limits:
            config = self.endpoint_limits[path]
            return (config["limit"], config["window"]) 
        # Streaming/proxy endpoints deserve stricter, tiered limits
        lowered = path.lower()
        is_ai_stream = ("/ai/stream" in lowered) or lowered.endswith("/stream") or ("/stream" in lowered and "/ai" in lowered)
        is_llm_proxy = ("/ai/" in lowered or "/llm" in lowered or "/proxy" in lowered) and ("/ai/" in lowered or "/llm" in lowered)
        if is_ai_stream:
            # Tiered streaming limits (conservative defaults)
            streaming_limits = {
                "free": (5, 60),
                "pro": (20, 60),
                "enterprise": (200, 60),
            }
            return streaming_limits.get(tier, streaming_limits["free"])
        if is_llm_proxy and ("/ai/" in lowered or "/llm" in lowered):
            # Slightly tightened limits for endpoints that proxy to costly LLM calls
            proxy_limits = {
                "free": (30, 60),
                "pro": (120, 60),
                "enterprise": (1000, 60),
            }
            return proxy_limits.get(tier, (self.default_limit, self.default_window))
        # Fallback: check prefixes in endpoint_limits
        for prefix, config in self.endpoint_limits.items():
            if path.startswith(prefix):
                return (config["limit"], config["window"]) 
        return (self.default_limit, self.default_window)

    async def is_allowed(self, request: Request) -> tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.
        Returns: (allowed, remaining, retry_after)
        """
        # Attempt to eagerly resolve API key -> tier mapping from DB if missing
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key not in self.api_key_tiers:
            try:
                await self.resolve_api_key_tier(api_key)
            except Exception:
                logger.debug("Non-fatal: failed to eagerly resolve api key tier")
        key = self._get_rate_limit_key(request)
        tier = self._get_tier(request)
        limit, window = self._get_endpoint_limit(request.url.path, tier=tier)
        now = int(time.time())
        if not self.redis:
            logger.warning("Redis client not configured; falling back to in-memory rate limiting.")
            return await self._in_memory_check(key, limit, window, now)
        try:
            if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._sliding_window_check(key, limit, window, now)
            if self.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await self._fixed_window_check(key, limit, window, now)
            return await self._token_bucket_check(key, limit, window, now)
        except redis.RedisError:
            logger.warning("Redis error during rate check; falling back to in-memory rate limiting.")
            return await self._in_memory_check(key, limit, window, now)

    async def _in_memory_check(self, key: str, limit: int, window: int, now: int) -> tuple[bool, int, int]:
        """In-memory fallback for rate limiting."""
        if len(self._memory_store) >= 100 or now % 60 == 0:
            self._cleanup_memory_store(now)
        if self.strategy == RateLimitStrategy.FIXED_WINDOW:
            window_id = now // window
            mem_key = f"{key}:{window_id}"
            if mem_key not in self._memory_store:
                self._memory_store[mem_key] = {"count": 0, "expires": now + window}
            data = self._memory_store[mem_key]
            data["count"] += 1
            if data["count"] > limit:
                retry_after = window - now % window
                return (False, 0, retry_after)
            return (True, limit - data["count"], 0)
        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            if key not in self._memory_store:
                self._memory_store[key] = {"hits": [], "expires": now + window}
            data = self._memory_store[key]
            window_start = now - window
            data["hits"] = [h for h in data["hits"] if h > window_start]
            if len(data["hits"]) >= limit:
                retry_after = int(data["hits"][0] + window - now)
                return (False, 0, max(1, retry_after))
            data["hits"].append(now)
            data["expires"] = now + window
            return (True, limit - len(data["hits"]), 0)
        bucket_key = f"{key}:bucket"
        if bucket_key not in self._memory_store:
            self._memory_store[bucket_key] = {"tokens": float(limit), "last_update": now, "expires": now + window * 2}
        data = self._memory_store[bucket_key]
        time_passed = now - data["last_update"]
        rate = limit / window
        data["tokens"] = min(limit, data["tokens"] + time_passed * rate)
        data["last_update"] = now
        data["expires"] = now + window * 2
        if data["tokens"] < 1:
            retry_after = int((1 - data["tokens"]) / rate) + 1
            return (False, 0, retry_after)
        data["tokens"] -= 1
        return (True, int(data["tokens"]), 0)

    def _cleanup_memory_store(self, now: int):
        """Remove expired entries from memory store."""
        expired_keys = []
        for k, v in self._memory_store.items():
            expiry = v.get("expires") or v.get("expiration") or 0
            if expiry < now:
                expired_keys.append(k)
        for k in expired_keys:
            del self._memory_store[k]
        if expired_keys:
            logger.debug("Cleaned up %s expired entries from memory store", len(expired_keys))

    async def _sliding_window_check(self, key: str, limit: int, window: int, now: int) -> tuple[bool, int, int]:
        """Sliding window rate limiting using Redis sorted sets."""
        pipe = self.redis.pipeline()
        window_start = now - window
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window + 1)
        results = await pipe.execute()
        current_count = results[1]
        if current_count >= limit:
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            retry_after = int(oldest[0][1] + window - now) if oldest else window
            return (False, 0, max(1, retry_after))
        remaining = limit - current_count - 1
        return (True, remaining, 0)

    async def _fixed_window_check(self, key: str, limit: int, window: int, now: int) -> tuple[bool, int, int]:
        """Fixed window rate limiting using Redis counters."""
        window_key = f"{key}:{now // window}"
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window)
        results = await pipe.execute()
        current_count = results[0]
        if current_count > limit:
            retry_after = window - now % window
            return (False, 0, retry_after)
        remaining = limit - current_count
        return (True, remaining, 0)

    async def _token_bucket_check(self, key: str, limit: int, window: int, now: int) -> tuple[bool, int, int]:
        """Token bucket rate limiting."""
        bucket_key = f"{key}:bucket"
        last_update_key = f"{key}:last_update"
        pipe = self.redis.pipeline()
        pipe.get(bucket_key)
        pipe.get(last_update_key)
        results = await pipe.execute()
        tokens = float(results[0]) if results[0] else limit
        last_update = int(results[1]) if results[1] else now
        time_passed = now - last_update
        rate = limit / window
        new_tokens = min(limit, tokens + time_passed * rate)
        if new_tokens < 1:
            retry_after = int((1 - new_tokens) / rate) + 1
            return (False, 0, retry_after)
        new_tokens -= 1
        pipe = self.redis.pipeline()
        pipe.set(bucket_key, str(new_tokens))
        pipe.set(last_update_key, str(now))
        pipe.expire(bucket_key, window * 2)
        pipe.expire(last_update_key, window * 2)
        await pipe.execute()
        return (True, int(new_tokens), 0)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    Automatically applies rate limits to all incoming requests.
    """

    def __init__(self, app, redis_url: str | None=None, default_limit: int=100, default_window: int=60, strategy: str="sliding_window", skip_paths: list | None=None):
        super().__init__(app)
        redis_client = None
        if redis_url:
            try:
                redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                import logging
                logging.warning(f"Failed to connect to Redis: {e}")
        # Use global RateLimiter instance when possible so startup population
        # and other helpers operate on the same in-memory cache.
        # Use global RateLimiter instance so startup cache population
        # operates on the same in-memory cache.
        self.limiter = get_rate_limiter(redis_url=redis_url, default_limit=default_limit, default_window=default_window, strategy=RateLimitStrategy(strategy))
        if redis_client:
            self.limiter.redis = redis_client
        self.skip_paths = set(skip_paths or ["/health", "/", "/docs", "/redoc", "/openapi.json"])

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in self.skip_paths:
            return await call_next(request)
        allowed, remaining, retry_after = await self.limiter.is_allowed(request)
        if not allowed:
            raise RateLimitExceeded(retry_after)
        response = await call_next(request)
        # Set headers with per-endpoint limit when available (include tier info)
        tier = self.limiter._get_tier(request)
        limit, window = self.limiter._get_endpoint_limit(request.url.path, tier=tier)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Window"] = str(window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

def rate_limit(limit: int=100, window: int=60, key_func: Callable | None=None):
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
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                for _key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            if request:
                app = request.app
                if not hasattr(app.state, "rate_limiter"):
                    import os
                    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                    app.state.rate_limiter = RateLimiter()
                    try:
                        app.state.rate_limiter.redis = redis.from_url(redis_url, decode_responses=True)
                    except Exception:
                        app.state.rate_limiter.redis = None
                limiter = app.state.rate_limiter
                limiter.default_limit = limit
                limiter.default_window = window
                allowed, _remaining, retry_after = await limiter.is_allowed(request)
                if not allowed:
                    raise RateLimitExceeded(retry_after)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
_rate_limiter_instance: RateLimiter | None = None

def get_rate_limiter(redis_url: str | None=None, default_limit: int=100, default_window: int=60, strategy: RateLimitStrategy=RateLimitStrategy.SLIDING_WINDOW) -> RateLimiter:
    """Get or create a global RateLimiter instance."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        redis_client = None
        if redis_url:
            import redis.asyncio as redis
            try:
                redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception:
                redis_client = None
        _rate_limiter_instance = RateLimiter(redis_client=redis_client, default_limit=default_limit, default_window=default_window, strategy=strategy)
    return _rate_limiter_instance

def reset_rate_limiter():
    """Reset the global rate limiter instance (primarily for testing)."""
    global _rate_limiter_instance
    _rate_limiter_instance = None
