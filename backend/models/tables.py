from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(512))
    timezone = Column(String(100), default="UTC")
    tenant_id = Column(Integer, index=True)  # For Row-Level Security (RLS)
    
    # Consent Preferences
    consent_analytics = Column(Boolean, default=True, nullable=False)
    consent_notifications = Column(Boolean, default=True, nullable=False)
    consent_ai_training = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
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

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("UserTable", back_populates="events")
