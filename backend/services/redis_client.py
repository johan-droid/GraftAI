import os
import logging
from redis import asyncio as aioredis
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Ensure .env is loaded
load_dotenv()

_redis_client = None

async def get_redis_client():
    """
    Returns a singleton instance of the async Redis client.
    Connects using REDIS_URL from environment variables.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        _redis_client = aioredis.from_url(
            redis_url, 
            encoding="utf-8", 
            decode_responses=False # Keep False for binary compatibility with serializers
        )
        # Test connection
        await _redis_client.ping()
        logger.info(f"✅ Connected to Redis at {redis_url}")
        return _redis_client
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis at {redis_url}: {e}")
        return None

async def get_redis_binary():
    """Alias for binary-compatible redis client usage."""
    return await get_redis_client()
