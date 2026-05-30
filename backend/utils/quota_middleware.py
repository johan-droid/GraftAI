"""
AI Quota Enforcement Middleware.
Implements a Redis-backed token bucket to prevent LLM cost-exhaustion.
"""
import logging
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.redis import get_redis

logger = logging.getLogger(__name__)
AI_QUOTA_CONFIG = {"/api/v1/bookings": {"capacity": 10, "refill_rate": 0.01, "cost": 1}, "/api/v1/ai/chat": {"capacity": 50, "refill_rate": 0.1, "cost": 1}}

class AIQuotaExceeded(HTTPException):

    def __init__(self, retry_after: int):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"AI quota exceeded. Your tokens refill over time. Please try again in {retry_after} seconds.", headers={"Retry-After": str(retry_after)})

class AIQuotaMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce AI usage quotas per user using a Token Bucket algorithm.
    Stored and synchronized via Redis.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        config = None
        for prefix, cfg in AI_QUOTA_CONFIG.items():
            if path.startswith(prefix):
                config = cfg
                break
        if not config:
            return await call_next(request)
        if request.method not in ("POST", "PATCH"):
            return await call_next(request)
        user_id = await self._get_user_id(request)
        if not user_id:
            return await call_next(request)
        allowed, tokens_left, retry_after = await self._check_quota_redis(user_id, path, config)
        if not allowed:
            logger.warning("🚨 AI Quota exceeded for user %s on %s", user_id, path)
            raise AIQuotaExceeded(retry_after)
        response = await call_next(request)
        response.headers["X-AI-Quota-Remaining"] = str(int(tokens_left))
        return response

    async def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request state or tokens."""
        if hasattr(request.state, "user") and request.state.user:
            return str(request.state.user.id)
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            token = request.cookies.get("graftai_access_token")
        if token:
            try:
                from backend.services.auth_service import decode_jwt_token
                payload = await decode_jwt_token(token)
                return payload.get("sub")
            except Exception:
                pass
        return None

    async def _check_quota_redis(self, user_id: str, path: str, config: dict) -> tuple[bool, float, int]:
        """
        Implements the token bucket algorithm in Redis.
        Returns: (allowed, remaining_tokens, retry_after_seconds)
        """
        try:
            r = await get_redis()
            key = f"ai_quota:{user_id}:{path}"
            capacity = config["capacity"]
            refill_rate = config["refill_rate"]
            cost = config["cost"]
            now = time.time()
            lua_script = "\nlocal bucket = redis.call('HMGET', KEYS[1], 'tokens', 'last_update')\nlocal tokens = tonumber(bucket[1])\nlocal last_update = tonumber(bucket[2])\n\nlocal now = tonumber(ARGV[1])\nlocal refill_rate = tonumber(ARGV[2])\nlocal capacity = tonumber(ARGV[3])\nlocal cost = tonumber(ARGV[4])\n\nif tokens == nil then\n    tokens = capacity\n    last_update = now\nelse\n    local delta = math.max(0, now - last_update)\n    tokens = math.min(capacity, tokens + delta * refill_rate)\n    last_update = now\nend\n\nlocal allowed = false\nif tokens >= cost then\n    tokens = tokens - cost\n    allowed = true\nend\n\nredis.call('HMSET', KEYS[1], 'tokens', tokens, 'last_update', last_update)\nredis.call('EXPIRE', KEYS[1], 86400)\n\nreturn {allowed and 1 or 0, tokens}\n"
            result = await r.eval(lua_script, 1, key, now, refill_rate, capacity, cost)
            allowed = bool(result[0])
            tokens_left = float(result[1])
            retry_after = 0
            if not allowed:
                retry_after = int((cost - tokens_left) / refill_rate) + 1
            return (allowed, tokens_left, retry_after)
        except Exception as e:
            logger.exception("Redis quota check failed: %s", e)
            critical_quota_paths = ["/api/v1/ai/chat", "/api/v1/ai/complete", "/api/v1/ai/generate"]
            is_critical = any(p in path for p in critical_quota_paths)
            if is_critical:
                logger.critical("🚨 Redis DOWN - BLOCKING quota request for security: %s", path)
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Quota system temporarily unavailable. Please try again later.", headers={"Retry-After": "30"})
            logger.warning("Redis down for quota check on non-critical endpoint: %s", path)
            return (True, 0, 0)
