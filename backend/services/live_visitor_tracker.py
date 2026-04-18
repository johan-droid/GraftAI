"""
Live Visitor Tracking Service

Uses Redis pub/sub for multi-instance coordination.
Tracks live visitors across multiple backend instances.
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os
import asyncio

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
VISITOR_TTL_SECONDS = 300  # 5 minutes
HEARTBEAT_INTERVAL = 60  # 1 minute


class LiveVisitorTracker:
    """
    Multi-instance live visitor tracking using Redis.

    Uses Redis sets to track active visitors and pub/sub for
    cross-instance coordination.
    """

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - live visitor tracking disabled")
            return False

        try:
            self.redis = await redis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await self.redis.ping()
            self.connected = True
            logger.info("✅ Live visitor tracker connected to Redis")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.connected = False

    async def track_visitor(
        self,
        visitor_id: str,
        page: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track a visitor as active on a page.

        Args:
            visitor_id: Unique visitor identifier (user_id or session_id)
            page: Current page path
            metadata: Optional metadata (user agent, IP, etc.)

        Returns:
            True if tracking succeeded, False otherwise
        """
        if not self.connected:
            return False

        try:
            # Store visitor data with TTL
            key = f"visitor:{visitor_id}"
            data = {
                "visitor_id": visitor_id,
                "page": page,
                "metadata": metadata or {},
                "last_seen": datetime.now(timezone.utc).isoformat(),
            }

            await self.redis.setex(key, VISITOR_TTL_SECONDS, json.dumps(data))

            # Add to live visitors set
            await self.redis.sadd("live_visitors", visitor_id)

            # Publish update for other instances
            await self.redis.publish(
                "visitor_updates",
                json.dumps({"action": "track", "visitor_id": visitor_id}),
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track visitor: {e}")
            return False

    async def remove_visitor(self, visitor_id: str) -> bool:
        """Remove a visitor from tracking."""
        if not self.connected:
            return False

        try:
            # Remove from Redis
            key = f"visitor:{visitor_id}"
            await self.redis.delete(key)
            await self.redis.srem("live_visitors", visitor_id)

            # Publish update
            await self.redis.publish(
                "visitor_updates",
                json.dumps({"action": "remove", "visitor_id": visitor_id}),
            )

            return True

        except Exception as e:
            logger.error(f"Failed to remove visitor: {e}")
            return False

    async def get_live_visitor_count(self) -> int:
        """Get the current count of live visitors."""
        if not self.connected:
            return 0

        try:
            return await self.redis.scard("live_visitors")
        except Exception as e:
            logger.error(f"Failed to get visitor count: {e}")
            return 0

    async def get_live_visitors(self, limit: int = 100) -> list:
        """Get details of live visitors."""
        if not self.connected:
            return []

        try:
            visitor_ids = await self.redis.smembers("live_visitors")
            visitors = []

            for visitor_id in list(visitor_ids)[:limit]:
                key = f"visitor:{visitor_id}"
                data = await self.redis.get(key)
                if data:
                    visitors.append(json.loads(data))

            return visitors

        except Exception as e:
            logger.error(f"Failed to get live visitors: {e}")
            return []

    async def start_heartbeat(self, visitor_id: str, page: str) -> None:
        """
        Start heartbeat for a visitor.

        This should be called when a visitor first arrives.
        It periodically refreshes the visitor's TTL.
        """
        if not self.connected:
            return

        async def heartbeat_loop():
            while self.connected:
                await self.track_visitor(visitor_id, page)
                await asyncio.sleep(HEARTBEAT_INTERVAL)

        # Start heartbeat in background
        asyncio.create_task(heartbeat_loop())

    async def cleanup_expired_visitors(self) -> int:
        """
        Clean up expired visitors (those whose TTL has passed).

        This is called periodically by a background task.
        """
        if not self.connected:
            return 0

        try:
            # Get all visitor IDs
            visitor_ids = await self.redis.smembers("live_visitors")
            cleaned = 0

            for visitor_id in visitor_ids:
                key = f"visitor:{visitor_id}"
                exists = await self.redis.exists(key)

                if not exists:
                    # TTL expired, remove from set
                    await self.redis.srem("live_visitors", visitor_id)
                    cleaned += 1

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired visitors")

            return cleaned

        except Exception as e:
            logger.error(f"Failed to cleanup expired visitors: {e}")
            return 0


# Global tracker instance
_tracker: Optional[LiveVisitorTracker] = None


def get_tracker() -> LiveVisitorTracker:
    """Get or create the global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = LiveVisitorTracker()
    return _tracker


# Background task for periodic cleanup
async def visitor_cleanup_task() -> None:
    """Background task to clean up expired visitors."""
    tracker = get_tracker()
    await tracker.connect()

    while True:
        try:
            await tracker.cleanup_expired_visitors()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Visitor cleanup task error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error
