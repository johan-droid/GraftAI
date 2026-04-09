import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint, Integer
from sqlalchemy.orm import relationship
from .base import Base # Re-using central Base for consistency

def generate_uuid():
    return str(uuid.uuid4())

class UserTable(Base):
    """Core user account. Stripped of complex multi-tenant organization IDs."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    timezone = Column(String, nullable=True, default="UTC")
    hashed_password = Column(String, nullable=False) # Enforced non-nullable for Monolith
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    tokens = relationship("UserTokenTable", back_populates="user", cascade="all, delete-orphan")
    events = relationship("EventTable", back_populates="user", cascade="all, delete-orphan")
    event_types = relationship("EventTypeTable", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("BookingTable", back_populates="user", cascade="all, delete-orphan")
    webhooks = relationship("WebhookSubscriptionTable", back_populates="user", cascade="all, delete-orphan")


class UserTokenTable(Base):
    """Holds OAuth tokens for Google Calendar / MS Graph."""
    __tablename__ = "user_tokens"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)  # e.g., 'google' or 'microsoft'
    
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Used by the sync engine to fetch only new events
    sync_token = Column(String, nullable=True)  
    is_active = Column(Boolean, default=True)

    user = relationship("UserTable", back_populates="tokens")


class EventTable(Base):
    """Unified table for both local schedule blocks and external synced events."""
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type_id = Column(String, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    
    external_id = Column(String, nullable=True, index=True) # ID from Google/MSFT
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    source = Column(String, nullable=False) # 'google', 'microsoft', or 'local'
    location = Column(String, nullable=True)
    meeting_url = Column(Text, nullable=True)
    is_meeting = Column(Boolean, default=False, nullable=False)
    meeting_provider = Column(String, nullable=True)
    attendees = Column(JSON, nullable=True)
    metadata_payload = Column(JSON, nullable=True)
    
    # We kept the fingerprint to detect changes easily without complex diffing
    fingerprint = Column(String, nullable=False, index=True) 
    
    # Used by the Arq worker to trigger the simple email reminder
    is_reminded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("UserTable", back_populates="events")
    event_type = relationship("EventTypeTable", back_populates="events")
    booking = relationship("BookingTable", back_populates="event", uselist=False)


class BookingTable(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("user_id", "start_time", "end_time", name="uq_bookings_user_start_end"),
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type_id = Column(String, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    event_id = Column(String, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)

    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    time_zone = Column(String, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, default="confirmed")
    questions = Column(JSON, nullable=True)
    metadata_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("UserTable", back_populates="bookings")
    event_type = relationship("EventTypeTable")
    event = relationship("EventTable", back_populates="booking")


class WebhookSubscriptionTable(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    secret = Column(String, nullable=False)
    external_subscription_id = Column(String, nullable=True, index=True)
    client_state = Column(String, nullable=True)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UserTable", back_populates="webhooks")
    logs = relationship("WebhookLogTable", back_populates="webhook", cascade="all, delete-orphan")


class WebhookLogTable(Base):
    __tablename__ = "webhook_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    webhook_id = Column(String, ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    request_status = Column(Integer, nullable=False, default=0)
    request_error = Column(Text, nullable=True)
    attempts = Column(Integer, nullable=False, default=1)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    webhook = relationship("WebhookSubscriptionTable", back_populates="logs")


class EventTypeTable(Base):
    __tablename__ = "event_types"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_user_event_type_slug"),)

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    meeting_provider = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)
    buffer_before_minutes = Column(Integer, nullable=True)
    buffer_after_minutes = Column(Integer, nullable=True)
    minimum_notice_minutes = Column(Integer, nullable=True, default=0)
    availability = Column(JSON, nullable=True)
    exceptions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("UserTable", back_populates="event_types")
    events = relationship("EventTable", back_populates="event_type", cascade="all, delete-orphan")
