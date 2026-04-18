"""Data breach notification system for GDPR Articles 33-34 compliance."""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.dsr import DataBreachRecord

logger = logging.getLogger(__name__)


class BreachManager:
    """GDPR Articles 33-34 - Data Breach Notification manager."""

    SUPERVISORY_NOTIFICATION_DEADLINE = 72  # hours from discovery
    DATA_SUBJECT_NOTIFICATION_THRESHOLD = "high"

    BREACH_NATURES = [
        "unauthorized_access",
        "unauthorized_disclosure",
        "loss_of_data",
        "destruction_of_data",
        "alteration_of_data",
        "other",
    ]

    RISK_LEVELS = ["low", "medium", "high", "critical"]

    def __init__(self):
        pass

    async def report_breach(
        self,
        db: AsyncSession,
        breach_details: Dict[str, Any],
        reported_by: str,
    ) -> DataBreachRecord:
        """
        Report a suspected or confirmed data breach.

        Args:
            breach_details: Dict containing breach information
            reported_by: User ID of person reporting the breach
        """
        # Generate breach reference
        breach_ref = (
            f"BRE-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        )

        # Create breach record
        breach = DataBreachRecord(
            breach_reference=breach_ref,
            discovered_at=datetime.utcnow(),
            nature_of_breach=breach_details.get("nature", "other"),
            data_categories=breach_details.get("data_categories", []),
            data_subjects_affected=breach_details.get("subjects_affected"),
            approximate_subjects=breach_details.get("approximate_subjects", "unknown"),
            risk_level=breach_details.get("risk_level", "medium"),
            likely_consequences=breach_details.get("consequences"),
            special_category_data=breach_details.get("special_category_data", False),
            children_affected=breach_details.get("children_affected", False),
            containment_measures=breach_details.get("containment_measures", []),
            remediation_actions=breach_details.get("remediation_actions", []),
            status="investigating",
        )

        db.add(breach)
        await db.commit()

        logger.warning(
            f"Data breach reported: {breach_ref} - {breach.nature_of_breach}"
        )

        # Notify DPO immediately
        await self._notify_dpo(breach)

        # Assess if immediate supervisory notification is required
        if breach.risk_level in ["high", "critical"]:
            await self._notify_supervisory_authority(db, breach)

        return breach

    async def update_breach_status(
        self,
        db: AsyncSession,
        breach_id: str,
        status: str,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> DataBreachRecord:
        """Update breach status with additional information."""
        stmt = select(DataBreachRecord).where(DataBreachRecord.id == breach_id)
        breach = (await db.execute(stmt)).scalars().first()

        if not breach:
            raise ValueError(f"Breach not found: {breach_id}")

        breach.status = status

        if additional_info:
            if "containment_measures" in additional_info:
                breach.containment_measures = additional_info["containment_measures"]
            if "remediation_actions" in additional_info:
                breach.remediation_actions = additional_info["remediation_actions"]
            if "data_subjects_affected" in additional_info:
                breach.data_subjects_affected = additional_info[
                    "data_subjects_affected"
                ]

        if status == "closed":
            breach.closed_at = datetime.utcnow()

        await db.commit()

        return breach

    async def notify_supervisory_authority(
        self,
        db: AsyncSession,
        breach_id: str,
        supervisory_authority: str = "DPC",  # Data Protection Commission (Ireland)
    ) -> DataBreachRecord:
        """
        Notify supervisory authority of data breach (Article 33).

        Must be done within 72 hours of discovery.
        """
        stmt = select(DataBreachRecord).where(DataBreachRecord.id == breach_id)
        breach = (await db.execute(stmt)).scalars().first()

        if not breach:
            raise ValueError(f"Breach not found: {breach_id}")

        # Check if already notified
        if breach.supervisory_notified:
            logger.warning(
                f"Supervisory authority already notified for breach {breach.breach_reference}"
            )
            return breach

        # Check deadline
        hours_since_discovery = (
            datetime.utcnow() - breach.discovered_at
        ).total_seconds() / 3600
        if hours_since_discovery > self.SUPERVISORY_NOTIFICATION_DEADLINE:
            logger.error(
                f"Breach notification deadline exceeded: {hours_since_discovery:.1f} hours"
            )

        # Generate notification
        notification = {
            "breach_reference": breach.breach_reference,
            "nature_of_breach": breach.nature_of_breach,
            "categories_data": breach.data_categories,
            "approximate_subjects": breach.approximate_subjects,
            "likely_consequences": breach.likely_consequences,
            "measures_taken": breach.containment_measures,
            "contact_details": "dpo@graftai.com",
            "submitted_at": datetime.utcnow().isoformat(),
        }

        # Send notification (in production, integrate with DPC API)
        await self._send_supervisory_notification(notification, supervisory_authority)

        # Update breach record
        breach.supervisory_notified = True
        breach.supervisory_notified_at = datetime.utcnow()
        breach.supervisory_authority = supervisory_authority

        await db.commit()

        logger.info(
            f"Supervisory authority notified for breach {breach.breach_reference}"
        )

        return breach

    async def notify_data_subjects(
        self,
        db: AsyncSession,
        breach_id: str,
        notification_method: str = "email",
    ) -> DataBreachRecord:
        """
        Notify data subjects of breach (Article 34).

        Required when breach poses high risk to rights and freedoms.
        """
        stmt = select(DataBreachRecord).where(DataBreachRecord.id == breach_id)
        breach = (await db.execute(stmt)).scalars().first()

        if not breach:
            raise ValueError(f"Breach not found: {breach_id}")

        # Check if notification is required
        if breach.risk_level not in ["high", "critical"]:
            logger.info(
                f"Breach risk level {breach.risk_level} does not require data subject notification"
            )
            return breach

        # Check if already notified
        if breach.data_subjects_notified:
            logger.warning(
                f"Data subjects already notified for breach {breach.breach_reference}"
            )
            return breach

        # Generate notification
        notification = {
            "breach_reference": breach.breach_reference,
            "nature_of_breach": breach.nature_of_breach,
            "likely_consequences": breach.likely_consequences,
            "measures_taken": breach.containment_measures,
            "contact_details": "dpo@graftai.com",
            "sent_at": datetime.utcnow().isoformat(),
        }

        # Send notifications to affected subjects
        await self._send_subject_notifications(notification, breach)

        # Update breach record
        breach.data_subjects_notified = True
        breach.data_subjects_notified_at = datetime.utcnow()
        breach.notification_method = notification_method

        await db.commit()

        logger.info(f"Data subjects notified for breach {breach.breach_reference}")

        return breach

    async def get_breach_report(
        self, db: AsyncSession, breach_id: str
    ) -> Dict[str, Any]:
        """Generate detailed breach report."""
        stmt = select(DataBreachRecord).where(DataBreachRecord.id == breach_id)
        breach = (await db.execute(stmt)).scalars().first()

        if not breach:
            raise ValueError(f"Breach not found: {breach_id}")

        return {
            "breach_reference": breach.breach_reference,
            "discovered_at": breach.discovered_at.isoformat(),
            "reported_at": breach.reported_at.isoformat()
            if breach.reported_at
            else None,
            "nature_of_breach": breach.nature_of_breach,
            "data_categories": breach.data_categories,
            "data_subjects_affected": breach.data_subjects_affected,
            "approximate_subjects": breach.approximate_subjects,
            "risk_level": breach.risk_level,
            "likely_consequences": breach.likely_consequences,
            "special_category_data": breach.special_category_data,
            "children_affected": breach.children_affected,
            "containment_measures": breach.containment_measures,
            "remediation_actions": breach.remediation_actions,
            "supervisory_notified": breach.supervisory_notified,
            "supervisory_notified_at": breach.supervisory_notified_at.isoformat()
            if breach.supervisory_notified_at
            else None,
            "supervisory_authority": breach.supervisory_authority,
            "data_subjects_notified": breach.data_subjects_notified,
            "data_subjects_notified_at": breach.data_subjects_notified_at.isoformat()
            if breach.data_subjects_notified_at
            else None,
            "notification_method": breach.notification_method,
            "subprocessors_notified": breach.subprocessors_notified,
            "status": breach.status,
            "closed_at": breach.closed_at.isoformat() if breach.closed_at else None,
            "dpo_consulted": breach.dpo_consulted,
            "dpo_recommendations": breach.dpo_recommendations,
        }

    async def list_breaches(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List data breach records."""
        stmt = select(DataBreachRecord)

        if status:
            stmt = stmt.where(DataBreachRecord.status == status)

        stmt = stmt.order_by(DataBreachRecord.discovered_at.desc()).limit(limit)
        breaches = (await db.execute(stmt)).scalars().all()

        return [
            {
                "id": b.id,
                "breach_reference": b.breach_reference,
                "discovered_at": b.discovered_at.isoformat(),
                "nature_of_breach": b.nature_of_breach,
                "risk_level": b.risk_level,
                "status": b.status,
                "supervisory_notified": b.supervisory_notified,
                "data_subjects_notified": b.data_subjects_notified,
            }
            for b in breaches
        ]

    async def _notify_dpo(self, breach: DataBreachRecord):
        """Notify Data Protection Officer of breach."""
        # In production, send email/pager alert to DPO
        logger.critical(
            f"DPO ALERT: Breach {breach.breach_reference} - {breach.nature_of_breach}"
        )
        breach.dpo_consulted = True

    async def _notify_supervisory_authority(
        self,
        db: AsyncSession,
        breach: DataBreachRecord,
    ):
        """Immediately notify supervisory authority for high-risk breaches."""
        await self.notify_supervisory_authority(db, breach.id)

    async def _send_supervisory_notification(
        self,
        notification: Dict[str, Any],
        authority: str,
    ):
        """Send notification to supervisory authority."""
        # In production, integrate with DPC/ICO/other authority APIs
        logger.info(
            f"Sending breach notification to {authority}: {notification['breach_reference']}"
        )

    async def _send_subject_notifications(
        self,
        notification: Dict[str, Any],
        breach: DataBreachRecord,
    ):
        """Send notifications to affected data subjects."""
        # In production, send emails to affected users
        logger.info(
            f"Sending subject notifications for breach {breach.breach_reference}"
        )


# Global breach manager instance
breach_manager = BreachManager()
