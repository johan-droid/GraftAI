import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base # Re-using central Base for consistency

# Type hints for forward references
if TYPE_CHECKING:
    from backend.models.dsr import DSRRecord, ConsentRecord
    from backend.models.team import TeamMember
    from backend.models.api_key import APIKey
    from backend.models.integration import Integration
    from backend.models.email_template import EmailTemplate
    from backend.models.video_conference import VideoConferenceConfig
    from backend.models.resource import Resource, ResourceBooking
    from backend.models.automation import AutomationRule

def generate_uuid():
    return str(uuid.uuid4())


def generate_booking_code() -> str:
    return uuid.uuid4().hex[:10].upper()

class UserTable(Base):
    """Core user account. Stripped of complex multi-tenant organization IDs."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String, nullable=True, default="UTC")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email_verification_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    
    # Billing & Quota Fields
    tier: Mapped[str] = mapped_column(String, default="free", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String, default="inactive", nullable=False)
    razorpay_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    razorpay_subscription_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    daily_ai_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_ai_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    daily_sync_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_sync_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    trial_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Relationships
    tokens: Mapped[List["UserTokenTable"]] = relationship("UserTokenTable", back_populates="user", cascade="all, delete-orphan")
    events: Mapped[List["EventTable"]] = relationship("EventTable", back_populates="user", cascade="all, delete-orphan")
    event_types: Mapped[List["EventTypeTable"]] = relationship("EventTypeTable", back_populates="user", cascade="all, delete-orphan")
    team_event_type_memberships: Mapped[List["EventTypeTeamMemberTable"]] = relationship(
        "EventTypeTeamMemberTable",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[List["BookingTable"]] = relationship("BookingTable", back_populates="user", cascade="all, delete-orphan")
    webhooks: Mapped[List["WebhookSubscriptionTable"]] = relationship("WebhookSubscriptionTable", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["NotificationTable"]] = relationship("NotificationTable", back_populates="user", cascade="all, delete-orphan")
    mfa_settings: Mapped[List["UserMFATable"]] = relationship("UserMFATable", back_populates="user", cascade="all, delete-orphan")
    dsr_requests: Mapped[List["DSRRecord"]] = relationship("DSRRecord", back_populates="user", cascade="all, delete-orphan")
    consent_records: Mapped[List["ConsentRecord"]] = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")
    team_memberships: Mapped[List["TeamMember"]] = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[List["APIKey"]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    integrations: Mapped[List["Integration"]] = relationship("Integration", back_populates="user", cascade="all, delete-orphan")
    email_templates: Mapped[List["EmailTemplate"]] = relationship("EmailTemplate", back_populates="user", cascade="all, delete-orphan")
    video_conference_configs: Mapped[List["VideoConferenceConfig"]] = relationship("VideoConferenceConfig", back_populates="user", cascade="all, delete-orphan")
    owned_resources: Mapped[List["Resource"]] = relationship("Resource", back_populates="owner", cascade="all, delete-orphan")
    resource_bookings: Mapped[List["ResourceBooking"]] = relationship("ResourceBooking", back_populates="user")
    automation_rules: Mapped[List["AutomationRule"]] = relationship("AutomationRule", back_populates="user", cascade="all, delete-orphan")


class UserTokenTable(Base):
    """Holds OAuth tokens for Google Calendar / MS Graph."""
    __tablename__ = "user_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 'google' or 'microsoft'
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="tokens")


class NotificationTable(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="notifications")


class EventTable(Base):
    """Unified table for both local schedule blocks and external synced events."""
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    meeting_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_meeting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meeting_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    attendees: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String, nullable=False, index=True)
    is_reminded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="events")
    event_type: Mapped[Optional["EventTypeTable"]]= relationship("EventTypeTable", back_populates="events")
    booking: Mapped[Optional["BookingTable"]]= relationship("BookingTable", back_populates="event", uselist=False)


class BookingTable(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("user_id", "start_time", "end_time", name="uq_bookings_user_start_end"),
        Index("ix_bookings_user_start_time", "user_id", "start_time"),
        Index("ix_bookings_booking_code", "booking_code"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    event_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    booking_code: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=generate_booking_code)
    time_zone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="confirmed")
    is_reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    questions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="bookings")
    event_type: Mapped[Optional["EventTypeTable"]] = relationship("EventTypeTable")
    event: Mapped[Optional["EventTable"]] = relationship("EventTable", back_populates="booking")


class WebhookSubscriptionTable(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    events: Mapped[dict] = mapped_column(JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    external_subscription_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    client_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_triggered: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="webhooks")
    logs: Mapped[List["WebhookLogTable"]] = relationship("WebhookLogTable", back_populates="webhook", cascade="all, delete-orphan")


class WebhookLogTable(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    webhook_id: Mapped[str] = mapped_column(String, ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    event: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    webhook: Mapped["WebhookSubscriptionTable"] = relationship("WebhookSubscriptionTable", back_populates="logs")


class EventTypeTable(Base):
    __tablename__ = "event_types"
    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_user_event_type_slug"),
        Index("ix_event_types_user_slug", "user_id", "slug"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    meeting_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    buffer_before_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    buffer_after_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minimum_notice_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    availability: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    exceptions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_questions: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    requires_attendee_confirmation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    travel_time_before_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    travel_time_after_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requires_payment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payment_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    payment_currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    team_assignment_method: Mapped[str] = mapped_column(String, default="host_only", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="event_types")
    events: Mapped[List["EventTable"]] = relationship("EventTable", back_populates="event_type", cascade="all, delete-orphan")
    team_members: Mapped[List["EventTypeTeamMemberTable"]] = relationship(
        "EventTypeTeamMemberTable",
        back_populates="event_type",
        cascade="all, delete-orphan",
    )


class EventTypeTeamMemberTable(Base):
    __tablename__ = "event_type_team_members"
    __table_args__ = (
        UniqueConstraint("event_type_id", "user_id", name="uq_event_type_team_member"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    event_type_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("event_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_method: Mapped[str] = mapped_column(String, default="host_only", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    event_type: Mapped["EventTypeTable"] = relationship("EventTypeTable", back_populates="team_members")
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="team_event_type_memberships")


class UserMFATable(Base):
    """Multi-factor authentication settings for users (TOTP)."""
    __tablename__ = "user_mfa"
    __table_args__ = (
        Index("ix_user_mfa_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mfa_type: Mapped[str] = mapped_column(String, nullable=False, default="totp")  # 'totp', 'backup_codes'
    secret: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Encrypted TOTP secret
    backup_codes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Hashed backup codes
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="mfa_settings")


class AuditLogTable(Base):
    """Audit log for security and compliance events (SOC 2)."""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_event_type", "event_type"),
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_ip_address", "ip_address"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    
    # Event classification
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(30), nullable=False)  # 'authentication', 'authorization', 'data_access', 'system'
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="info")  # 'info', 'warning', 'error', 'critical'
    
    # Actor information
    user_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("users.id"), nullable=True, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Action details
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # 'login', 'logout', 'create', 'update', 'delete', 'view'
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user', 'calendar', 'event', 'booking'
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Result
    result: Mapped[str] = mapped_column(String(10), nullable=False, default="success")  # 'success', 'failure', 'denied'
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional context (JSON)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Compliance tracking
    compliance_standards: Mapped[list] = mapped_column(JSON, default=list)  # ['SOC2', 'GDPR', 'HIPAA']
    
    # Data for GDPR Article 30 (Records of Processing)
    data_subjects_affected: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_categories: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
