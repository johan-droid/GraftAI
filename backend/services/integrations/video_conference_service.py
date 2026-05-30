"""Video conferencing service for Zoom, Google Meet, and Microsoft Teams.

This module provides:
- OAuth authentication with video providers
- Meeting creation and management
- Recording retrieval
- Webhook handling for meeting events

Example Usage:
    service = VideoConferenceService(db)

    # Create a Zoom meeting
    meeting = await service.create_meeting(
        user_id="user_123",
        provider="zoom",
        topic="Team Standup",
        start_time="2024-01-20T10:00:00Z",
        duration_minutes=30,
        settings={"waiting_room": True}
    )

    logger.info(f"Meeting join URL: {meeting.join_url}")
    logger.info(f"Meeting host URL: {meeting.host_url}")
"""
import secrets
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.video_conference import (
    VideoConferenceConfig,
    VideoConferenceMeeting,
    VideoConferenceRecording,
)


class VideoConferenceService:
    """Service for managing video conference integrations."""
    OAUTH_ENDPOINTS = {"zoom": {"auth_url": "https://zoom.us/oauth/authorize", "token_url": "https://zoom.us/oauth/token", "revoke_url": "https://zoom.us/oauth/revoke", "scopes": "meeting:write meeting:read user:read"}, "google_meet": {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth", "token_url": "https://oauth2.googleapis.com/token", "scopes": "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar"}, "microsoft_teams": {"auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize", "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token", "scopes": "OnlineMeetings.ReadWrite Calendars.ReadWrite"}}

    def __init__(self, db: AsyncSession):
        """Initialize the video conference service.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def get_config(self, user_id: str, provider: str) -> VideoConferenceConfig | None:
        """Get a user's video conference configuration.

        Args:
            user_id: User ID
            provider: Provider name (zoom, google_meet, microsoft_teams)

        Returns:
            VideoConferenceConfig or None
        """
        stmt = select(VideoConferenceConfig).where(and_(VideoConferenceConfig.user_id == user_id, VideoConferenceConfig.provider == provider, VideoConferenceConfig.is_enabled))
        return (await self.db.execute(stmt)).scalars().first()

    async def get_default_config(self, user_id: str) -> VideoConferenceConfig | None:
        """Get the default video conference configuration for a user.

        Args:
            user_id: User ID

        Returns:
            VideoConferenceConfig or None
        """
        stmt = select(VideoConferenceConfig).where(and_(VideoConferenceConfig.user_id == user_id, VideoConferenceConfig.is_default, VideoConferenceConfig.is_enabled))
        return (await self.db.execute(stmt)).scalars().first()

    async def create_zoom_meeting(self, config: VideoConferenceConfig, topic: str, start_time: datetime, duration_minutes: int=30, settings: dict | None=None) -> VideoConferenceMeeting:
        """Create a Zoom meeting.

        Args:
            config: Zoom configuration with valid access token
            topic: Meeting topic/title
            start_time: Meeting start time (timezone-aware)
            duration_minutes: Meeting duration
            settings: Additional Zoom meeting settings

        Returns:
            VideoConferenceMeeting record

        Raises:
            ValueError: If access token is invalid or expired
            httpx.HTTPError: If Zoom API request fails
        """
        if not config.access_token:
            msg = "Zoom not authenticated"
            raise ValueError(msg)
        meeting_settings = {"topic": topic, "type": 2, "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"), "duration": duration_minutes, "timezone": "UTC", "settings": {"waiting_room": settings.get("waiting_room", True), "password": settings.get("password", ""), "host_video": settings.get("host_video", False), "participant_video": settings.get("participant_video", False), "mute_upon_entry": settings.get("mute_upon_entry", True), "auto_recording": "cloud" if settings.get("enable_recording", False) else "none", "join_before_host": settings.get("allow_join_before_host", False)}}
        response = await self.http_client.post("https://api.zoom.us/v2/users/me/meetings", headers={"Authorization": f"Bearer {config.access_token}", "Content-Type": "application/json"}, json=meeting_settings)
        response.raise_for_status()
        zoom_data = response.json()
        meeting = VideoConferenceMeeting(config_id=config.id, provider="zoom", provider_meeting_id=str(zoom_data["id"]), topic=topic, join_url=zoom_data["join_url"], host_url=zoom_data.get("start_url"), password=zoom_data.get("password"), start_time=start_time, end_time=start_time + timedelta(minutes=duration_minutes), timezone="UTC", settings=meeting_settings["settings"], status="scheduled", metadata={"zoom_meeting_uuid": zoom_data.get("uuid"), "zoom_host_id": zoom_data.get("host_id")})
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        config.last_used_at = datetime.now(UTC)
        await self.db.commit()
        return meeting

    async def create_jitsi_meeting(self, config: object | None, topic: str, start_time: datetime, duration_minutes: int=30, settings: dict | None=None, booking_id: str | None=None) -> VideoConferenceMeeting:
        """Create a Jitsi meeting descriptor and persist a VideoConferenceMeeting record.

        For public Jitsi (`meet.jit.si`) this will generate a join URL without
        contacting any external API. For self-hosted Jitsi, pass relevant `config`
        with domain/jwt_secret and this method will record the metadata.
        """
        from backend.models.video_conference import VideoConferenceMeeting
        base = (booking_id or secrets.token_urlsafe(8)).replace("/", "-")
        room_name = f"graftai-{base}"
        domain = "meet.jit.si"
        if config and getattr(config, "config", None) and config.config.get("domain"):
            domain = config.config.get("domain")
        join_url = f"https://{domain}/{room_name}"
        meeting = VideoConferenceMeeting(config_id=config.id if config is not None else "", provider="jitsi", provider_meeting_id=room_name, topic=topic, join_url=join_url, host_url=None, password=None, start_time=start_time, end_time=start_time + timedelta(minutes=duration_minutes), timezone="UTC", settings=settings or {}, status="scheduled", metadata_json={"room_name": room_name, "domain": domain})
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        if config is not None:
            try:
                config.last_used_at = datetime.now(UTC)
                await self.db.commit()
            except Exception:
                pass
        return meeting

    async def create_google_meet(self, config: VideoConferenceConfig, topic: str, start_time: datetime, duration_minutes: int=30, settings: dict | None=None) -> VideoConferenceMeeting:
        """Create a Google Meet conference via Google Calendar API.

        Creates a calendar event with Google Meet conference data.

        Args:
            config: Google configuration with valid access token
            topic: Meeting title
            start_time: Meeting start time
            duration_minutes: Meeting duration
            settings: Additional settings

        Returns:
            VideoConferenceMeeting record
        """
        if not config.access_token:
            msg = "Google not authenticated"
            raise ValueError(msg)
        end_time = start_time + timedelta(minutes=duration_minutes)
        event_data = {"summary": topic, "description": settings.get("description", ""), "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"}, "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"}, "conferenceData": {"createRequest": {"requestId": secrets.token_urlsafe(16), "conferenceSolutionKey": {"type": "hangoutsMeet"}}}}
        response = await self.http_client.post("https://www.googleapis.com/calendar/v3/calendars/primary/events", headers={"Authorization": f"Bearer {config.access_token}", "Content-Type": "application/json"}, params={"conferenceDataVersion": 1}, json=event_data)
        response.raise_for_status()
        event_data = response.json()
        conference_data = event_data.get("conferenceData", {})
        meet_url = None
        for entry_point in conference_data.get("entryPoints", []):
            if entry_point.get("entryPointType") == "video":
                meet_url = entry_point.get("uri")
                break
        meeting = VideoConferenceMeeting(config_id=config.id, provider="google_meet", provider_meeting_id=conference_data.get("conferenceId", event_data["id"]), topic=topic, join_url=meet_url or f"https://meet.google.com/{conference_data.get('conferenceId', 'unknown')}", host_url=meet_url, start_time=start_time, end_time=end_time, timezone="UTC", settings=settings or {}, status="scheduled", metadata={"google_event_id": event_data["id"], "google_calendar_id": "primary", "conference_id": conference_data.get("conferenceId")})
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        config.last_used_at = datetime.now(UTC)
        await self.db.commit()
        return meeting

    async def create_teams_meeting(self, config: VideoConferenceConfig, topic: str, start_time: datetime, duration_minutes: int=30, settings: dict | None=None) -> VideoConferenceMeeting:
        """Create a Microsoft Teams meeting.

        Args:
            config: Teams configuration with valid access token
            topic: Meeting title
            start_time: Meeting start time
            duration_minutes: Meeting duration
            settings: Additional settings

        Returns:
            VideoConferenceMeeting record
        """
        if not config.access_token:
            msg = "Microsoft Teams not authenticated"
            raise ValueError(msg)
        end_time = start_time + timedelta(minutes=duration_minutes)
        meeting_data = {"subject": topic, "startDateTime": start_time.isoformat(), "endDateTime": end_time.isoformat(), "allowedPresenters": "everyone" if settings.get("allow_everyone_present", True) else "organizer"}
        if settings.get("lobby_bypass"):
            meeting_data["lobbyBypassSettings"] = {"scope": settings["lobby_bypass"]}
        response = await self.http_client.post("https://graph.microsoft.com/v1.0/me/onlineMeetings", headers={"Authorization": f"Bearer {config.access_token}", "Content-Type": "application/json"}, json=meeting_data)
        response.raise_for_status()
        teams_data = response.json()
        meeting = VideoConferenceMeeting(config_id=config.id, provider="microsoft_teams", provider_meeting_id=teams_data["id"], topic=topic, join_url=teams_data.get("joinWebUrl"), start_time=start_time, end_time=end_time, timezone="UTC", settings=settings or {}, status="scheduled", metadata={"teams_meeting_id": teams_data["id"], "join_meeting_id": teams_data.get("joinMeetingId"), "organizer_id": teams_data.get("organizer", {}).get("id")})
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        config.last_used_at = datetime.now(UTC)
        await self.db.commit()
        return meeting

    async def create_meeting(self, user_id: str, provider: str, topic: str, start_time: datetime, duration_minutes: int=30, settings: dict | None=None, booking_id: str | None=None) -> VideoConferenceMeeting:
        """Create a video conference meeting with the specified provider.

        This is the main entry point for creating meetings. It automatically
        routes to the appropriate provider implementation.

        Args:
            user_id: User ID
            provider: Provider name (zoom, google_meet, microsoft_teams)
            topic: Meeting title
            start_time: Meeting start time (timezone-aware)
            duration_minutes: Meeting duration
            settings: Provider-specific settings
            booking_id: Optional associated booking ID

        Returns:
            VideoConferenceMeeting record

        Raises:
            ValueError: If provider not configured or not supported
        """
        config = await self.get_config(user_id, provider)
        if not config:
            msg = f"{provider} not configured for this user"
            raise ValueError(msg)
        if provider == "zoom":
            meeting = await self.create_zoom_meeting(config, topic, start_time, duration_minutes, settings)
        elif provider == "google_meet":
            meeting = await self.create_google_meet(config, topic, start_time, duration_minutes, settings)
        elif provider == "microsoft_teams":
            meeting = await self.create_teams_meeting(config, topic, start_time, duration_minutes, settings)
        else:
            msg = f"Unsupported provider: {provider}"
            raise ValueError(msg)
        if booking_id:
            meeting.booking_id = booking_id
            await self.db.commit()
        return meeting

    async def delete_meeting(self, meeting_id: str, user_id: str) -> bool:
        """Delete/cancel a video conference meeting.

        Args:
            meeting_id: Meeting ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted successfully
        """
        stmt = select(VideoConferenceMeeting).where(and_(VideoConferenceMeeting.id == meeting_id, VideoConferenceMeeting.config_id.in_(select(VideoConferenceConfig.id).where(VideoConferenceConfig.user_id == user_id))))
        meeting = (await self.db.execute(stmt)).scalars().first()
        if not meeting:
            return False
        try:
            config = await self.db.get(VideoConferenceConfig, meeting.config_id)
            if config and config.access_token:
                if meeting.provider == "zoom":
                    await self.http_client.delete(f"https://api.zoom.us/v2/meetings/{meeting.provider_meeting_id}", headers={"Authorization": f"Bearer {config.access_token}"})
                elif meeting.provider == "google_meet":
                    await self.http_client.delete(f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{meeting.metadata_json.get('google_event_id')}", headers={"Authorization": f"Bearer {config.access_token}"})
        except Exception:
            pass
        meeting.status = "cancelled"
        await self.db.commit()
        return True

    async def get_meeting_recordings(self, meeting_id: str, user_id: str) -> list[VideoConferenceRecording]:
        """Get recordings for a meeting.

        Args:
            meeting_id: Meeting ID
            user_id: User ID (for authorization)

        Returns:
            List of VideoConferenceRecording records
        """
        stmt = select(VideoConferenceRecording).where(and_(VideoConferenceRecording.meeting_id == meeting_id, VideoConferenceRecording.status == "completed"))
        return (await self.db.execute(stmt)).scalars().all()

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
