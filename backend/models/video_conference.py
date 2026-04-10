"""Video conferencing integration models for Zoom, Google Meet, Microsoft Teams."""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
import secrets

from .base import Base

if TYPE_CHECKING:
    from backend.models.tables import UserTable
    from backend.models.video_conference import VideoConferenceMeeting


class VideoConferenceProvider(str):
    """Supported video conference providers."""
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    MICROSOFT_TEAMS = "microsoft_teams"
    WEBEX = "webex"


class VideoConferenceConfig(Base):
    """User's video conferencing provider configurations."""
    __tablename__ = "video_conference_configs"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # User ownership
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Provider settings
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # zoom, google_meet, microsoft_teams, webex
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # Use as default for new bookings
    
    # OAuth tokens (encrypted)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Provider-specific settings
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    # Examples:
    # Zoom: {"account_id": "...", "client_id": "..."}
    # Google: {"calendar_id": "primary"}
    # Teams: {"tenant_id": "..."}
    
    # Meeting defaults
    default_settings: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "waiting_room": True,
        "require_password": True,
        "enable_recording": False,
        "mute_upon_entry": True,
        "allow_join_before_host": False
    })
    
    # Metadata
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="video_conference_configs")
    meetings: Mapped[List["VideoConferenceMeeting"]] = relationship("VideoConferenceMeeting", back_populates="config", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_video_configs_user_provider', 'user_id', 'provider', unique=True),
        Index('ix_video_configs_default', 'user_id', 'is_default'),
    )


class VideoConferenceMeeting(Base):
    """Video conference meetings created through the platform."""
    __tablename__ = "video_conference_meetings"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # References
    config_id: Mapped[str] = mapped_column(String(100), ForeignKey("video_conference_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    team_booking_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("team_bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Provider info
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_meeting_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Zoom meeting ID, etc.
    
    # Meeting details
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Join information
    join_url: Mapped[str] = mapped_column(String(500), nullable=False)
    host_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Host/start URL
    password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Schedule
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Settings used
    settings: Mapped[dict] = mapped_column(JSON, default=dict)  # Snapshot of settings at creation
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled, started, ended, cancelled
    
    # Recording
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    recording_download_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    recording_password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Attendees
    attendee_count: Mapped[int] = mapped_column(default=0)
    max_attendees: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)  # Provider-specific data
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    config: Mapped["VideoConferenceConfig"] = relationship("VideoConferenceConfig", back_populates="meetings")
    
    __table_args__ = (
        Index('ix_video_meetings_booking', 'booking_id'),
        Index('ix_video_meetings_team_booking', 'team_booking_id'),
        Index('ix_video_meetings_time', 'start_time', 'status'),
    )


class VideoConferenceRecording(Base):
    """Recordings of video conference meetings."""
    __tablename__ = "video_conference_recordings"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    
    # References
    meeting_id: Mapped[str] = mapped_column(String(100), ForeignKey("video_conference_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Recording details
    provider_recording_id: Mapped[str] = mapped_column(String(100), nullable=False)
    recording_type: Mapped[str] = mapped_column(String(20), default="cloud")  # cloud, local
    
    # URLs
    play_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # File details
    file_size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    file_format: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # mp4, m4a, etc.
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing, completed, failed
    
    # Timestamps
    recording_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recording_ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
