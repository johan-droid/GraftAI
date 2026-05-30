"""Video conferencing integration models for Zoom, Google Meet, Microsoft Teams."""
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    JITSI = "jitsi"

class VideoConferenceConfig(Base):
    """User's video conferencing provider configurations."""
    __tablename__ = "video_conference_configs"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    default_settings: Mapped[dict] = mapped_column(JSON, default=lambda: {"waiting_room": True, "require_password": True, "enable_recording": False, "mute_upon_entry": True, "allow_join_before_host": False})
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="video_conference_configs")
    meetings: Mapped[list["VideoConferenceMeeting"]] = relationship("VideoConferenceMeeting", back_populates="config", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_video_configs_user_provider", "user_id", "provider", unique=True), Index("ix_video_configs_default", "user_id", "is_default"))

class VideoConferenceMeeting(Base):
    """Video conference meetings created through the platform."""
    __tablename__ = "video_conference_meetings"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    config_id: Mapped[str] = mapped_column(String(100), ForeignKey("video_conference_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    team_booking_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("team_bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_meeting_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    join_url: Mapped[str] = mapped_column(String(500), nullable=False)
    host_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    password: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    recording_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recording_download_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recording_password: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attendee_count: Mapped[int] = mapped_column(default=0)
    max_attendees: Mapped[int | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    config: Mapped["VideoConferenceConfig"] = relationship("VideoConferenceConfig", back_populates="meetings")
    __table_args__ = (Index("ix_video_meetings_booking", "booking_id"), Index("ix_video_meetings_team_booking", "team_booking_id"), Index("ix_video_meetings_time", "start_time", "status"))

class VideoConferenceRecording(Base):
    """Recordings of video conference meetings."""
    __tablename__ = "video_conference_recordings"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: secrets.token_urlsafe(16))
    meeting_id: Mapped[str] = mapped_column(String(100), ForeignKey("video_conference_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_recording_id: Mapped[str] = mapped_column(String(100), nullable=False)
    recording_type: Mapped[str] = mapped_column(String(20), default="cloud")
    play_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    password: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing")
    recording_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recording_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
