"""API routes for audit log access."""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.auth.schemes import get_current_user_id
from backend.utils.db import get_db
from backend.models.tables import AuditLogTable

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Logs"])

class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    event_category: str
    severity: str
    action: str
    result: str
    resource_type: str
    class Config:
        from_attributes = True

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_my_audit_logs(
    hours: int = Query(default=24, ge=1, le=720),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    stmt = select(AuditLogTable).where(
        AuditLogTable.user_id == user_id,
        AuditLogTable.timestamp >= cutoff
    ).order_by(AuditLogTable.timestamp.desc()).limit(100)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [AuditLogResponse.from_orm(log) for log in logs]
