import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.utils.soft_delete import SoftDeleteMixin

from .base import Base

logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    from backend.models.automation import AutomationRule
    from backend.models.dsr import ConsentRecord, DSRRecord
    from backend.models.email_template import EmailTemplate
    from backend.models.integration import Integration
    from backend.models.resource import Resource, ResourceBooking
    from backend.models.team import Team, TeamMember
    from backend.models.video_conference import VideoConferenceConfig

def generate_uuid():
    return str(uuid.uuid4())

def generate_booking_code() -> str:
    return uuid.uuid4().hex[:10].upper()

class UserTable(Base):
    """Core user account. Stripped of complex multi-tenant organization IDs."""
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String, nullable=True, default="UTC")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_code: Mapped[str | None] = mapped_column(String, nullable=True)
    email_verification_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tier: Mapped[str] = mapped_column(String, default="free", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String, default="inactive", nullable=False)
    razorpay_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    razorpay_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)
    daily_ai_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_ai_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_sync_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_sync_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quota_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_ai_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_api_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_scheduling_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tokens: Mapped[list["UserTokenTable"]] = relationship("UserTokenTable", back_populates="user", cascade="all, delete-orphan")
    events: Mapped[list["EventTable"]] = relationship("EventTable", back_populates="user", cascade="all, delete-orphan")
    event_types: Mapped[list["EventTypeTable"]] = relationship("EventTypeTable", back_populates="user", cascade="all, delete-orphan")
    team_event_type_memberships: Mapped[list["EventTypeTeamMemberTable"]] = relationship("EventTypeTeamMemberTable", back_populates="user", cascade="all, delete-orphan")
    bookings: Mapped[list["BookingTable"]] = relationship("BookingTable", back_populates="user", cascade="all, delete-orphan")
    webhooks: Mapped[list["WebhookSubscriptionTable"]] = relationship("WebhookSubscriptionTable", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["NotificationTable"]] = relationship("NotificationTable", back_populates="user", cascade="all, delete-orphan")
    mfa_settings: Mapped[list["UserMFATable"]] = relationship("UserMFATable", back_populates="user", cascade="all, delete-orphan")
    dsr_requests: Mapped[list["DSRRecord"]] = relationship("DSRRecord", back_populates="user", cascade="all, delete-orphan")
    consent_records: Mapped[list["ConsentRecord"]] = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")
    team_memberships: Mapped[list["TeamMember"]] = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    integrations: Mapped[list["Integration"]] = relationship("Integration", back_populates="user", cascade="all, delete-orphan")
    email_templates: Mapped[list["EmailTemplate"]] = relationship("EmailTemplate", back_populates="user", cascade="all, delete-orphan")
    video_conference_configs: Mapped[list["VideoConferenceConfig"]] = relationship("VideoConferenceConfig", back_populates="user", cascade="all, delete-orphan")
    owned_resources: Mapped[list["Resource"]] = relationship("Resource", back_populates="owner", cascade="all, delete-orphan")
    resource_bookings: Mapped[list["ResourceBooking"]] = relationship("ResourceBooking", back_populates="user")
    automation_rules: Mapped[list["AutomationRule"]] = relationship("AutomationRule", back_populates="user", cascade="all, delete-orphan")

class UserTokenTable(Base):
    """Holds OAuth tokens for Google Calendar / MS Graph."""
    __tablename__ = "user_tokens"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_token: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="tokens")

class NotificationTable(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="notifications")

class EventTable(Base, SoftDeleteMixin):
    """Unified table for both local schedule blocks and external synced events."""
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type_id: Mapped[str | None] = mapped_column(String, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_meeting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meeting_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    attendees: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String, nullable=False, index=True)
    is_reminded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="events")
    event_type: Mapped[Optional["EventTypeTable"]] = relationship("EventTypeTable", back_populates="events")
    booking: Mapped[Optional["BookingTable"]] = relationship("BookingTable", back_populates="event", uselist=False)

class BookingTable(Base, SoftDeleteMixin):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("user_id", "start_time", "end_time", name="uq_bookings_user_start_end"), Index("ix_bookings_user_start_time", "user_id", "start_time"), Index("ix_bookings_booking_code", "booking_code"), Index("ix_bookings_automation_status", "automation_status"), Index("ix_bookings_automation_run_at", "automation_run_at"), Index("ix_bookings_decision_score", "decision_score"), Index("ix_bookings_risk_level", "risk_level"))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type_id: Mapped[str | None] = mapped_column(String, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    event_id: Mapped[str | None] = mapped_column(String, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    booking_code: Mapped[str | None] = mapped_column(String, nullable=True, default=generate_booking_code)
    time_zone: Mapped[str | None] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="confirmed")
    is_reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    questions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    automation_status: Mapped[str | None] = mapped_column(String, nullable=True, default="pending")
    automation_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String, nullable=True)
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="bookings")
    event_type: Mapped[Optional["EventTypeTable"]] = relationship("EventTypeTable")
    event: Mapped[Optional["EventTable"]] = relationship("EventTable", back_populates="booking")

class WebhookSubscriptionTable(Base, SoftDeleteMixin):
    __tablename__ = "webhook_subscriptions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    events: Mapped[dict] = mapped_column(JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    external_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    client_state: Mapped[str | None] = mapped_column(String, nullable=True)
    last_triggered: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="webhooks")
    logs: Mapped[list["WebhookLogTable"]] = relationship("WebhookLogTable", back_populates="webhook", cascade="all, delete-orphan")

class WebhookLogTable(Base):
    __tablename__ = "webhook_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    webhook_id: Mapped[str] = mapped_column(String, ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    event: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True, unique=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    webhook: Mapped["WebhookSubscriptionTable"] = relationship("WebhookSubscriptionTable", back_populates="logs")

class EventTypeTable(Base, SoftDeleteMixin):
    __tablename__ = "event_types"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_user_event_type_slug"), Index("ix_event_types_user_slug", "user_id", "slug"))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3b82f6")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    meeting_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    buffer_before_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buffer_after_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minimum_notice_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    availability: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    exceptions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_questions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    requires_attendee_confirmation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    travel_time_before_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    travel_time_after_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requires_payment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payment_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    payment_currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    team_assignment_method: Mapped[str] = mapped_column(String, default="host_only", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="event_types")
    events: Mapped[list["EventTable"]] = relationship("EventTable", back_populates="event_type", cascade="all, delete-orphan")
    team_members: Mapped[list["EventTypeTeamMemberTable"]] = relationship("EventTypeTeamMemberTable", back_populates="event_type", cascade="all, delete-orphan")

class EventTypeTeamMemberTable(Base):
    __tablename__ = "event_type_team_members"
    __table_args__ = (UniqueConstraint("event_type_id", "user_id", name="uq_event_type_team_member"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    event_type_id: Mapped[str] = mapped_column(String, ForeignKey("event_types.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_method: Mapped[str] = mapped_column(String, default="host_only", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    event_type: Mapped["EventTypeTable"] = relationship("EventTypeTable", back_populates="team_members")
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="team_event_type_memberships")

class UserMFATable(Base):
    """Multi-factor authentication settings for users (TOTP)."""
    __tablename__ = "user_mfa"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mfa_type: Mapped[str] = mapped_column(String, nullable=False, default="totp")
    secret: Mapped[str | None] = mapped_column(String, nullable=True)
    backup_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="mfa_settings")

class AuditLogTable(Base):
    """SaaS Audit Log for security, compliance and usage tracking (SOC 2)."""
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="info")
    user_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result: Mapped[str] = mapped_column(String(10), nullable=False, default="success")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    compliance_standards: Mapped[list] = mapped_column(JSON, default=list)
    data_subjects_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_categories: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    user: Mapped[Optional["UserTable"]] = relationship("UserTable", foreign_keys=[user_id])
    team: Mapped[Optional["Team"]] = relationship("Team")

class ManualActivationRequestTable(Base):
    """Manual activation requests for users who cannot complete automated payments.

    Allows users (students) to request a paid tier upgrade which an admin
    (or parent) can approve manually after reviewing proof.
    """
    __tablename__ = "manual_activation_requests"
    __table_args__ = (Index("ix_manual_activation_requests_user_id", "user_id"), Index("ix_manual_activation_requests_status", "status"))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    requested_tier: Mapped[str] = mapped_column(String(50), nullable=False, default="pro")
    proof_url: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    user: Mapped["UserTable"] = relationship("UserTable", foreign_keys=[user_id], backref="manual_activation_requests")
    reviewer: Mapped[Optional["UserTable"]] = relationship("UserTable", foreign_keys=[reviewed_by])

class ChatMessageTable(Base):
    """AI Copilot chat messages for conversation history and context."""
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    user: Mapped["UserTable"] = relationship("UserTable", backref="chat_messages")

class TeamMembershipTable(Base):
    """Team membership with role-based access (OWNER, ADMIN, MEMBER)."""
    __tablename__ = "team_memberships"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=generate_uuid)
    team_id: Mapped[str] = mapped_column(String(100), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="MEMBER")
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    invited_by: Mapped[str | None] = mapped_column(String(100), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invite_token: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    invite_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    user: Mapped["UserTable"] = relationship("UserTable", foreign_keys=[user_id])
    inviter: Mapped[Optional["UserTable"]] = relationship("UserTable", foreign_keys=[invited_by])

class WorkflowTable(Base, SoftDeleteMixin):
    """Workflows for automated sequences."""
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=generate_uuid)
    user_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    team_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    user: Mapped[Optional["UserTable"]] = relationship("UserTable", backref="workflows")
    team: Mapped[Optional["Team"]] = relationship("Team", backref="workflows")
    event_type: Mapped[Optional["EventTypeTable"]] = relationship("EventTypeTable", backref="workflows")
    steps: Mapped[list["WorkflowStepTable"]] = relationship("WorkflowStepTable", backref="workflow", lazy="selectin", order_by="WorkflowStepTable.step_number")

class WorkflowStepTable(Base):
    """Individual steps in a workflow."""
    __tablename__ = "workflow_steps"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=generate_uuid)
    workflow_id: Mapped[str] = mapped_column(String(100), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    action_config: Mapped[dict] = mapped_column(JSON, default=dict)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

class ReminderLogTable(Base):
    """Scheduled reminders for bookings."""
    __tablename__ = "reminder_logs"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=generate_uuid)
    booking_id: Mapped[str] = mapped_column(String(100), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    booking: Mapped["BookingTable"] = relationship("BookingTable", backref="reminders")

class AIAutomationTable(Base):
    """
    Tracks AI agent automation executions for bookings.
    Stores results from the 4-phase agent loop.
    """
    __tablename__ = "ai_automations"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=generate_uuid)
    booking_id: Mapped[str] = mapped_column(String(100), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    decision_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_assessment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    agent_decisions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actions_executed: Mapped[list | None] = mapped_column(JSON, nullable=True)
    external_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    fallback_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trigger_source: Mapped[str] = mapped_column(String(50), default="api")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    @validates("external_results", "agent_decisions", "actions_executed")
    def validate_json_size(self, key, value):
        """Prevent unbounded growth of JSON columns by truncating or limiting."""
        if value is not None:
            serialized_value = json.dumps(value, default=str)
            original_size = len(serialized_value)
            if original_size > 100000:
                if isinstance(value, list):
                    logger.warning("Truncated JSON field %s (size=%s, action=%s)", key, original_size, "truncate_list")
                    return value[:50]
                if isinstance(value, dict):
                    logger.warning("Truncated JSON field %s (size=%s, action=%s)", key, original_size, "truncate_dict")
                    truncated = {k: str(v)[:1000] + "..." if isinstance(v, str) and len(str(v)) > 1000 else v for k, v in list(value.items())[:50]}
                    truncated["_warning"] = "Data truncated due to size limits"
                    return truncated
                logger.warning("Truncated JSON field %s (size=%s, action=%s)", key, original_size, "replace_placeholder")
                return {"_warning": "Data removed due to size limits"}
        return value
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    __table_args__ = (Index("idx_automation_status", "status"), Index("idx_automation_booking_user", "booking_id", "user_id"), Index("idx_automation_created", "created_at"))
    booking: Mapped["BookingTable"] = relationship("BookingTable", backref="ai_automations")
    user: Mapped["UserTable"] = relationship("UserTable", backref="ai_automations")

class DeadLetterQueueItem(Base):
    """Dead letter queue for failed tasks that need retry or manual resolution."""
    __tablename__ = "dead_letter_queue"
    __table_args__ = (Index("ix_dlq_status", "status"), Index("ix_dlq_task_type", "task_type"), Index("ix_dlq_retry_count", "retry_count"), Index("ix_dlq_created_at", "created_at"), Index("ix_dlq_next_retry", "next_retry_at"))
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=generate_uuid)
    task_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    resolution: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    resolver: Mapped[Optional["UserTable"]] = relationship("UserTable", foreign_keys=[resolved_by])

class IdempotencyKeyTable(Base):
    """Stores idempotency keys to prevent duplicate mutation operations."""
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_idempotency_keys_user_key"), Index("ix_idempotency_keys_expires", "expires_at"))
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=generate_uuid)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    user: Mapped["UserTable"] = relationship("UserTable", backref="idempotency_keys")

class PaymentIntentTable(Base):
    """Tracks payment intents across Stripe and Razorpay with state machine."""
    __tablename__ = "payment_intents"
    __table_args__ = (
        Index("ix_payment_intents_user_id", "user_id"),
        Index("ix_payment_intents_booking_id", "booking_id"),
        Index("ix_payment_intents_gateway_intent", "gateway", "gateway_payment_intent_id"),
        Index("ix_payment_intents_status", "status"),
        Index("ix_payment_intents_created_at", "created_at"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    booking_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    event_type_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True)
    gateway: Mapped[str] = mapped_column(String(20), nullable=False)
    gateway_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="initiated", nullable=False, index=True)
    client_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    user: Mapped["UserTable"] = relationship("UserTable", backref="payment_intents")
    booking: Mapped[Optional["BookingTable"]] = relationship("BookingTable", backref="payment_intents", foreign_keys=[booking_id])
