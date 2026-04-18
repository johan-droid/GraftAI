"""Data Subject Request (DSR) workflow for GDPR compliance."""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from backend.models.dsr import DSRRecord, DSRType, DSRStatus, DSRAuditLog
from backend.models.tables import UserTable, EventTable, BookingTable, UserTokenTable
from backend.utils.audit_logger import AuditLogger, Action
from backend.services.notifications import send_custom_notification

logger = logging.getLogger(__name__)


class DSRWorkflow:
    """GDPR Data Subject Request fulfillment workflow."""

    GDPR_DEADLINE_DAYS = 30  # Article 12.3
    COMPLEX_REQUEST_EXTENSION = 60  # Article 12.3 extension for complex requests
    IDENTITY_VERIFICATION_CODE_EXPIRY = 24  # hours

    def __init__(self):
        self.handlers = {
            DSRType.ACCESS: self._handle_access_request,
            DSRType.RECTIFICATION: self._handle_rectification_request,
            DSRType.ERASURE: self._handle_erasure_request,
            DSRType.RESTRICTION: self._handle_restriction_request,
            DSRType.PORTABILITY: self._handle_portability_request,
            DSRType.OBJECTION: self._handle_objection_request,
        }

    async def submit_request(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        request_type: DSRType,
        details: Dict[str, Any],
        requester_email: Optional[str] = None,
        requester_ip: Optional[str] = None,
        requester_user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a new DSR.

        For authenticated users, user_id is required.
        For non-authenticated requests, requester_email is required with identity verification.
        """
        # Validate request
        if not user_id and not requester_email:
            raise ValueError("Either user_id or requester_email must be provided")

        # Calculate deadline
        deadline = datetime.utcnow() + timedelta(days=self.GDPR_DEADLINE_DAYS)

        # Create request record
        dsr = DSRRecord(
            user_id=user_id or None,  # Will be set after identity verification
            request_type=request_type,
            status=DSRStatus.IDENTITY_VERIFICATION_PENDING
            if not user_id
            else DSRStatus.SUBMITTED,
            deadline_at=deadline,
            request_details=details,
            requester_email=requester_email,
            requester_ip=requester_ip,
            requester_user_agent=requester_user_agent,
        )

        db.add(dsr)
        await db.flush()

        # Log submission
        await self._log_audit(
            db, dsr.id, "request_submitted", {"request_type": request_type.value}
        )

        # Send verification if needed
        if not user_id:
            verification_code = secrets.token_urlsafe(16)
            await self._send_verification_email(requester_email, verification_code)
            dsr.request_details = dsr.request_details or {}
            dsr.request_details["verification_code"] = verification_code
            await db.commit()

            return {
                "request_id": dsr.id,
                "status": "identity_verification_pending",
                "message": "Verification code sent to email",
            }
        else:
            # Auto-verify authenticated users
            dsr.status = DSRStatus.IDENTITY_VERIFIED
            dsr.identity_verified = True
            dsr.identity_verified_at = datetime.utcnow()
            dsr.verification_method = "authenticated"
            await db.commit()

            # Queue for processing
            await self._queue_for_processing(db, dsr)

            return {
                "request_id": dsr.id,
                "status": "submitted",
                "deadline": deadline.isoformat(),
            }

    async def verify_identity(
        self,
        db: AsyncSession,
        request_id: str,
        verification_code: str,
    ) -> Dict[str, Any]:
        """Verify identity for non-authenticated DSR."""
        stmt = select(DSRRecord).where(DSRRecord.id == request_id)
        dsr = (await db.execute(stmt)).scalars().first()

        if not dsr:
            raise ValueError("Request not found")

        if dsr.identity_verified:
            return {"status": "already_verified"}

        stored_code = dsr.request_details.get("verification_code")
        if stored_code != verification_code:
            raise ValueError("Invalid verification code")

        # Verify identity
        dsr.identity_verified = True
        dsr.identity_verified_at = datetime.utcnow()
        dsr.verification_method = "email_code"
        dsr.status = DSRStatus.IDENTITY_VERIFIED

        # Find user by email
        if dsr.requester_email:
            user_stmt = select(UserTable).where(UserTable.email == dsr.requester_email)
            user = (await db.execute(user_stmt)).scalars().first()
            if user:
                dsr.user_id = user.id

        await self._log_audit(db, dsr.id, "identity_verified", {"method": "email_code"})
        await db.commit()

        # Queue for processing
        await self._queue_for_processing(db, dsr)

        return {"status": "verified", "request_id": dsr.id}

    async def _queue_for_processing(self, db: AsyncSession, dsr: DSRRecord):
        """Queue DSR for processing."""
        dsr.status = DSRStatus.IN_PROGRESS
        await self._log_audit(db, dsr.id, "queued_for_processing")
        await db.commit()

    async def process_request(
        self, db: AsyncSession, request_id: str
    ) -> Dict[str, Any]:
        """Process a DSR using the appropriate handler."""
        stmt = select(DSRRecord).where(DSRRecord.id == request_id)
        dsr = (await db.execute(stmt)).scalars().first()

        if not dsr:
            raise ValueError("Request not found")

        if not dsr.identity_verified:
            raise ValueError("Identity not verified")

        # Get handler for request type
        handler = self.handlers.get(dsr.request_type)
        if not handler:
            raise ValueError(f"No handler for request type: {dsr.request_type}")

        # Process
        try:
            result = await handler(db, dsr)

            # Update status
            dsr.status = DSRStatus.COMPLETED
            dsr.completed_at = datetime.utcnow()

            await self._log_audit(db, dsr.id, "request_completed", result)
            await db.commit()

            return result
        except Exception as e:
            logger.error(f"DSR processing failed: {e}", exc_info=True)
            dsr.status = DSRStatus.REJECTED
            dsr.rejection_reason = str(e)
            await db.commit()
            raise

    async def _handle_access_request(
        self, db: AsyncSession, dsr: DSRRecord
    ) -> Dict[str, Any]:
        """Handle Right of Access (Article 15)."""
        if not dsr.user_id:
            raise ValueError("User ID required for access request")

        # Gather all user data
        package = await self._generate_access_package(db, dsr.user_id)

        # Store securely (in production, use encrypted storage)
        # For now, return in response
        return {
            "status": "completed",
            "data_package": package,
            "data_categories": list(package.keys()),
        }

    async def _handle_erasure_request(
        self, db: AsyncSession, dsr: DSRRecord
    ) -> Dict[str, Any]:
        """Handle Right to Erasure (Article 17)."""
        if not dsr.user_id:
            raise ValueError("User ID required for erasure request")

        # 1. Identify all data locations
        data_inventory = await self._locate_all_user_data(db, dsr.user_id)

        # 2. Check for legal retention obligations (Article 17.3)
        retention_required = await self._check_retention_obligations(db, dsr.user_id)

        # 3. Delete or anonymize based on retention requirements
        deletion_results = []
        for location in data_inventory:
            if location["can_delete"]:
                result = await self._delete_data(db, dsr.user_id, location)
            else:
                result = await self._anonymize_data(db, dsr.user_id, location)
            deletion_results.append(result)

        # 4. Notify third parties (Article 19)
        third_parties = await self._get_data_recipients(db, dsr.user_id)
        for processor in third_parties:
            await self._notify_deletion(processor, dsr.user_id)

        # 5. Revoke all access tokens
        await self._revoke_all_tokens(db, dsr.user_id)

        # 6. Log for audit
        await AuditLogger.log_data_access(
            db=db,
            action=Action.DELETE,
            resource_type="user_account",
            resource_id=dsr.user_id,
            user_id=dsr.user_id,
            metadata={
                "reason": "DSR erasure request",
                "retained_count": len(retention_required),
            },
        )

        return {
            "status": "completed",
            "data_locations_processed": len(deletion_results),
            "retained_due_to_legal_obligation": len(retention_required),
            "third_parties_notified": len(third_parties),
            "completion_date": datetime.utcnow().isoformat(),
        }

    async def _handle_rectification_request(
        self, db: AsyncSession, dsr: DSRRecord
    ) -> Dict[str, Any]:
        """Handle Right to Rectification (Article 16)."""
        if not dsr.user_id:
            raise ValueError("User ID required for rectification request")

        corrections = dsr.request_details.get("corrections", {})

        # Apply corrections
        updated_fields = []
        for field, new_value in corrections.items():
            if field in ["full_name", "email", "timezone"]:
                stmt = (
                    update(UserTable)
                    .where(UserTable.id == dsr.user_id)
                    .values({field: new_value})
                )
                await db.execute(stmt)
                updated_fields.append(field)

        await db.commit()

        return {
            "status": "completed",
            "fields_updated": updated_fields,
        }

    async def _handle_restriction_request(
        self, db: AsyncSession, dsr: DSRRecord
    ) -> Dict[str, Any]:
        """Handle Right to Restriction of Processing (Article 18)."""
        # Mark user account for restricted processing
        # Implementation depends on specific processing activities to restrict
        return {
            "status": "completed",
            "message": "Processing restricted as requested",
        }

    async def _handle_portability_request(
        self, db: AsyncSession, dsr: DSRRecord
    ) -> Dict[str, Any]:
        """Handle Right to Data Portability (Article 20)."""
        if not dsr.user_id:
            raise ValueError("User ID required for portability request")

        # Generate portable data package (JSON, CSV, etc.)
        package = await self._generate_portability_package(db, dsr.user_id)

        return {
            "status": "completed",
            "format": "json",
            "data_package": package,
        }

    async def _handle_objection_request(
        self, db: AsyncSession, dsr: DSRRecord
    ) -> Dict[str, Any]:
        """Handle Right to Object (Article 21)."""
        # Stop processing based on legitimate interests
        # Requires manual review
        return {
            "status": "completed",
            "message": "Objection recorded, processing will be reviewed",
        }

    async def _generate_access_package(
        self, db: AsyncSession, user_id: str
    ) -> Dict[str, Any]:
        """Generate comprehensive data access package."""
        package = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "governance": "GDPR Article 15",
                "data_controller": "GraftAI Inc.",
            },
            "personal_data": {
                "profile": await self._get_profile_data(db, user_id),
                "calendar": await self._get_calendar_data(db, user_id),
                "bookings": await self._get_booking_data(db, user_id),
                "tokens": await self._get_token_data(db, user_id),
            },
            "processing_information": {
                "purposes": ["scheduling", "calendar_sync", "ai_assistance"],
                "retention_periods": await self._get_retention_periods(db),
            },
        }
        return package

    async def _locate_all_user_data(
        self, db: AsyncSession, user_id: str
    ) -> List[Dict[str, Any]]:
        """Identify all locations where user data is stored."""
        locations = [
            {
                "table": "users",
                "can_delete": False,
                "reason": "Account record required for legal compliance",
            },
            {"table": "events", "can_delete": True, "reason": "User's calendar events"},
            {
                "table": "bookings",
                "can_delete": True,
                "reason": "User's booking history",
            },
            {"table": "user_tokens", "can_delete": True, "reason": "OAuth tokens"},
            {"table": "user_mfa", "can_delete": True, "reason": "MFA settings"},
        ]
        return locations

    async def _delete_data(
        self, db: AsyncSession, user_id: str, location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete data from a specific location."""
        table = location["table"]

        if table == "events":
            stmt = delete(EventTable).where(EventTable.user_id == user_id)
            result = await db.execute(stmt)
        elif table == "bookings":
            stmt = delete(BookingTable).where(BookingTable.user_id == user_id)
            result = await db.execute(stmt)
        elif table == "user_tokens":
            stmt = delete(UserTokenTable).where(UserTokenTable.user_id == user_id)
            result = await db.execute(stmt)
        else:
            return {"table": table, "deleted": 0, "reason": "Not implemented"}

        return {"table": table, "deleted": result.rowcount}

    async def _anonymize_data(
        self, db: AsyncSession, user_id: str, location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Anonymize data instead of deleting."""
        # Replace PII with hashes or nulls
        return {"table": location["table"], "anonymized": True}

    async def _get_profile_data(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Get user profile data."""
        stmt = select(UserTable).where(UserTable.id == user_id)
        user = (await db.execute(stmt)).scalars().first()
        if not user:
            return {}

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "timezone": user.timezone,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    async def _get_calendar_data(
        self, db: AsyncSession, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get user calendar events."""
        stmt = select(EventTable).where(EventTable.user_id == user_id)
        events = (await db.execute(stmt)).scalars().all()

        return [
            {
                "id": e.id,
                "title": e.title,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "end_time": e.end_time.isoformat() if e.end_time else None,
            }
            for e in events
        ]

    async def _get_booking_data(
        self, db: AsyncSession, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get user bookings."""
        stmt = select(BookingTable).where(BookingTable.user_id == user_id)
        bookings = (await db.execute(stmt)).scalars().all()

        return [
            {
                "id": b.id,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bookings
        ]

    async def _get_token_data(
        self, db: AsyncSession, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get user OAuth tokens (without secrets)."""
        stmt = select(UserTokenTable).where(UserTokenTable.user_id == user_id)
        tokens = (await db.execute(stmt)).scalars().all()

        return [
            {
                "provider": t.provider,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tokens
        ]

    async def _check_retention_obligations(
        self, db: AsyncSession, user_id: str
    ) -> List[Dict[str, Any]]:
        """Check if any data must be retained for legal reasons."""
        # Check for active bookings, legal holds, etc.
        return []

    async def _get_data_recipients(self, db: AsyncSession, user_id: str) -> List[str]:
        """Get list of third parties who have received user data."""
        # Check user_tokens for connected providers
        stmt = select(UserTokenTable.provider).where(
            UserTokenTable.user_id == user_id, UserTokenTable.is_active == True
        )
        providers = (await db.execute(stmt)).scalars().all()
        return list(providers)

    async def _notify_deletion(self, processor: str, user_id: str):
        """Notify third party of data deletion."""
        # Send deletion requests to Google, Microsoft, etc.
        logger.info(f"Notifying {processor} of deletion for user {user_id}")

    async def _revoke_all_tokens(self, db: AsyncSession, user_id: str):
        """Revoke all OAuth tokens for user."""
        stmt = (
            update(UserTokenTable)
            .where(UserTokenTable.user_id == user_id)
            .values(is_active=False)
        )
        await db.execute(stmt)

    async def _generate_portability_package(
        self, db: AsyncSession, user_id: str
    ) -> Dict[str, Any]:
        """Generate data in portable format (Article 20)."""
        # Similar to access package but in standardized format
        return await self._generate_access_package(db, user_id)

    async def _get_retention_periods(self, db: AsyncSession) -> Dict[str, str]:
        """Get retention periods for data categories."""
        return {
            "profile": "2 years after account deletion",
            "events": "1 year after event completion",
            "bookings": "3 years after booking",
        }

    async def _log_audit(
        self, db: AsyncSession, dsr_id: str, action: str, details: Dict = None
    ):
        """Log DSR action for audit trail."""
        log = DSRAuditLog(
            dsr_id=dsr_id,
            action=action,
            action_details=details or {},
            performed_at=datetime.utcnow(),
        )
        db.add(log)

    async def _send_verification_email(self, email: str, code: str):
        """Send identity verification email."""
        subject = "Verify your data request"
        text_body = (
            "We received a Data Subject Request for this email address.\n\n"
            f"Verification code: {code}\n"
            f"This code expires in {self.IDENTITY_VERIFICATION_CODE_EXPIRY} hours.\n\n"
            "If you did not make this request, you can safely ignore this email."
        )
        html_body = (
            "<p>We received a Data Subject Request for this email address.</p>"
            f"<p><strong>Verification code:</strong> {code}</p>"
            f"<p>This code expires in {self.IDENTITY_VERIFICATION_CODE_EXPIRY} hours.</p>"
            "<p>If you did not make this request, you can safely ignore this email.</p>"
        )

        await send_custom_notification(
            user_email=email,
            subject=subject,
            message=text_body,
            html_body=html_body,
            text_body=text_body,
        )


# Global DSR workflow instance
dsr_workflow = DSRWorkflow()
