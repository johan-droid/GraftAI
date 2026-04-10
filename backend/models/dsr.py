"""Data Subject Request (DSR) models for GDPR compliance."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from backend.models.base import Base, generate_uuid


class DSRType(str, Enum):
    """GDPR Data Subject Request types (Articles 15-22)."""
    ACCESS = "access"                    # Article 15 - Right of Access
    RECTIFICATION = "rectification"      # Article 16 - Right to Rectification
    ERASURE = "erasure"                  # Article 17 - Right to Erasure (Right to be Forgotten)
    RESTRICTION = "restriction"          # Article 18 - Right to Restriction of Processing
    PORTABILITY = "portability"          # Article 20 - Right to Data Portability
    OBJECTION = "objection"              # Article 21 - Right to Object


class DSRStatus(str, Enum):
    """DSR processing status."""
    SUBMITTED = "submitted"
    IDENTITY_VERIFICATION_PENDING = "identity_verification_pending"
    IDENTITY_VERIFIED = "identity_verified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXTENDED = "extended"  # Complex request, deadline extended


class DSRRecord(Base):
    """Data Subject Request record for GDPR compliance."""
    __tablename__ = "dsr_records"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    
    # Request details
    request_type = Column(SQLEnum(DSRType), nullable=False)
    status = Column(SQLEnum(DSRStatus), default=DSRStatus.SUBMITTED)
    
    # Request metadata
    submitted_at = Column(DateTime, default=datetime.utcnow)
    deadline_at = Column(DateTime, nullable=False)  # 30 days from submission
    completed_at = Column(DateTime, nullable=True)
    
    # Identity verification
    identity_verified = Column(Boolean, default=False)
    identity_verified_at = Column(DateTime, nullable=True)
    verification_method = Column(String(50), nullable=True)  # email, mfa, document
    
    # Request details
    request_details = Column(JSON, default=dict)  # Specific data categories, date ranges, etc.
    rejection_reason = Column(Text, nullable=True)
    extension_reason = Column(Text, nullable=True)
    
    # Processing tracking
    processing_log = Column(JSON, default=list)  # Audit trail of actions taken
    data_locations_processed = Column(Integer, default=0)
    third_parties_notified = Column(Integer, default=0)
    
    # Response data
    response_data_url = Column(String(500), nullable=True)  # Secure download URL
    response_expires_at = Column(DateTime, nullable=True)
    
    # Contact information for non-authenticated requests
    requester_email = Column(String(255), nullable=True)
    requester_ip = Column(String(45), nullable=True)
    requester_user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("UserTable", back_populates="dsr_requests")
    
    @property
    def is_overdue(self) -> bool:
        """Check if request is past deadline."""
        if self.status in [DSRStatus.COMPLETED, DSREcho.REJECTED, DSRStatus.CANCELLED]:
            return False
        return datetime.utcnow() > self.deadline_at
    
    @property
    def days_remaining(self) -> int:
        """Days remaining until deadline."""
        if self.status in [DSRStatus.COMPLETED, DSRStatus.REJECTED, DSRStatus.CANCELLED]:
            return 0
        delta = self.deadline_at - datetime.utcnow()
        return max(0, delta.days)


class DSRAuditLog(Base):
    """Audit log for DSR processing."""
    __tablename__ = "dsr_audit_logs"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    dsr_id = Column(String(100), ForeignKey("dsr_records.id"), nullable=False, index=True)
    
    action = Column(String(100), nullable=False)  # verify_identity, locate_data, delete_data, etc.
    action_details = Column(JSON, default=dict)
    performed_by = Column(String(100), nullable=True)  # User ID or 'system'
    performed_at = Column(DateTime, default=datetime.utcnow)
    
    # For data modifications
    data_location = Column(String(200), nullable=True)
    records_affected = Column(Integer, nullable=True)
    
    # Compliance tracking
    gdpr_article = Column(String(10), nullable=True)  # Article reference


class DataRetentionSchedule(Base):
    """Data retention schedule for GDPR Article 5.1.e compliance."""
    __tablename__ = "data_retention_schedules"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    
    # Data category
    data_category = Column(String(100), nullable=False, unique=True)
    data_types = Column(JSON, default=list)  # Specific data fields
    
    # Retention policy
    retention_days = Column(Integer, nullable=False)
    retention_basis = Column(String(50), nullable=False)  # legal_obligation, contract, consent, legitimate_interest
    legal_basis_details = Column(Text, nullable=True)
    
    # Action after retention period
    action_after_retention = Column(String(50), default="delete")  # delete, anonymize, archive
    
    # Automation settings
    auto_apply = Column(Boolean, default=True)
    last_applied_at = Column(DateTime, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConsentRecord(Base):
    """Granular consent records for GDPR Article 6/7 compliance."""
    __tablename__ = "consent_records"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    
    # Consent categories
    essential = Column(Boolean, default=True)  # Required, cannot be withdrawn
    analytics = Column(Boolean, default=False)
    marketing = Column(Boolean, default=False)
    ai_training = Column(Boolean, default=False)
    third_party_sharing = Column(Boolean, default=False)
    
    # Consent metadata
    consent_version = Column(String(10), default="1.0")
    consented_at = Column(DateTime, nullable=True)
    consent_ip = Column(String(45), nullable=True)
    consent_user_agent = Column(Text, nullable=True)
    
    # Withdrawal tracking
    withdrawn_at = Column(DateTime, nullable=True)
    withdrawal_reason = Column(Text, nullable=True)
    
    # Individual category withdrawal dates
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
            return True  # Always required
        
        if not self.is_valid:
            return False
        
        category_attr = getattr(self, category, False)
        withdrawal_attr = getattr(self, f"{category}_withdrawn_at", None)
        
        return category_attr and withdrawal_attr is None


class DataProcessingRecord(Base):
    """Records of Processing Activities (RoPA) for GDPR Article 30 compliance."""
    __tablename__ = "data_processing_records"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    
    # Activity identification
    activity_id = Column(String(20), unique=True, nullable=False)
    activity_name = Column(String(200), nullable=False)
    activity_description = Column(Text, nullable=True)
    
    # Processing details
    purposes = Column(JSON, default=list)
    data_categories = Column(JSON, default=list)
    data_subjects = Column(JSON, default=list)
    
    # Recipients
    internal_recipients = Column(JSON, default=list)
    external_recipients = Column(JSON, default=list)
    subprocessors = Column(JSON, default=list)
    
    # Legal basis
    legal_basis = Column(String(50), nullable=False)  # consent, contract, legal_obligation, etc.
    legal_basis_details = Column(Text, nullable=True)
    
    # Retention
    retention_period_days = Column(Integer, nullable=True)
    retention_basis = Column(Text, nullable=True)
    
    # Security measures
    security_measures = Column(JSON, default=list)
    encryption_applied = Column(Boolean, default=False)
    pseudonymization_applied = Column(Boolean, default=False)
    
    # International transfers
    involves_transfers = Column(Boolean, default=False)
    transfer_mechanism = Column(String(50), nullable=True)  # SCCs, adequacy_decision, BCRs
    transfer_countries = Column(JSON, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)


class DataBreachRecord(Base):
    """Data breach records for GDPR Articles 33-34 compliance."""
    __tablename__ = "data_breach_records"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    
    # Breach identification
    breach_reference = Column(String(50), unique=True, nullable=False)
    discovered_at = Column(DateTime, nullable=False)
    reported_at = Column(DateTime, nullable=True)
    
    # Breach details
    nature_of_breach = Column(Text, nullable=False)
    data_categories = Column(JSON, default=list)
    data_subjects_affected = Column(Integer, nullable=True)
    approximate_subjects = Column(String(50), nullable=True)  # <100, 100-1000, 1000-10000, >10000
    
    # Risk assessment
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    likely_consequences = Column(Text, nullable=True)
    special_category_data = Column(Boolean, default=False)
    children_affected = Column(Boolean, default=False)
    
    # Measures taken
    containment_measures = Column(JSON, default=list)
    remediation_actions = Column(JSON, default=list)
    
    # Notifications
    supervisory_notified = Column(Boolean, default=False)
    supervisory_notified_at = Column(DateTime, nullable=True)
    supervisory_authority = Column(String(100), nullable=True)  # DPC, ICO, etc.
    
    data_subjects_notified = Column(Boolean, default=False)
    data_subjects_notified_at = Column(DateTime, nullable=True)
    notification_method = Column(String(50), nullable=True)  # email, direct, public
    
    # Third parties
    subprocessors_notified = Column(JSON, default=list)
    
    # Status
    status = Column(String(50), default="investigating")  # investigating, contained, remediated, closed
    closed_at = Column(DateTime, nullable=True)
    
    # DPO involvement
    dpo_consulted = Column(Boolean, default=False)
    dpo_recommendations = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
