from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.utils.db import get_db
from backend.auth.schemes import get_current_user_id
from backend.models.tables import AuditLogTable, UserTable
from backend.models.base import DBModel

router = APIRouter()

class AuditLogResponse(DBModel):
    id: str
    timestamp: datetime
    action: str
    event_category: str
    severity: str
    status: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    metadata_json: Optional[dict]



@router.get("/me", response_model=List[AuditLogResponse])
async def get_my_audit_logs(
    limit: int = Query(50, le=100),
    offset: int = 0,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Retrieve audit logs for the current user.
    Provides transparency into AI usage, billing actions, and security events.
    """
    stmt = select(AuditLogTable).where(AuditLogTable.user_id == user_id)
    
    if category:
        stmt = stmt.where(AuditLogTable.event_category == category)
        
    stmt = stmt.order_by(desc(AuditLogTable.timestamp)).limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs

@router.get("/stats")
async def get_my_usage_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get aggregated usage stats from the user's meter reading fields.
    """
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "ai_tokens": user.total_ai_tokens,
        "api_calls": user.total_api_calls,
        "scheduling_count": user.total_scheduling_count,
        "daily_ai_usage": user.daily_ai_count,
        "daily_sync_usage": user.daily_sync_count,
        "tier": user.tier,
        "subscription_status": user.subscription_status
    }
