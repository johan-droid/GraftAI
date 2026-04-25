"""Records of Processing Activities (RoPA) manager for GDPR Article 30 compliance."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.dsr import DataProcessingRecord

logger = logging.getLogger(__name__)


class RoPAManager:
    """GDPR Article 30 - Records of Processing Activities manager."""

    # Default processing activities
    DEFAULT_ACTIVITIES = {
        "ROP-001": {
            "activity_name": "User Account Management",
            "activity_description": "User authentication, authorization, and account maintenance",
            "purposes": [
                "User authentication and authorization",
                "Account maintenance and security",
                "User profile management",
            ],
            "data_categories": [
                "Identification data (email, name)",
                "Authentication data (password hash)",
                "Contact data (timezone, preferences)",
            ],
            "data_subjects": ["customers", "prospective customers"],
            "internal_recipients": ["Authentication service", "Customer support"],
            "external_recipients": [],
            "subprocessors": [],
            "legal_basis": "contract",
            "legal_basis_details": "Performance of service contract (Article 6.1.b)",
            "retention_period_days": 730,
            "retention_basis": "Legal obligation for accounting and security",
            "security_measures": [
                "Encryption at rest (AES-256)",
                "Encryption in transit (TLS 1.3)",
                "Multi-factor authentication",
                "Rate limiting",
                "Input validation",
            ],
            "encryption_applied": True,
            "pseudonymization_applied": False,
            "involves_transfers": False,
            "is_active": True,
        },
        "ROP-002": {
            "activity_name": "Calendar Synchronization",
            "activity_description": "Sync user calendar events from external providers",
            "purposes": [
                "Sync user calendar events",
                "Provide scheduling services",
                "Generate availability windows",
            ],
            "data_categories": [
                "Calendar event data (title, time, attendees)",
                "Time zone information",
                "Meeting URLs and locations",
            ],
            "data_subjects": ["customers"],
            "internal_recipients": ["Calendar sync service", "Scheduling engine"],
            "external_recipients": ["Google Calendar API", "Microsoft Graph API"],
            "subprocessors": ["Google LLC", "Microsoft Corporation"],
            "legal_basis": "consent",
            "legal_basis_details": "User consent for calendar access (Article 6.1.a)",
            "retention_period_days": 365,
            "retention_basis": "Data minimization - only needed for scheduling",
            "security_measures": [
                "OAuth 2.0 with refresh tokens",
                "Token encryption",
                "API rate limiting",
                "Secure token storage",
            ],
            "encryption_applied": True,
            "pseudonymization_applied": False,
            "involves_transfers": True,
            "transfer_mechanism": "SCCs",
            "transfer_countries": ["United States"],
            "is_active": True,
        },
        "ROP-003": {
            "activity_name": "AI Copilot Processing",
            "activity_description": "Natural language command processing and scheduling suggestions",
            "purposes": [
                "Natural language command processing",
                "Scheduling suggestions and optimization",
                "AI-powered calendar assistance",
            ],
            "data_categories": [
                "User commands and queries",
                "Calendar context (anonymized)",
                "Anonymized usage patterns",
            ],
            "data_subjects": ["customers"],
            "internal_recipients": ["AI processing service", "Analytics team"],
            "external_recipients": ["LLM API provider"],
            "subprocessors": ["OpenAI / Anthropic / similar"],
            "legal_basis": "consent",
            "legal_basis_details": "User consent for AI features (Article 6.1.a)",
            "retention_period_days": 90,
            "retention_basis": "Query retention for quality assurance",
            "security_measures": [
                "PII removal before external processing",
                "Prompt injection protection",
                "Rate limiting",
                "Content filtering",
            ],
            "encryption_applied": True,
            "pseudonymization_applied": True,
            "involves_transfers": True,
            "transfer_mechanism": "SCCs",
            "transfer_countries": ["United States"],
            "is_active": True,
        },
        "ROP-004": {
            "activity_name": "Booking Management",
            "activity_description": "Process and manage meeting bookings",
            "purposes": [
                "Process meeting requests",
                "Send booking confirmations",
                "Manage calendar conflicts",
            ],
            "data_categories": [
                "Booking details (time, attendees)",
                "Email addresses",
                "Meeting preferences",
            ],
            "data_subjects": ["customers", "prospective customers"],
            "internal_recipients": ["Booking service", "Notification service"],
            "external_recipients": ["Email service provider"],
            "subprocessors": ["SendGrid / Mailgun / similar"],
            "legal_basis": "contract",
            "legal_basis_details": "Service delivery (Article 6.1.b)",
            "retention_period_days": 1095,
            "retention_basis": "Legal obligation for business records",
            "security_measures": [
                "Booking code verification",
                "Rate limiting",
                "Email encryption",
            ],
            "encryption_applied": True,
            "pseudonymization_applied": False,
            "involves_transfers": False,
            "is_active": True,
        },
        "ROP-005": {
            "activity_name": "Email Communication",
            "activity_description": "Send transactional and marketing emails",
            "purposes": [
                "Send booking confirmations",
                "Send reminders",
                "Send marketing communications (with consent)",
            ],
            "data_categories": [
                "Email addresses",
                "User preferences",
            ],
            "data_subjects": ["customers", "prospective customers"],
            "internal_recipients": ["Marketing team", "Customer support"],
            "external_recipients": ["Email service provider"],
            "subprocessors": ["SendGrid / Mailgun / similar"],
            "legal_basis": "consent",
            "legal_basis_details": "Marketing emails require consent (Article 6.1.a), transactional emails are contract (Article 6.1.b)",
            "retention_period_days": 730,
            "retention_basis": "Marketing communication history",
            "security_measures": [
                "Consent tracking",
                "Unsubscribe functionality",
                "Email authentication (SPF, DKIM, DMARC)",
            ],
            "encryption_applied": True,
            "pseudonymization_applied": False,
            "involves_transfers": False,
            "is_active": True,
        },
        "ROP-006": {
            "activity_name": "Analytics and Monitoring",
            "activity_description": "Application performance monitoring and usage analytics",
            "purposes": [
                "Application performance monitoring",
                "Usage analytics",
                "Error tracking",
            ],
            "data_categories": [
                "Anonymized usage patterns",
                "Performance metrics",
                "Error logs (may contain PII)",
            ],
            "data_subjects": ["customers"],
            "internal_recipients": ["Engineering team", "Product team"],
            "external_recipients": ["Monitoring service", "Analytics provider"],
            "subprocessors": ["Sentry / Datadog / Google Analytics"],
            "legal_basis": "legitimate_interest",
            "legal_basis_details": "Service improvement and security monitoring (Article 6.1.f)",
            "retention_period_days": 2555,
            "retention_basis": "Long-term security analysis",
            "security_measures": [
                "PII minimization in logs",
                "Data anonymization",
                "Access controls",
            ],
            "encryption_applied": True,
            "pseudonymization_applied": True,
            "involves_transfers": True,
            "transfer_mechanism": "SCCs",
            "transfer_countries": ["United States"],
            "is_active": True,
        },
    }

    def __init__(self):
        self.activities = self.DEFAULT_ACTIVITIES.copy()

    async def initialize_default_records(self, db: AsyncSession):
        """Initialize default RoPA records in database."""
        for activity_id, activity_data in self.DEFAULT_ACTIVITIES.items():
            stmt = select(DataProcessingRecord).where(
                DataProcessingRecord.activity_id == activity_id
            )
            existing = (await db.execute(stmt)).scalars().first()

            if not existing:
                record = DataProcessingRecord(activity_id=activity_id, **activity_data)
                db.add(record)

        await db.commit()
        logger.info("Default RoPA records initialized")

    async def get_ropa_report(self, db: AsyncSession) -> Dict[str, Any]:
        """Generate RoPA report for GDPR Article 30."""
        stmt = select(DataProcessingRecord).where(
            DataProcessingRecord.is_active == True
        )
        records = (await db.execute(stmt)).scalars().all()

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_controller": "GraftAI Inc.",
            "contact_dpo": "dpo@graftai.com",
            "total_activities": len(records),
            "activities": [],
        }

        for record in records:
            report["activities"].append(
                {
                    "activity_id": record.activity_id,
                    "activity_name": record.activity_name,
                    "activity_description": record.activity_description,
                    "purposes": record.purposes,
                    "data_categories": record.data_categories,
                    "data_subjects": record.data_subjects,
                    "internal_recipients": record.internal_recipients,
                    "external_recipients": record.external_recipients,
                    "subprocessors": record.subprocessors,
                    "legal_basis": record.legal_basis,
                    "legal_basis_details": record.legal_basis_details,
                    "retention_period_days": record.retention_period_days,
                    "retention_basis": record.retention_basis,
                    "security_measures": record.security_measures,
                    "encryption_applied": record.encryption_applied,
                    "pseudonymization_applied": record.pseudonymization_applied,
                    "involves_transfers": record.involves_transfers,
                    "transfer_mechanism": record.transfer_mechanism,
                    "transfer_countries": record.transfer_countries,
                    "last_reviewed_at": record.last_reviewed_at.isoformat()
                    if record.last_reviewed_at
                    else None,
                    "review_notes": record.review_notes,
                }
            )

        return report

    async def add_processing_activity(
        self,
        db: AsyncSession,
        activity_id: str,
        activity_data: Dict[str, Any],
        reviewed_by: Optional[str] = None,
    ) -> DataProcessingRecord:
        """Add a new processing activity to RoPA."""
        stmt = select(DataProcessingRecord).where(
            DataProcessingRecord.activity_id == activity_id
        )
        existing = (await db.execute(stmt)).scalars().first()

        if existing:
            # Update existing
            for key, value in activity_data.items():
                setattr(existing, key, value)
            existing.last_reviewed_at = datetime.now(timezone.utc)
            existing.reviewed_by = reviewed_by
            await db.commit()
            return existing

        record = DataProcessingRecord(
            activity_id=activity_id,
            last_reviewed_at=datetime.now(timezone.utc),
            reviewed_by=reviewed_by,
            **activity_data,
        )
        db.add(record)
        await db.commit()

        logger.info(f"Added RoPA activity: {activity_id}")
        return record

    async def review_activity(
        self,
        db: AsyncSession,
        activity_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None,
    ) -> DataProcessingRecord:
        """Mark a processing activity as reviewed."""
        stmt = select(DataProcessingRecord).where(
            DataProcessingRecord.activity_id == activity_id
        )
        record = (await db.execute(stmt)).scalars().first()

        if not record:
            raise ValueError(f"Activity not found: {activity_id}")

        record.last_reviewed_at = datetime.now(timezone.utc)
        record.reviewed_by = reviewed_by
        record.review_notes = review_notes

        await db.commit()

        logger.info(f"Reviewed RoPA activity: {activity_id}")
        return record


# Global RoPA manager instance
ropa_manager = RoPAManager()
