import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.api.deps import get_db
from backend.models.user_token import UserTokenTable
from backend.utils.redis_singleton import get_redis
from backend.auth.schemes import get_current_user_id
from backend.services.access_control import check_user_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/sync-status")
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Administrative overview of synchronization health.
    Requires admin privileges.
    """
    if not check_user_role(current_user_id, "admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")

    try:
        # 1. Check Redis Connectivity
        redis_client = get_redis()
        redis_ok = False
        try:
            redis_ok = redis_client.ping()
        except Exception:
            pass

        # 2. Token Health Metrics
        # Count total tokens per provider
        token_counts_stmt = select(
            UserTokenTable.provider, 
            func.count(UserTokenTable.id).label("total"),
            func.count(UserTokenTable.id).filter(UserTokenTable.is_active == True).label("active")
        ).group_by(UserTokenTable.provider)
        
        counts_res = await db.execute(token_counts_stmt)
        provider_stats = []
        for row in counts_res.all():
            provider_stats.append({
                "provider": row.provider,
                "total_tokens": row.total,
                "active_tokens": row.active,
                "health_rate": (row.active / row.total * 100) if row.total > 0 else 100
            })

        # 3. Recent Sync Failures (Expired tokens that are still marked active)
        now = datetime.now(timezone.utc)
        expired_stmt = select(func.count(UserTokenTable.id)).where(
            UserTokenTable.is_active == True,
            UserTokenTable.expires_at < now
        )
        expired_res = await db.execute(expired_stmt)
        expired_count = expired_res.scalar() or 0

        return {
            "status": "operational",
            "timestamp": now.isoformat(),
            "infrastructure": {
                "redis_connected": redis_ok,
                "database_connected": True
            },
            "sync_metrics": {
                "providers": provider_stats,
                "tokens_requiring_refresh": expired_count,
            }
        }
    except Exception as e:
        logger.exception("Failed to fetch sync status")
        raise HTTPException(status_code=500, detail=f"Monitoring error: {str(e)}")
