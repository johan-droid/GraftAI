import logging

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import AuditLogTable

logger = logging.getLogger(__name__)

async def log_activity(
    db: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    team_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    event_type: Optional[str] = None,
    event_category: Optional[str] = None,
    severity: str = "info"
):
    """
    Records a high-level activity log entry for SaaS compliance and auditing.
    """
    try:
        # Infer defaults if not provided
        if not event_type:
            event_type = action
        if not event_category:
            if "." in action:
                event_category = action.split(".")[0]
            else:
                event_category = "system"

        new_log = AuditLogTable(
            user_id=user_id,
            team_id=team_id,
            action=action,
            event_type=event_type,
            event_category=event_category,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            result=status, # Keep result synced with status for SOC 2 compatibility
            metadata_json=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(new_log)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}", exc_info=True)
        # We don't want to break the main flow if logging fails, 
        # but in a critical SaaS it might be required to fail open/closed.
        await db.rollback()
