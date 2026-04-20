"""
AI Quota Enforcement Middleware.
Implements a Redis-backed token bucket to prevent LLM cost-exhaustion.
"""

import time
import logging
from typing import Optional, Callable

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.redis import get_redis

logger = logging.getLogger(__name__)

# AI Quota Configurations
AI_QUOTA_CONFIG = {
    "/api/v1/bookings": {
        "capacity": 10,       # Max burst tokens
        "refill_rate": 0.01, # Tokens per second (0.01 = 1 token per 100 seconds = ~144/day)
        "cost": 1            # Tokens per request
    },
    "/api/v1/ai/chat": {
        "capacity": 50,
        "refill_rate": 0.1,  # 1 token per 10 seconds
        "cost": 1
    }
}

class AIQuotaExceeded(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"AI quota exceeded. Your tokens refill over time. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

class AIQuotaMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce AI usage quotas per user using a Token Bucket algorithm.
    Stored and synchronized via Redis.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        
        # Check if the path is an AI-heavy route
        config = None
        for prefix, cfg in AI_QUOTA_CONFIG.items():
            if path.startswith(prefix):
                config = cfg
                break
        
        if not config:
            return await call_next(request)

        # Skip quota check for non-POST/PUT/PATCH methods if needed
        if request.method not in ("POST", "PATCH"):
            return await call_next(request)

        # Identify the user
        user_id = await self._get_user_id(request)
        if not user_id:
            return await call_next(request)

        # Token Bucket Logic via Lua Script for Atomicity
        allowed, tokens_left, retry_after = await self._check_quota_redis(
            user_id, path, config
        )

        if not allowed:
            logger.warning(f"🚨 AI Quota exceeded for user {user_id} on {path}")
            raise AIQuotaExceeded(retry_after)

        response = await call_next(request)
        
        # Add metadata headers
        response.headers["X-AI-Quota-Remaining"] = str(int(tokens_left))
        return response

    async def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request state or tokens."""
        # 1. Try request.state (if populated by a previous middleware)
        if hasattr(request.state, "user") and request.state.user:
            return str(request.state.user.id)
        
        # 2. Try to decode JWT from Header or Cookie manually
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        if not token:
            token = request.cookies.get("graftai_access_token")

        if token:
            try:
                from jose import jwt
                from backend.auth.config import SECRET_KEY, ALGORITHM
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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

            # LUA script for atomic update
            lua = """
            local bucket = redis.call('HMGET', KEYS[1], 'tokens', 'last_update')
            local tokens = tonumber(bucket[1])
            local last_update = tonumber(bucket[2])
            
            local now = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local capacity = tonumber(ARGV[3])
            local cost = tonumber(ARGV[4])
            
            if tokens == nil then
                tokens = capacity
                last_update = now
            else
                local delta = math.max(0, now - last_update)
                tokens = math.min(capacity, tokens + delta * refill_rate)
                last_update = now
            end
            
            local allowed = false
            if tokens >= cost then
                tokens = tokens - cost
                allowed = true
            end
            
            redis.call('HMSET', KEYS[1], 'tokens', tokens, 'last_update', last_update)
            redis.call('EXPIRE', KEYS[1], 86400) -- Clean up after 24h of inactivity
            
            return {allowed and 1 or 0, tokens}
            """
            
            result = await r.eval(lua, 1, key, now, refill_rate, capacity, cost)
            allowed = bool(result[0])
            tokens_left = float(result[1])
            
            retry_after = 0
            if not allowed:
                retry_after = int((cost - tokens_left) / refill_rate) + 1

            return allowed, tokens_left, retry_after

        except Exception as e:
            logger.error(f"Redis quota check failed: {e}")
            return True, 0, 0
