import logging
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.scheduler import get_optimized_context
from backend.services.redis_client import get_redis

logger = logging.getLogger(__name__)

class ContextPrefetcher:
    """
    Proactive Context Caching.
    Pre-computes and stores the AI context for a user in Redis.
    """
    
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    async def prefetch_user_context(cls, db: AsyncSession, user_id: str, org_id: int, workspace_id: Optional[int] = None):
        """
        Computes the current day's optimized context and caches it (Scoped by Org).
        """
        try:
            now = datetime.now()
            context_str = await get_optimized_context(db, user_id, now, org_id=org_id, workspace_id=workspace_id)
            
            redis = await get_redis()
            # Context is scoped by user + org + workspace
            ws_suffix = f":ws_{workspace_id}" if workspace_id else ""
            cache_key = f"ai_context:{user_id}:org_{org_id}{ws_suffix}:{now.strftime('%Y%mkd')}"
            
            await redis.setex(cache_key, cls.CACHE_TTL, context_str)
            logger.info(f"⚡ Context prefetched for user {user_id} in org {org_id}")
            
        except Exception as e:
            logger.error(f"⚠ Prefetch failed for user {user_id}: {e}")

    @classmethod
    async def get_cached_context(cls, user_id: str, org_id: Optional[int] = None, workspace_id: Optional[int] = None) -> Optional[str]:
        """Retrieves cached context from Redis if available (SaaS Secure)."""
        try:
            redis = await get_redis()
            now = datetime.now()
            # If org_id is None, it might be a legacy call or un-scoped
            scope = f"org_{org_id}" if org_id else "global"
            ws_suffix = f":ws_{workspace_id}" if workspace_id else ""
            cache_key = f"ai_context:{user_id}:{scope}{ws_suffix}:{now.strftime('%Y%mkd')}"
            return await redis.get(cache_key)
        except Exception:
            return None

prefetcher = ContextPrefetcher()
