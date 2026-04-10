"""Audit logging utility for SOC 2 compliance and security monitoring."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.tables import AuditLogTable

logger = logging.getLogger(__name__)


class EventCategory(str, Enum):
    """Event categories for audit logging."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM = "system"
    SECURITY = "security"
    MFA = "mfa"


class EventType(str, Enum):
    """Event types for audit logging."""
    # Authentication events
    LOGIN = "login"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOCATION = "token_revocation"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    
    # MFA events
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_SETUP_INITIATED = "mfa_setup_initiated"
    MFA_VERIFICATION_SUCCESS = "mfa_verification_success"
    MFA_VERIFICATION_FAILURE = "mfa_verification_failure"
    MFA_BACKUP_CODE_USED = "mfa_backup_code_used"
    
    # OAuth events
    OAUTH_LOGIN = "oauth_login"
    OAUTH_LINK = "oauth_link"
    OAUTH_UNLINK = "oauth_unlink"
    
    # Authorization events
    PERMISSION_DENIED = "permission_denied"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    
    # Data access events
    USER_VIEW = "user_view"
    CALENDAR_VIEW = "calendar_view"
    EVENT_VIEW = "event_view"
    BOOKING_VIEW = "booking_view"
    DATA_EXPORT = "data_export"
    
    # Data modification events
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    CALENDAR_CREATE = "calendar_create"
    CALENDAR_UPDATE = "calendar_update"
    CALENDAR_DELETE = "calendar_delete"
    EVENT_CREATE = "event_create"
    EVENT_UPDATE = "event_update"
    EVENT_DELETE = "event_delete"
    BOOKING_CREATE = "booking_create"
    BOOKING_UPDATE = "booking_update"
    BOOKING_DELETE = "booking_delete"
    
    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    CSRF_ATTEMPT = "csrf_attempt"
    XSS_ATTEMPT = "xss_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    
    # System events
    CONFIGURATION_CHANGE = "configuration_change"
    BACKUP_STARTED = "backup_started"
    BACKUP_COMPLETED = "backup_completed"
    BACKUP_FAILED = "backup_failed"


class Severity(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Action(str, Enum):
    """Action types for audit events."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    EXPORT = "export"


class Result(str, Enum):
    """Result types for audit events."""
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    PENDING = "pending"


class AuditLogger:
    """SOC 2 compliant audit logging system."""
    
    # Critical events that require immediate attention
    CRITICAL_EVENTS = {
        EventType.PRIVILEGE_ESCALATION,
        EventType.CSRF_ATTEMPT,
        EventType.SQL_INJECTION_ATTEMPT,
        EventType.SUSPICIOUS_ACTIVITY,
    }
    
    # Events that should trigger security alerts
    ALERT_EVENTS = {
        EventType.LOGIN_FAILURE,
        EventType.MFA_VERIFICATION_FAILURE,
        EventType.PERMISSION_DENIED,
        EventType.RATE_LIMIT_EXCEEDED,
        EventType.INVALID_TOKEN,
    }
    
    @staticmethod
    async def log(
        db: AsyncSession,
        event_type: EventType,
        event_category: EventCategory,
        action: Action,
        result: Result,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
        severity: Optional[Severity] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compliance_standards: Optional[List[str]] = None,
        data_subjects_affected: Optional[int] = None,
        data_categories: Optional[List[str]] = None,
    ) -> AuditLogTable:
        """
        Log an audit event.
        
        Args:
            db: Database session
            event_type: Type of event
            event_category: Category of event
            action: Action performed
            result: Result of the action
            user_id: ID of the user who performed the action
            user_email: Email of the user
            ip_address: Client IP address
            user_agent: Client user agent
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            failure_reason: Reason for failure (if applicable)
            severity: Severity level (auto-determined if not provided)
            metadata: Additional JSON metadata
            compliance_standards: List of compliance standards (e.g., ['SOC2', 'GDPR'])
            data_subjects_affected: Number of data subjects affected (for GDPR)
            data_categories: List of data categories affected
            
        Returns:
            The created AuditLogTable instance
        """
        # Auto-determine severity if not provided
        if severity is None:
            severity = AuditLogger._determine_severity(event_type, result)
        
        # Create audit log entry
        audit_entry = AuditLogTable(
            timestamp=datetime.now(timezone.utc),
            event_type=event_type.value,
            event_category=event_category.value,
            severity=severity.value,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action.value,
            resource_type=resource_type or "system",
            resource_id=resource_id,
            result=result.value,
            failure_reason=failure_reason,
            metadata_json=metadata,
            compliance_standards=compliance_standards or ["SOC2"],
            data_subjects_affected=data_subjects_affected,
            data_categories=data_categories,
        )
        
        db.add(audit_entry)
        await db.commit()
        
        # Log to standard logger for real-time monitoring
        log_message = (
            f"AUDIT: {event_category.value} | {event_type.value} | "
            f"user={user_email or user_id or 'anonymous'} | "
            f"action={action.value} | result={result.value}"
        )
        
        if result == Result.FAILURE:
            logger.warning(log_message)
        elif severity == Severity.CRITICAL:
            logger.critical(log_message)
            # Send alert to security team via webhook if configured
            await AuditLogger._send_security_alert(event_type, event_category, log_message, metadata)
        elif event_type in AuditLogger.ALERT_EVENTS:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return audit_entry
    
    @staticmethod
    def _determine_severity(event_type: EventType, result: Result) -> Severity:
        """Determine severity level based on event type and result."""
        if event_type in AuditLogger.CRITICAL_EVENTS:
            return Severity.CRITICAL
        
        if result == Result.DENIED:
            return Severity.WARNING
        
        if event_type in {EventType.LOGIN_FAILURE, EventType.MFA_VERIFICATION_FAILURE}:
            return Severity.WARNING
        
        if event_type in AuditLogger.ALERT_EVENTS:
            return Severity.WARNING
        
        return Severity.INFO
    
    @staticmethod
    async def log_auth_event(
        db: AsyncSession,
        event_type: EventType,
        result: Result,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLogTable:
        """Convenience method for logging authentication events."""
        return await AuditLogger.log(
            db=db,
            event_type=event_type,
            event_category=EventCategory.AUTHENTICATION,
            action=Action.LOGIN if "login" in event_type.value else Action.LOGOUT,
            result=result,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="user",
            resource_id=user_id,
            failure_reason=failure_reason,
            metadata=metadata,
            compliance_standards=["SOC2"],
        )
    
    @staticmethod
    async def log_data_access(
        db: AsyncSession,
        action: Action,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLogTable:
        """Convenience method for logging data access events."""
        event_type_map = {
            Action.CREATE: EventType.USER_CREATE if resource_type == "user" else EventType.CALENDAR_CREATE,
            Action.READ: EventType.USER_VIEW if resource_type == "user" else EventType.CALENDAR_VIEW,
            Action.UPDATE: EventType.USER_UPDATE if resource_type == "user" else EventType.CALENDAR_UPDATE,
            Action.DELETE: EventType.USER_DELETE if resource_type == "user" else EventType.CALENDAR_DELETE,
        }
        
        event_type = event_type_map.get(action, EventType.DATA_EXPORT)
        
        return await AuditLogger.log(
            db=db,
            event_type=event_type,
            event_category=EventCategory.DATA_ACCESS if action == Action.READ else EventCategory.DATA_MODIFICATION,
            action=action,
            result=Result.SUCCESS,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            compliance_standards=["SOC2", "GDPR"],
            data_subjects_affected=1 if resource_type == "user" else None,
        )
    
    @staticmethod
    async def query_recent_events(
        db: AsyncSession,
        hours: int = 24,
        event_category: Optional[EventCategory] = None,
        severity: Optional[Severity] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLogTable]:
        """
        Query recent audit events for monitoring and reporting.
        
        Args:
            db: Database session
            hours: Number of hours to look back
            event_category: Filter by event category
            severity: Filter by severity
            user_id: Filter by user
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        stmt = select(AuditLogTable).where(AuditLogTable.timestamp >= cutoff)
        
        if event_category:
            stmt = stmt.where(AuditLogTable.event_category == event_category.value)
        
        if severity:
            stmt = stmt.where(AuditLogTable.severity == severity.value)
        
        if user_id:
            stmt = stmt.where(AuditLogTable.user_id == user_id)
        
        stmt = stmt.order_by(AuditLogTable.timestamp.desc()).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_failed_login_attempts(
        db: AsyncSession,
        hours: int = 1,
        ip_address: Optional[str] = None,
    ) -> int:
        """
        Count failed login attempts for rate limiting and security monitoring.
        
        Args:
            db: Database session
            hours: Number of hours to look back
            ip_address: Optional IP address to filter by
            
        Returns:
            Number of failed login attempts
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        stmt = select(func.count(AuditLogTable.id)).where(
            AuditLogTable.event_type == EventType.LOGIN_FAILURE.value,
            AuditLogTable.timestamp >= cutoff,
        )
        
        if ip_address:
            stmt = stmt.where(AuditLogTable.ip_address == ip_address)
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    @staticmethod
    async def _send_security_alert(
        event_type: EventType,
        event_category: EventCategory,
        log_message: str,
        audit_data: Dict[str, Any]
    ) -> None:
        """Send security alert via webhook (Slack/Discord) for critical events."""
        import os
        import httpx
        
        webhook_url = os.getenv("SECURITY_WEBHOOK_URL")
        if not webhook_url:
            return  # No webhook configured, skip silently
        
        try:
            # Format alert payload
            alert_payload = {
                "text": f"🚨 SECURITY ALERT: {event_type.value}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 Security Alert: {event_type.value}",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Category:*\n{event_category.value}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*User:*\n{audit_data.get('user_email', 'Unknown')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*IP Address:*\n{audit_data.get('ip_address', 'Unknown')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Timestamp:*\n{datetime.now(timezone.utc).isoformat()}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{log_message}```"
                        }
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    webhook_url,
                    json=alert_payload,
                    timeout=5.0
                )
        except Exception as e:
            # Don't let webhook failures break audit logging
            logger.error(f"Failed to send security alert webhook: {e}")


# Global audit logger instance
audit_logger = AuditLogger()
