import os
import logging
import asyncio
from typing import Optional, Any
import redis.asyncio as redis

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_LUA = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('get', key)
if current and tonumber(current) >= limit then
    return 0
end

if not current then
    redis.call('set', key, 1)
    redis.call('expire', key, window)
else
    redis.call('incr', key)
end
return 1
"""

logger = logging.getLogger(__name__)

class ResilientRedisClient:
    """
    SaaS-Grade High-Performance Async Redis Client.
    Features:
    - Connection pooling for sub-millisecond latency.
    - Global fail-open resilience (Infrastructure issues won't crash the API).
    - Intelligent SSL handling for rediss:// (Upstash/Managed Redis).
    """
    
    _instance: Optional["ResilientRedisClient"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResilientRedisClient, cls).__new__(cls)
        return cls._instance

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._initialize()
        return self._client

    def _initialize(self):
        """Lazy initialization of the Redis connection pool."""
        options = {
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
        
        if REDIS_URL.startswith("rediss://"):
            options.update({
                "ssl_cert_reqs": None,
                "socket_keepalive": True
            })
            
        self._client = redis.from_url(REDIS_URL, **options)
        logger.info(f"🚀 Resilient Redis Client initialized (SaaS Mode: {REDIS_URL.split('@')[-1]})")

    async def get_redis(self) -> redis.Redis:
        return self.client

    async def check_health(self) -> bool:
        """SaaS health check for observability."""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"❌ Redis Health Check Failed: {e}")
            return False

    async def acquire_lock(self, lock_name: str, expiry: int = 60) -> bool:
        """Atomic distributed lock with fail-safe behavior."""
        try:
            return bool(await self.client.set(f"lock:{lock_name}", "locked", ex=expiry, nx=True))
        except Exception as e:
            logger.warning(f"⚠ Lock acquisition failed (failing open): {e}")
            return True # Fail open to prevent deadlocks in SaaS environments

    async def release_lock(self, lock_name: str):
        """Graceful lock release."""
        try:
            await self.client.delete(f"lock:{lock_name}")
        except Exception as e:
            logger.warning(f"⚠ Lock release failed: {e}")

    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Atomic rate limiting via Lua script with absolute resilience."""
        try:
            result = await self.client.eval(RATE_LIMIT_LUA, 1, key, limit, window)
            return bool(result)
        except Exception as e:
            logger.warning(f"⚠ Rate limit check failed (failing open): {e}")
            return True # SaaS users should never see 500s because of cache issues

    async def publish(self, channel: str, message: str):
        try:
            await self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"⚠ Redis Publish Error: {e}")

    def subscribe(self, channel: str):
        """Returns an async pubsub instance."""
        pubsub = self.client.pubsub()
        return pubsub

# Centralized Singleton for high-performance access
redis_service = ResilientRedisClient()

# Maintain backwards-compatible signatures for initial migration (but marked as async)
async def get_redis():
    return await redis_service.get_redis()

async def check_rate_limit(key: str, limit: int, window: int) -> bool:
    return await redis_service.check_rate_limit(key, limit, window)

async def acquire_lock(lock_name: str, expiry: int = 60) -> bool:
    return await redis_service.acquire_lock(lock_name, expiry)

async def release_lock(lock_name: str):
    await redis_service.release_lock(lock_name)

async def publish(channel: str, message: str):
    await redis_service.publish(channel, message)

def subscribe(channel: str):
    return redis_service.subscribe(channel)
