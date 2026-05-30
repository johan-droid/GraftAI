from datetime import datetime

from backend.auth.schemes import get_current_user_id
from backend.core.saas_config import get_limit
from backend.models.base import DBModel
from backend.models.tables import AuditLogTable, UserTable
from backend.utils.db import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

class AuditLogResponse(DBModel):
    id: str
    timestamp: datetime
    action: str
    event_category: str
    severity: str
    status: str
    resource_type: str | None
    resource_id: str | None
    metadata_json: dict | None

@router.get("/me", response_model=list[AuditLogResponse])
async def get_my_audit_logs(limit: int=Query(50, le=100), offset: int=0, category: str | None=None, db: AsyncSession=Depends(get_db), user_id: str=Depends(get_current_user_id)):
    """
    Retrieve audit logs for the current user.
    Provides transparency into AI usage, billing actions, and security events.
    """
    stmt = select(AuditLogTable).where(AuditLogTable.user_id == user_id)
    if category:
        stmt = stmt.where(AuditLogTable.event_category == category)
    stmt = stmt.order_by(desc(AuditLogTable.timestamp)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/stats")
async def get_my_usage_stats(db: AsyncSession=Depends(get_db), user_id: str=Depends(get_current_user_id)):
    """
    Get aggregated usage stats from the user's meter reading fields.
    """
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    daily_ai_limit = user.daily_ai_limit if user.daily_ai_limit is not None else get_limit(user.tier, "daily_ai_messages")
    daily_sync_limit = user.daily_sync_limit if user.daily_sync_limit is not None else get_limit(user.tier, "daily_calendar_syncs")
    quota_reset_at = user.quota_reset_at.isoformat() if user.quota_reset_at else None
    return {"ai_tokens": user.total_ai_tokens, "api_calls": user.total_api_calls, "scheduling_count": user.total_scheduling_count, "daily_ai_usage": user.daily_ai_count, "daily_sync_usage": user.daily_sync_count, "daily_ai_limit": daily_ai_limit, "daily_sync_limit": daily_sync_limit, "ai_remaining": max(0, daily_ai_limit - user.daily_ai_count), "sync_remaining": max(0, daily_sync_limit - user.daily_sync_count), "quota_reset_at": quota_reset_at, "tier": user.tier, "subscription_status": user.subscription_status}
