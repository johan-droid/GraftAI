import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import AuditLogTable

logger = logging.getLogger(__name__)

async def log_activity(db: AsyncSession, action: str, user_id: str | None=None, team_id: str | None=None, resource_type: str | None=None, resource_id: str | None=None, status: str="success", metadata: dict[str, Any] | None=None, ip_address: str | None=None, user_agent: str | None=None, event_type: str | None=None, event_category: str | None=None, severity: str="info"):
    """
    Records a high-level activity log entry for SaaS compliance and auditing.
    """
    try:
        if not event_type:
            event_type = action
        if not event_category:
            if "." in action:
                event_category = action.split(".", maxsplit=1)[0]
            else:
                event_category = "system"
        new_log = AuditLogTable(user_id=user_id, team_id=team_id, action=action, event_type=event_type, event_category=event_category, severity=severity, resource_type=resource_type, resource_id=resource_id, status=status, result=status, metadata_json=metadata, ip_address=ip_address, user_agent=user_agent)
        db.add(new_log)
        await db.flush()
    except Exception as e:
        logger.error("Failed to write audit log: %s", e, exc_info=True)
