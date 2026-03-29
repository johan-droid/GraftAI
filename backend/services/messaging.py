"""Real-time instant messaging service using Redis pub/sub."""

from typing import Dict, Any, List
from backend.services.redis_client import publish, subscribe
import json
import logging

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "chat_message_"


def send_message(user_id: int, message: str, metadata: Dict[str, Any] = None):
    payload = {
        "user_id": user_id,
        "message": message,
        "metadata": metadata or {},
    }
    publish(f"{CHANNEL_PREFIX}{user_id}", json.dumps(payload))
    logger.info(f"Published message to user {user_id}")


def subscribe_user_channel(user_id: int):
    return subscribe(f"{CHANNEL_PREFIX}{user_id}")
