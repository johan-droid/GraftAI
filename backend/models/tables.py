import json
import logging
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
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from .base import Base  # Re-using central Base for consistency


logger = logging.getLogger(__name__)

# Type hints for forward references
if TYPE_CHECKING:
    from backend.models.dsr import DSRRecord, ConsentRecord
    from backend.models.team import Team, TeamMember
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
    username: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, default="UTC"
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_code: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    email_verification_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Billing & Quota Fields
    tier: Mapped[str] = mapped_column(String, default="free", nullable=False)
    subscription_status: Mapped[str] = mapped_column(
        String, default="inactive", nullable=False
    )

    # Razorpay (India payments)
    razorpay_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    razorpay_subscription_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )

    # Stripe (International payments) - separate columns to prevent ID collision
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    daily_ai_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_ai_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    daily_sync_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_sync_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    trial_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Relationships
    tokens: Mapped[List["UserTokenTable"]] = relationship(
        "UserTokenTable", back_populates="user", cascade="all, delete-orphan"
    )
    events: Mapped[List["EventTable"]] = relationship(
        "EventTable", back_populates="user", cascade="all, delete-orphan"
    )
    event_types: Mapped[List["EventTypeTable"]] = relationship(
        "EventTypeTable", back_populates="user", cascade="all, delete-orphan"
    )
    team_event_type_memberships: Mapped[List["EventTypeTeamMemberTable"]] = (
        relationship(
            "EventTypeTeamMemberTable",
            back_populates="user",
            cascade="all, delete-orphan",
        )
    )
    bookings: Mapped[List["BookingTable"]] = relationship(
        "BookingTable", back_populates="user", cascade="all, delete-orphan"
    )
    webhooks: Mapped[List["WebhookSubscriptionTable"]] = relationship(
        "WebhookSubscriptionTable", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["NotificationTable"]] = relationship(
        "NotificationTable", back_populates="user", cascade="all, delete-orphan"
    )
    mfa_settings: Mapped[List["UserMFATable"]] = relationship(
        "UserMFATable", back_populates="user", cascade="all, delete-orphan"
    )
    dsr_requests: Mapped[List["DSRRecord"]] = relationship(
        "DSRRecord", back_populates="user", cascade="all, delete-orphan"
    )
    consent_records: Mapped[List["ConsentRecord"]] = relationship(
        "ConsentRecord", back_populates="user", cascade="all, delete-orphan"
    )
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember", back_populates="user", cascade="all, delete-orphan"
    )
    integrations: Mapped[List["Integration"]] = relationship(
        "Integration", back_populates="user", cascade="all, delete-orphan"
    )
    email_templates: Mapped[List["EmailTemplate"]] = relationship(
        "EmailTemplate", back_populates="user", cascade="all, delete-orphan"
    )
    video_conference_configs: Mapped[List["VideoConferenceConfig"]] = relationship(
        "VideoConferenceConfig", back_populates="user", cascade="all, delete-orphan"
    )
    owned_resources: Mapped[List["Resource"]] = relationship(
        "Resource", back_populates="owner", cascade="all, delete-orphan"
    )
    resource_bookings: Mapped[List["ResourceBooking"]] = relationship(
        "ResourceBooking", back_populates="user"
    )
    automation_rules: Mapped[List["AutomationRule"]] = relationship(
        "AutomationRule", back_populates="user", cascade="all, delete-orphan"
    )


class UserTokenTable(Base):
    """Holds OAuth tokens for Google Calendar / MS Graph."""

    __tablename__ = "user_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String, nullable=False
    )  # e.g., 'google' or 'microsoft'
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="tokens")


class NotificationTable(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["UserTable"] = relationship(
        "UserTable", back_populates="notifications"
    )


class EventTable(Base):
    """Unified table for both local schedule blocks and external synced events."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("event_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="events")
    event_type: Mapped[Optional["EventTypeTable"]] = relationship(
        "EventTypeTable", back_populates="events"
    )
    booking: Mapped[Optional["BookingTable"]] = relationship(
        "BookingTable", back_populates="event", uselist=False
    )


class BookingTable(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "start_time", "end_time", name="uq_bookings_user_start_end"
        ),
        Index("ix_bookings_user_start_time", "user_id", "start_time"),
        Index("ix_bookings_booking_code", "booking_code"),
        Index("ix_bookings_automation_status", "automation_status"),
        Index("ix_bookings_automation_run_at", "automation_run_at"),
        Index("ix_bookings_decision_score", "decision_score"),
        Index("ix_bookings_risk_level", "risk_level"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("event_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    booking_code: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, default=generate_booking_code
    )
    time_zone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="confirmed")
    is_reminder_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    questions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # AI Automation tracking fields
    automation_status: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, default="pending"
    )
    automation_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decision_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="bookings")
    event_type: Mapped[Optional["EventTypeTable"]] = relationship("EventTypeTable")
    event: Mapped[Optional["EventTable"]] = relationship(
        "EventTable", back_populates="booking"
    )


class WebhookSubscriptionTable(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    events: Mapped[dict] = mapped_column(JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    external_subscription_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, index=True
    )
    client_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_triggered: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="webhooks")
    logs: Mapped[List["WebhookLogTable"]] = relationship(
        "WebhookLogTable", back_populates="webhook", cascade="all, delete-orphan"
    )


class WebhookLogTable(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    webhook_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    webhook: Mapped["WebhookSubscriptionTable"] = relationship(
        "WebhookSubscriptionTable", back_populates="logs"
    )


class EventTypeTable(Base):
    __tablename__ = "event_types"
    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_user_event_type_slug"),
        Index("ix_event_types_user_slug", "user_id", "slug"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3b82f6")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    meeting_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    buffer_before_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    buffer_after_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minimum_notice_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    availability: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    exceptions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_questions: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    requires_attendee_confirmation: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    travel_time_before_minutes: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    travel_time_after_minutes: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    requires_payment: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    payment_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    payment_currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    team_assignment_method: Mapped[str] = mapped_column(
        String, default="host_only", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="event_types")
    events: Mapped[List["EventTable"]] = relationship(
        "EventTable", back_populates="event_type", cascade="all, delete-orphan"
    )
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
    assignment_method: Mapped[str] = mapped_column(
        String, default="host_only", nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    event_type: Mapped["EventTypeTable"] = relationship(
        "EventTypeTable", back_populates="team_members"
    )
    user: Mapped["UserTable"] = relationship(
        "UserTable", back_populates="team_event_type_memberships"
    )


class UserMFATable(Base):
    """Multi-factor authentication settings for users (TOTP)."""

    __tablename__ = "user_mfa"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mfa_type: Mapped[str] = mapped_column(
        String, nullable=False, default="totp"
    )  # 'totp', 'backup_codes'
    secret: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Encrypted TOTP secret
    backup_codes: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Hashed backup codes
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Event classification
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # 'authentication', 'authorization', 'data_access', 'system'
    severity: Mapped[str] = mapped_column(
        String(10), nullable=False, default="info"
    )  # 'info', 'warning', 'error', 'critical'

    # Actor information
    user_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("users.id"), nullable=True, index=True
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, index=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Action details
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'login', 'logout', 'create', 'update', 'delete', 'view'
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'user', 'calendar', 'event', 'booking'
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Result
    result: Mapped[str] = mapped_column(
        String(10), nullable=False, default="success"
    )  # 'success', 'failure', 'denied'
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional context (JSON)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSON, nullable=True
    )

    # Compliance tracking
    compliance_standards: Mapped[list] = mapped_column(
        JSON, default=list
    )  # ['SOC2', 'GDPR', 'HIPAA']

    # Data for GDPR Article 30 (Records of Processing)
    data_subjects_affected: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    data_categories: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class ManualActivationRequestTable(Base):
    """Manual activation requests for users who cannot complete automated payments.

    Allows users (students) to request a paid tier upgrade which an admin
    (or parent) can approve manually after reviewing proof.
    """

    __tablename__ = "manual_activation_requests"
    __table_args__ = (
        Index("ix_manual_activation_requests_user_id", "user_id"),
        Index("ix_manual_activation_requests_status", "status"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    requested_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pro"
    )
    proof_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, approved, rejected
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["UserTable"] = relationship(
        "UserTable", foreign_keys=[user_id], backref="manual_activation_requests"
    )
    reviewer: Mapped[Optional["UserTable"]] = relationship(
        "UserTable", foreign_keys=[reviewed_by]
    )


class ChatMessageTable(Base):
    """AI Copilot chat messages for conversation history and context."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("users.id"), nullable=False, index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped["UserTable"] = relationship("UserTable", backref="chat_messages")


class TeamMembershipTable(Base):
    """Team membership with role-based access (OWNER, ADMIN, MEMBER)."""

    __tablename__ = "team_memberships"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=generate_uuid
    )
    team_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("teams.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("users.id"), nullable=False, index=True
    )

    # Role: OWNER, ADMIN, MEMBER
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="MEMBER")

    # Invitation status
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    invited_by: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("users.id"), nullable=True
    )
    invite_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    invite_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["UserTable"] = relationship("UserTable", foreign_keys=[user_id])
    inviter: Mapped[Optional["UserTable"]] = relationship(
        "UserTable", foreign_keys=[invited_by]
    )


class WorkflowTable(Base):
    """Workflows for automated sequences."""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("users.id"), nullable=True, index=True
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("teams.id"), nullable=True, index=True
    )
    event_type_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("event_types.id"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Trigger: BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_RESCHEDULED, etc.
    trigger: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional["UserTable"]] = relationship("UserTable", backref="workflows")
    team: Mapped[Optional["Team"]] = relationship("Team", backref="workflows")
    event_type: Mapped[Optional["EventTypeTable"]] = relationship(
        "EventTypeTable", backref="workflows"
    )
    steps: Mapped[List["WorkflowStepTable"]] = relationship(
        "WorkflowStepTable",
        backref="workflow",
        lazy="selectin",
        order_by="WorkflowStepTable.step_number",
    )


class WorkflowStepTable(Base):
    """Individual steps in a workflow."""

    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=generate_uuid
    )
    workflow_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("workflows.id"), nullable=False, index=True
    )

    step_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Action type: EMAIL, SMS, WEBHOOK, SLACK, TEAMS
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Action configuration (JSON)
    action_config: Mapped[dict] = mapped_column(JSON, default=dict)

    # Delay before executing (minutes)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Is step active
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ReminderLogTable(Base):
    """Scheduled reminders for bookings."""

    __tablename__ = "reminder_logs"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=generate_uuid
    )
    booking_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("bookings.id"), nullable=False, index=True
    )

    # Reminder type: EMAIL, SMS
    reminder_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # When to send
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Status
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Cancellation
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    booking: Mapped["BookingTable"] = relationship("BookingTable", backref="reminders")


class AIAutomationTable(Base):
    """
    Tracks AI agent automation executions for bookings.
    Stores results from the 4-phase agent loop.
    """

    __tablename__ = "ai_automations"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=generate_uuid
    )
    booking_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Automation status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, in_progress, completed, partial, failed

    # Decision quality
    decision_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 0-100
    risk_assessment: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # low, medium, high, critical

    # Agent decisions and reasoning
    agent_decisions: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {actions, reasoning, confidence}

    # Actions executed
    actions_executed: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # List of action results

    # External service results
    external_results: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {email_id, calendar_id, task_id}

    # Execution metrics
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Fallback tracking
    fallback_mode: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # ai_agent, rule_based, manual_review

    # Trigger source
    trigger_source: Mapped[str] = mapped_column(
        String(50), default="api"
    )  # api, webhook, scheduler, manual

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @validates("external_results", "agent_decisions", "actions_executed")
    def validate_json_size(self, key, value):
        """Prevent unbounded growth of JSON columns by truncating or limiting."""
        if value is not None:
            serialized_value = json.dumps(value, default=str)
            original_size = len(serialized_value)
            if original_size > 100000:  # ~100KB limit
                if isinstance(value, list):
                    logger.warning(
                        "Truncated JSON field %s (size=%s, action=%s)",
                        key,
                        original_size,
                        "truncate_list",
                    )
                    return value[:50]  # Keep only first 50 items
                if isinstance(value, dict):
                    logger.warning(
                        "Truncated JSON field %s (size=%s, action=%s)",
                        key,
                        original_size,
                        "truncate_dict",
                    )
                    truncated = {
                        k: str(v)[:1000] + "..."
                        if isinstance(v, str) and len(str(v)) > 1000
                        else v
                        for k, v in list(value.items())[:50]
                    }
                    truncated["_warning"] = "Data truncated due to size limits"
                    return truncated
                logger.warning(
                    "Truncated JSON field %s (size=%s, action=%s)",
                    key,
                    original_size,
                    "replace_placeholder",
                )
                return {"_warning": "Data removed due to size limits"}
        return value
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Indexes for queries
    __table_args__ = (
        Index("idx_automation_status", "status"),
        Index("idx_automation_booking_user", "booking_id", "user_id"),
        Index("idx_automation_created", "created_at"),
    )

    # Relationships
    booking: Mapped["BookingTable"] = relationship(
        "BookingTable", backref="ai_automations"
    )
    user: Mapped["UserTable"] = relationship("UserTable", backref="ai_automations")


class DeadLetterQueueItem(Base):
    """Dead letter queue for failed tasks that need retry or manual resolution."""

    __tablename__ = "dead_letter_queue"
    __table_args__ = (
        Index("ix_dlq_status", "status"),
        Index("ix_dlq_task_type", "task_type"),
        Index("ix_dlq_retry_count", "retry_count"),
        Index("ix_dlq_created_at", "created_at"),
        Index("ix_dlq_next_retry", "next_retry_at"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=generate_uuid
    )
    task_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Original payload
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, retrying, failed, resolved

    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # manual, auto, ignored
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    resolver: Mapped[Optional["UserTable"]] = relationship(
        "UserTable", foreign_keys=[resolved_by]
    )


class IdempotencyKeyTable(Base):
    """Stores idempotency keys to prevent duplicate mutation operations."""

    __tablename__ = "idempotency_keys"
    __table_args__ = (
        # Enforce uniqueness of (user_id, key) at the DB level to avoid races
        UniqueConstraint("user_id", "key", name="uq_idempotency_keys_user_key"),
        Index("ix_idempotency_keys_expires", "expires_at"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=generate_uuid
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Request fingerprint for verification
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    # Cached response
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=200)

    # TTL
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    user: Mapped["UserTable"] = relationship("UserTable", backref="idempotency_keys")
