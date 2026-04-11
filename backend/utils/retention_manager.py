"""Data retention automation for GDPR Article 5.1.e compliance."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, exists, literal, func

from backend.models.dsr import DataRetentionSchedule
from backend.models.tables import (
    AuditLogTable,
    BookingTable,
    EventTable,
    UserMFATable,
    UserTokenTable,
    UserTable,
)

logger = logging.getLogger(__name__)


class DataRetentionManager:
    """GDPR Article 5.1.e - Storage Limitation compliance."""
    
    # Default retention schedules
    DEFAULT_SCHEDULES = {
        "user_profile": {
            "duration_days": 730,  # 2 years
            "action": "anonymize",
            "legal_basis": "contract",
            "data_types": ["email", "full_name", "timezone"],
        },
        "calendar_events": {
            "duration_days": 365,  # 1 year
            "action": "delete",
            "legal_basis": "consent",
            "data_types": ["event_title", "event_description", "attendees"],
        },
        "booking_history": {
            "duration_days": 1095,  # 3 years
            "action": "archive",
            "legal_basis": "contract",
            "data_types": ["booking_status", "booking_code"],
        },
        "audit_logs": {
            "duration_days": 2555,  # 7 years
            "action": "delete",
            "legal_basis": "legal_obligation",
            "data_types": ["event_type", "action", "result"],
        },
        "session_tokens": {
            "duration_days": 30,
            "action": "delete",
            "legal_basis": "security",
            "data_types": ["access_token", "refresh_token"],
        },
        "email_verification_codes": {
            "duration_days": 1,
            "action": "delete",
            "legal_basis": "security",
            "data_types": ["verification_code"],
        },
        "password_reset_tokens": {
            "duration_days": 1,
            "action": "delete",
            "legal_basis": "security",
            "data_types": ["reset_token"],
        },
        "mfa_backup_codes": {
            "duration_days": 365,  # 1 year after generation
            "action": "delete",
            "legal_basis": "security",
            "data_types": ["backup_codes"],
        },
    }
    
    def __init__(self):
        self.schedules = self.DEFAULT_SCHEDULES.copy()
    
    async def initialize_default_schedules(self, db: AsyncSession):
        """Initialize default retention schedules in database."""
        for category, schedule in self.DEFAULT_SCHEDULES.items():
            stmt = select(DataRetentionSchedule).where(
                DataRetentionSchedule.data_category == category
            )
            existing = (await db.execute(stmt)).scalars().first()
            
            if not existing:
                retention = DataRetentionSchedule(
                    data_category=category,
                    data_types=schedule["data_types"],
                    retention_days=schedule["duration_days"],
                    retention_basis=schedule["legal_basis"],
                    action_after_retention=schedule["action"],
                    auto_apply=True,
                )
                db.add(retention)
        
        await db.commit()
        logger.info("Default retention schedules initialized")
    
    async def apply_retention_policies(self, db: AsyncSession) -> Dict[str, int]:
        """
        Apply all retention policies and delete/expired data.
        
        Returns:
            Dict mapping category to count of records processed
        """
        results = {}
        
        # Get all active schedules
        stmt = select(DataRetentionSchedule).where(DataRetentionSchedule.auto_apply == True)
        schedules = (await db.execute(stmt)).scalars().all()
        
        for schedule in schedules:
            try:
                count = await self._apply_schedule(db, schedule)
                results[schedule.data_category] = count
                
                # Update last applied timestamp
                schedule.last_applied_at = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Failed to apply retention for {schedule.data_category}: {e}")
                results[schedule.data_category] = 0
        
        await db.commit()
        logger.info(f"Retention policies applied: {results}")
        
        return results
    
    async def _apply_schedule(self, db: AsyncSession, schedule: DataRetentionSchedule) -> int:
        """Apply a single retention schedule."""
        category = schedule.data_category
        cutoff_date = datetime.utcnow() - timedelta(days=schedule.retention_days)
        action = schedule.action_after_retention
        
        if action == "delete":
            return await self._delete_expired_data(db, category, cutoff_date)
        elif action == "anonymize":
            return await self._anonymize_expired_data(db, category, cutoff_date)
        elif action == "archive":
            return await self._archive_expired_data(db, category, cutoff_date)
        
        return 0
    
    async def _delete_expired_data(self, db: AsyncSession, category: str, cutoff: datetime) -> int:
        """Delete data older than retention period."""
        count = 0
        
        if category == "calendar_events":
            stmt = delete(EventTable).where(EventTable.created_at < cutoff)
            result = await db.execute(stmt)
            count = result.rowcount
        
        elif category == "booking_history":
            stmt = delete(BookingTable).where(
                BookingTable.created_at < cutoff,
                BookingTable.status.in_(["cancelled", "completed", "archived"]),
            )
            result = await db.execute(stmt)
            count = result.rowcount

        elif category == "audit_logs":
            stmt = delete(AuditLogTable).where(AuditLogTable.timestamp < cutoff)
            result = await db.execute(stmt)
            count = result.rowcount

        elif category == "session_tokens":
            stmt = delete(UserTokenTable).where(
                UserTokenTable.expires_at < cutoff
            )
            result = await db.execute(stmt)
            count = result.rowcount

        elif category == "email_verification_codes":
            if hasattr(UserTable, "email_verification_expires_at"):
                stmt = update(UserTable).where(
                    UserTable.email_verification_expires_at.is_not(None),
                    UserTable.email_verification_expires_at < cutoff,
                ).values(
                    email_verification_code=None,
                    email_verification_expires_at=None,
                )
                result = await db.execute(stmt)
                count = result.rowcount

        elif category == "mfa_backup_codes":
            stmt = update(UserMFATable).where(
                UserMFATable.backup_codes.is_not(None),
                UserMFATable.created_at < cutoff,
            ).values(backup_codes=None)
            result = await db.execute(stmt)
            count = result.rowcount
        
        logger.info(f"Deleted {count} records from {category}")
        return count
    
    async def _anonymize_expired_data(self, db: AsyncSession, category: str, cutoff: datetime) -> int:
        """Anonymize data older than retention period."""
        count = 0
        
        if category == "user_profile":
            # Anonymize old profiles that show no recent booking/event activity.
            recent_event_exists = exists(
                select(EventTable.id).where(
                    EventTable.user_id == UserTable.id,
                    EventTable.created_at >= cutoff,
                )
            )
            recent_booking_exists = exists(
                select(BookingTable.id).where(
                    BookingTable.user_id == UserTable.id,
                    BookingTable.created_at >= cutoff,
                )
            )

            stmt = update(UserTable).where(
                UserTable.created_at < cutoff,
                ~recent_event_exists,
                ~recent_booking_exists,
            ).values(
                full_name="Anonymized User",
                email=literal("anonymized-") + UserTable.id + literal("@internal.local"),
            )
            result = await db.execute(stmt)
            count = result.rowcount
        
        logger.info(f"Anonymized {count} records from {category}")
        return count
    
    async def _archive_expired_data(self, db: AsyncSession, category: str, cutoff: datetime) -> int:
        """Archive data older than retention period."""
        # In production, this would move data to cold storage
        count = 0
        
        if category == "booking_history":
            # Mark as archived for completed booking history only
            stmt = update(BookingTable).where(
                BookingTable.created_at < cutoff,
                BookingTable.status.in_(["confirmed", "rescheduled"]),
            ).values(status="archived")
            result = await db.execute(stmt)
            count = result.rowcount
        
        logger.info(f"Archived {count} records from {category}")
        return count
    
    async def get_retention_report(self, db: AsyncSession) -> Dict[str, Any]:
        """Generate retention compliance report."""
        stmt = select(DataRetentionSchedule)
        schedules = (await db.execute(stmt)).scalars().all()
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_schedules": len(schedules),
            "active_schedules": len([s for s in schedules if s.auto_apply]),
            "schedules": [],
        }
        
        for schedule in schedules:
            report["schedules"].append({
                "category": schedule.data_category,
                "retention_days": schedule.retention_days,
                "action": schedule.action_after_retention,
                "legal_basis": schedule.retention_basis,
                "auto_apply": schedule.auto_apply,
                "last_applied": schedule.last_applied_at.isoformat() if schedule.last_applied_at else None,
            })
        
        return report
    
    async def get_data_inventory(self, db: AsyncSession) -> Dict[str, Any]:
        """Generate data inventory for GDPR Article 30 RoPA."""
        
        # Count records in each table
        event_count = (await db.execute(select(func.count()).select_from(EventTable))).scalar() or 0
        booking_count = (await db.execute(select(func.count()).select_from(BookingTable))).scalar() or 0
        token_count = (await db.execute(select(func.count()).select_from(UserTokenTable))).scalar() or 0
        user_count = (await db.execute(select(func.count()).select_from(UserTable))).scalar() or 0
        
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "data_inventory": {
                "users": {"count": user_count, "categories": ["identification", "contact"]},
                "events": {"count": event_count, "categories": ["calendar_data"]},
                "bookings": {"count": booking_count, "categories": ["scheduling_data"]},
                "user_tokens": {"count": token_count, "categories": ["authentication_data"]},
            },
        }


# Global retention manager instance
retention_manager = DataRetentionManager()
