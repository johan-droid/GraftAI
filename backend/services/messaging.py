"""Real-time reliable messaging service using Redis Streams and MessagePack."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from backend.services.redis_client import get_redis_client
from backend.utils.serialization import serializer

logger = logging.getLogger(__name__)

# Constants for Stream Configuration
STREAM_MAXLEN = 5000  # Pin-point precision: keep last 5k messages per user
EVENT_STREAM_KEY = "stream:user:{user_id}"


async def send_message(
    user_id: str, message: str, metadata: Optional[Dict[str, Any]] = None
):
    """
    Publishes a reliable message to a user's dedicated Redis Stream.
    Uses MessagePack for binary efficiency.
    """
    redis = await get_redis_client()
    if not redis:
        logger.error(f"❌ Redis unavailable for sending message to {user_id}")
        return

    stream_key = EVENT_STREAM_KEY.format(user_id=user_id)
    payload = {
        "user_id": user_id,
        "message": message,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
    }

    # Binary optimization: pack the payload
    binary_payload = serializer.pack_for_cache(payload)

    try:
        # XADD: Append to stream with automatic trimming to prevent memory bloat
        await redis.xadd(
            stream_key, {"data": binary_payload}, maxlen=STREAM_MAXLEN, approximate=True
        )
        # LEGACY SUPPORT: Still publish to Pub/Sub for simple listeners (e.g. basic SSE)
        # but mark it as a 'flicker-safe' legacy bridge.
        await redis.publish(f"chat_message_{user_id}", binary_payload)

        logger.debug(f"✅ Streamed precise message to user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to stream message to {user_id}: {e}")


async def get_recent_messages(user_id: str, count: int = 10) -> list:
    """
    Retrieves the most recent messages from a user's stream.
    Used for 'pin-point' state recovery if the frontend reconnects.
    """
    redis = await get_redis_client()
    if not redis:
        return []

    stream_key = EVENT_STREAM_KEY.format(user_id=user_id)
    try:
        # XREVRANGE: Fetch messages in reverse chronological order
        raw_rows = await redis.xrevrange(stream_key, count=count)
        messages = []
        for msg_id, data in raw_rows:
            binary_data = data.get(b"data")
            if binary_data:
                decoded = serializer.from_binary(binary_data)
                decoded["stream_id"] = msg_id.decode()
                messages.append(decoded)
        return messages
    except Exception as e:
        logger.error(f"❌ Failed to fetch recent messages for {user_id}: {e}")
        return []


async def acknowledge_message(user_id: str, group_name: str, message_id: str):
    """
    Acknowledges a message in a Consumer Group.
    Ready for 'Huge Crowd' multi-worker processing.
    """
    redis = await get_redis_client()
    if not redis:
        return
    stream_key = EVENT_STREAM_KEY.format(user_id=user_id)
    await redis.xack(stream_key, group_name, message_id)
