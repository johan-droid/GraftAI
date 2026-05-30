"""Data Subject Request (DSR) models for GDPR compliance."""
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from backend.models.base import Base, generate_uuid


class DSRType(StrEnum):
    """GDPR Data Subject Request types (Articles 15-22)."""
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICTION = "restriction"
    PORTABILITY = "portability"
    OBJECTION = "objection"

class DSRStatus(StrEnum):
    """DSR processing status."""
    SUBMITTED = "submitted"
    IDENTITY_VERIFICATION_PENDING = "identity_verification_pending"
    IDENTITY_VERIFIED = "identity_verified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXTENDED = "extended"

class DSRRecord(Base):
    """Data Subject Request record for GDPR compliance."""
    __tablename__ = "dsr_records"
    id = Column(String(100), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=True, index=True)
    request_type = Column(SQLEnum(DSRType), nullable=False)
    status = Column(SQLEnum(DSRStatus), default=DSRStatus.SUBMITTED)
    submitted_at = Column(DateTime, default=lambda: datetime.now(UTC))
    deadline_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    identity_verified = Column(Boolean, default=False)
    identity_verified_at = Column(DateTime, nullable=True)
    verification_method = Column(String(50), nullable=True)
    request_details = Column(JSON, default=dict)
    rejection_reason = Column(Text, nullable=True)
    extension_reason = Column(Text, nullable=True)
    processing_log = Column(JSON, default=list)
    data_locations_processed = Column(Integer, default=0)
    third_parties_notified = Column(Integer, default=0)
    response_data_url = Column(String(500), nullable=True)
    response_expires_at = Column(DateTime, nullable=True)
    requester_email = Column(String(255), nullable=True)
    requester_ip = Column(String(45), nullable=True)
    requester_user_agent = Column(Text, nullable=True)
    user = relationship("UserTable", back_populates="dsr_requests")

    @property
    def is_overdue(self) -> bool:
        """Check if request is past deadline."""
        if self.status in [DSRStatus.COMPLETED, DSRStatus.REJECTED, DSRStatus.CANCELLED]:
            return False
        return datetime.now(UTC) > self.deadline_at

    @property
    def days_remaining(self) -> int:
        """Days remaining until deadline."""
        if self.status in [DSRStatus.COMPLETED, DSRStatus.REJECTED, DSRStatus.CANCELLED]:
            return 0
        delta = self.deadline_at - datetime.now(UTC)
        return max(0, delta.days)

class DSRAuditLog(Base):
    """Audit log for DSR processing."""
    __tablename__ = "dsr_audit_logs"
    id = Column(String(100), primary_key=True, default=generate_uuid)
    dsr_id = Column(String(100), ForeignKey("dsr_records.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    action_details = Column(JSON, default=dict)
    performed_by = Column(String(100), nullable=True)
    performed_at = Column(DateTime, default=lambda: datetime.now(UTC))
    data_location = Column(String(200), nullable=True)
    records_affected = Column(Integer, nullable=True)
    gdpr_article = Column(String(10), nullable=True)

class DataRetentionSchedule(Base):
    """Data retention schedule for GDPR Article 5.1.e compliance."""
    __tablename__ = "data_retention_schedules"
    id = Column(String(100), primary_key=True, default=generate_uuid)
    data_category = Column(String(100), nullable=False, unique=True)
    data_types = Column(JSON, default=list)
    retention_days = Column(Integer, nullable=False)
    retention_basis = Column(String(50), nullable=False)
    legal_basis_details = Column(Text, nullable=True)
    action_after_retention = Column(String(50), default="delete")
    auto_apply = Column(Boolean, default=True)
    last_applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class ConsentRecord(Base):
    """Granular consent records for GDPR Article 6/7 compliance."""
    __tablename__ = "consent_records"
    id = Column(String(100), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    essential = Column(Boolean, default=True)
    analytics = Column(Boolean, default=False)
    marketing = Column(Boolean, default=False)
    ai_training = Column(Boolean, default=False)
    third_party_sharing = Column(Boolean, default=False)
    consent_version = Column(String(10), default="1.0")
    consented_at = Column(DateTime, nullable=True)
    consent_ip = Column(String(45), nullable=True)
    consent_user_agent = Column(Text, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)
    withdrawal_reason = Column(Text, nullable=True)
    analytics_withdrawn_at = Column(DateTime, nullable=True)
    marketing_withdrawn_at = Column(DateTime, nullable=True)
    ai_training_withdrawn_at = Column(DateTime, nullable=True)
    third_party_sharing_withdrawn_at = Column(DateTime, nullable=True)
    user = relationship("UserTable", back_populates="consent_records")

    @property
    def is_valid(self) -> bool:
        """Check if consent is valid (not fully withdrawn)."""
        return self.consented_at is not None and self.withdrawn_at is None

    def has_consent(self, category: str) -> bool:
        """Check if user has given consent for a specific category."""
        if category == "essential":
            return True
        if not self.is_valid:
            return False
        category_attr = getattr(self, category, False)
        withdrawal_attr = getattr(self, f"{category}_withdrawn_at", None)
        return category_attr and withdrawal_attr is None

class DataProcessingRecord(Base):
    """Records of Processing Activities (RoPA) for GDPR Article 30 compliance."""
    __tablename__ = "data_processing_records"
    id = Column(String(100), primary_key=True, default=generate_uuid)
    activity_id = Column(String(20), unique=True, nullable=False)
    activity_name = Column(String(200), nullable=False)
    activity_description = Column(Text, nullable=True)
    purposes = Column(JSON, default=list)
    data_categories = Column(JSON, default=list)
    data_subjects = Column(JSON, default=list)
    internal_recipients = Column(JSON, default=list)
    external_recipients = Column(JSON, default=list)
    subprocessors = Column(JSON, default=list)
    legal_basis = Column(String(50), nullable=False)
    legal_basis_details = Column(Text, nullable=True)
    retention_period_days = Column(Integer, nullable=True)
    retention_basis = Column(Text, nullable=True)
    security_measures = Column(JSON, default=list)
    encryption_applied = Column(Boolean, default=False)
    pseudonymization_applied = Column(Boolean, default=False)
    involves_transfers = Column(Boolean, default=False)
    transfer_mechanism = Column(String(50), nullable=True)
    transfer_countries = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    last_reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    review_notes = Column(Text, nullable=True)

class DataBreachRecord(Base):
    """Data breach records for GDPR Articles 33-34 compliance."""
    __tablename__ = "data_breach_records"
    id = Column(String(100), primary_key=True, default=generate_uuid)
    breach_reference = Column(String(50), unique=True, nullable=False)
    discovered_at = Column(DateTime, nullable=False)
    reported_at = Column(DateTime, nullable=True)
    nature_of_breach = Column(Text, nullable=False)
    data_categories = Column(JSON, default=list)
    data_subjects_affected = Column(Integer, nullable=True)
    approximate_subjects = Column(String(50), nullable=True)
    risk_level = Column(String(20), nullable=False)
    likely_consequences = Column(Text, nullable=True)
    special_category_data = Column(Boolean, default=False)
    children_affected = Column(Boolean, default=False)
    containment_measures = Column(JSON, default=list)
    remediation_actions = Column(JSON, default=list)
    supervisory_notified = Column(Boolean, default=False)
    supervisory_notified_at = Column(DateTime, nullable=True)
    supervisory_authority = Column(String(100), nullable=True)
    data_subjects_notified = Column(Boolean, default=False)
    data_subjects_notified_at = Column(DateTime, nullable=True)
    notification_method = Column(String(50), nullable=True)
    subprocessors_notified = Column(JSON, default=list)
    status = Column(String(50), default="investigating")
    closed_at = Column(DateTime, nullable=True)
    dpo_consulted = Column(Boolean, default=False)
    dpo_recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
