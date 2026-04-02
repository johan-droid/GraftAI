from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
import enum
from .base import Base

class UserTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ELITE = "elite"

class UserTable(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(512))
    # SaaS & Billing
    tier = Column(String(20), default=UserTier.FREE, nullable=False)
    stripe_customer_id = Column(String(255), index=True)
    razorpay_customer_id = Column(String(255), index=True)
    razorpay_subscription_id = Column(String(255), index=True)
    subscription_status = Column(String(50), default="inactive") # active, trialing, past_due, canceled
    
    # Daily Usage Tracking
    daily_ai_count = Column(Integer, default=0, nullable=False)
    daily_sync_count = Column(Integer, default=0, nullable=False)
    last_usage_reset = Column(DateTime(timezone=True), server_default=func.now())
    timezone = Column(String(50), default="UTC", nullable=False)

    # Consent Preferences
    consent_analytics = Column(Boolean, default=True, nullable=False)
    consent_notifications = Column(Boolean, default=True, nullable=False)
    consent_ai_training = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    events = relationship(
        "EventTable", back_populates="user", cascade="all, delete-orphan"
    )


class EventTable(Base):
    """
    Sovereign Scheduling Table
    Supports high-density meeting management and category-based visualization.
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", "external_id", name="uq_user_external_id"),
        Index("idx_events_user_time_range", "user_id", "start_time", "end_time"),
    )

    title = Column(String(512), nullable=False)
    description = Column(Text)
    category = Column(
        String(50), default="meeting", index=True
    )  # meeting, event, birthday, task
    color = Column(String(20), default="#8A2BE2")

    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)

    # Advanced metadata for AI integration (e.g. priority, required participants, location)
    metadata_payload = Column(JSONB, default={}, nullable=False)

    is_remote = Column(Boolean, default=True)
    status = Column(String(50), default="confirmed")  # confirmed, pending, canceled
    is_reminded = Column(Boolean, default=False, nullable=False)
    
    # SaaS Meeting Integration
    is_meeting = Column(Boolean, default=False, nullable=False)
    meeting_platform = Column(String(50))  # google_meet, zoom, teams
    meeting_link = Column(String(1024))
    attendees = Column(JSONB, default=[], nullable=False)
    agenda = Column(Text)

    # Smart Sync Engine Fields
    external_id = Column(String(512), index=True) # ID from Google/Microsoft/Zoom
    fingerprint = Column(String(256), index=True) # deduplication hash
    source = Column(String(50), default="local") # google, microsoft, zoom, local

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("UserTable", back_populates="events")

class ProcessedWebhook(Base):
    """
    Idempotency table for tracking processed Stripe/Razorpay webhook events.
    Prevents duplicate processing of retried webhooks.
    """
    __tablename__ = "processed_webhooks"
    
    event_id = Column(String(255), primary_key=True)
    provider = Column(String(50), nullable=False) # stripe, razorpay
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
