import os
import redis
import json
import logging
from typing import List, Any
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)

def get_session_history(user_id: str, session_id: str = "default") -> RedisChatMessageHistory:
    """
    Retrieve or create a Redis-backed chat message history for a specific user session.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    key_prefix = f"chat_history:{user_id}:{session_id}"
    
    return RedisChatMessageHistory(
        session_id=key_prefix,
        url=redis_url,
        ttl=86400, # 24 hours retention
    )

def clear_session_history(user_id: str, session_id: str = "default"):
    """
    Purge the chat history for a specific user session.
    """
    history = get_session_history(user_id, session_id)
    history.clear()
