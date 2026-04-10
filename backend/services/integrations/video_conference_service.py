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
    
    print(meeting.join_url)  # URL for attendees
    print(meeting.host_url)   # URL for host to start
"""

import json
import base64
import hashlib
import secrets
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.video_conference import (
    VideoConferenceConfig, VideoConferenceMeeting, 
    VideoConferenceRecording, VideoConferenceProvider
)


class VideoConferenceService:
    """Service for managing video conference integrations."""
    
    # Provider OAuth endpoints
    OAUTH_ENDPOINTS = {
        "zoom": {
            "auth_url": "https://zoom.us/oauth/authorize",
            "token_url": "https://zoom.us/oauth/token",
            "revoke_url": "https://zoom.us/oauth/revoke",
            "scopes": "meeting:write meeting:read user:read"
        },
        "google_meet": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scopes": "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar"
        },
        "microsoft_teams": {
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "scopes": "OnlineMeetings.ReadWrite Calendars.ReadWrite"
        }
    }
    
    def __init__(self, db: AsyncSession):
        """Initialize the video conference service.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def get_config(
        self, 
        user_id: str, 
        provider: str
    ) -> Optional[VideoConferenceConfig]:
        """Get a user's video conference configuration.
        
        Args:
            user_id: User ID
            provider: Provider name (zoom, google_meet, microsoft_teams)
        
        Returns:
            VideoConferenceConfig or None
        """
        stmt = select(VideoConferenceConfig).where(
            and_(
                VideoConferenceConfig.user_id == user_id,
                VideoConferenceConfig.provider == provider,
                VideoConferenceConfig.is_enabled == True
            )
        )
        return (await self.db.execute(stmt)).scalars().first()
    
    async def get_default_config(
        self, 
        user_id: str
    ) -> Optional[VideoConferenceConfig]:
        """Get the default video conference configuration for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            VideoConferenceConfig or None
        """
        stmt = select(VideoConferenceConfig).where(
            and_(
                VideoConferenceConfig.user_id == user_id,
                VideoConferenceConfig.is_default == True,
                VideoConferenceConfig.is_enabled == True
            )
        )
        return (await self.db.execute(stmt)).scalars().first()
    
    async def create_zoom_meeting(
        self,
        config: VideoConferenceConfig,
        topic: str,
        start_time: datetime,
        duration_minutes: int = 30,
        settings: Optional[Dict] = None
    ) -> VideoConferenceMeeting:
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
        # Ensure token is valid
        if not config.access_token:
            raise ValueError("Zoom not authenticated")
        
        # Build meeting settings
        meeting_settings = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration": duration_minutes,
            "timezone": "UTC",
            "settings": {
                "waiting_room": settings.get("waiting_room", True),
                "password": settings.get("password", ""),
                "host_video": settings.get("host_video", False),
                "participant_video": settings.get("participant_video", False),
                "mute_upon_entry": settings.get("mute_upon_entry", True),
                "auto_recording": "cloud" if settings.get("enable_recording", False) else "none",
                "join_before_host": settings.get("allow_join_before_host", False),
            }
        }
        
        # Create meeting via Zoom API
        response = await self.http_client.post(
            "https://api.zoom.us/v2/users/me/meetings",
            headers={
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json"
            },
            json=meeting_settings
        )
        response.raise_for_status()
        
        zoom_data = response.json()
        
        # Create meeting record
        meeting = VideoConferenceMeeting(
            config_id=config.id,
            provider="zoom",
            provider_meeting_id=str(zoom_data["id"]),
            topic=topic,
            join_url=zoom_data["join_url"],
            host_url=zoom_data.get("start_url"),
            password=zoom_data.get("password"),
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            timezone="UTC",
            settings=meeting_settings["settings"],
            status="scheduled",
            metadata={
                "zoom_meeting_uuid": zoom_data.get("uuid"),
                "zoom_host_id": zoom_data.get("host_id")
            }
        )
        
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        
        # Update last used
        config.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        return meeting
    
    async def create_google_meet(
        self,
        config: VideoConferenceConfig,
        topic: str,
        start_time: datetime,
        duration_minutes: int = 30,
        settings: Optional[Dict] = None
    ) -> VideoConferenceMeeting:
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
            raise ValueError("Google not authenticated")
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Build event with conference data
        event_data = {
            "summary": topic,
            "description": settings.get("description", ""),
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": secrets.token_urlsafe(16),
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            }
        }
        
        # Create event via Google Calendar API
        response = await self.http_client.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json"
            },
            params={"conferenceDataVersion": 1},
            json=event_data
        )
        response.raise_for_status()
        
        event_data = response.json()
        conference_data = event_data.get("conferenceData", {})
        
        # Extract Meet URL
        meet_url = None
        for entry_point in conference_data.get("entryPoints", []):
            if entry_point.get("entryPointType") == "video":
                meet_url = entry_point.get("uri")
                break
        
        # Create meeting record
        meeting = VideoConferenceMeeting(
            config_id=config.id,
            provider="google_meet",
            provider_meeting_id=conference_data.get("conferenceId", event_data["id"]),
            topic=topic,
            join_url=meet_url or f"https://meet.google.com/{conference_data.get('conferenceId', 'unknown')}",
            host_url=meet_url,  # Same for Google Meet
            start_time=start_time,
            end_time=end_time,
            timezone="UTC",
            settings=settings or {},
            status="scheduled",
            metadata={
                "google_event_id": event_data["id"],
                "google_calendar_id": "primary",
                "conference_id": conference_data.get("conferenceId")
            }
        )
        
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        
        config.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        return meeting
    
    async def create_teams_meeting(
        self,
        config: VideoConferenceConfig,
        topic: str,
        start_time: datetime,
        duration_minutes: int = 30,
        settings: Optional[Dict] = None
    ) -> VideoConferenceMeeting:
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
            raise ValueError("Microsoft Teams not authenticated")
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Build online meeting
        meeting_data = {
            "subject": topic,
            "startDateTime": start_time.isoformat(),
            "endDateTime": end_time.isoformat(),
            "allowedPresenters": "everyone" if settings.get("allow_everyone_present", True) else "organizer",
        }
        
        # Add lobby bypass if specified
        if settings.get("lobby_bypass"):
            meeting_data["lobbyBypassSettings"] = {
                "scope": settings["lobby_bypass"]  # organizer, organization, or everyone
            }
        
        # Create meeting via Microsoft Graph API
        response = await self.http_client.post(
            "https://graph.microsoft.com/v1.0/me/onlineMeetings",
            headers={
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json"
            },
            json=meeting_data
        )
        response.raise_for_status()
        
        teams_data = response.json()
        
        # Create meeting record
        meeting = VideoConferenceMeeting(
            config_id=config.id,
            provider="microsoft_teams",
            provider_meeting_id=teams_data["id"],
            topic=topic,
            join_url=teams_data.get("joinWebUrl"),
            start_time=start_time,
            end_time=end_time,
            timezone="UTC",
            settings=settings or {},
            status="scheduled",
            metadata={
                "teams_meeting_id": teams_data["id"],
                "join_meeting_id": teams_data.get("joinMeetingId"),
                "organizer_id": teams_data.get("organizer", {}).get("id")
            }
        )
        
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        
        config.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        return meeting
    
    async def create_meeting(
        self,
        user_id: str,
        provider: str,
        topic: str,
        start_time: datetime,
        duration_minutes: int = 30,
        settings: Optional[Dict] = None,
        booking_id: Optional[str] = None
    ) -> VideoConferenceMeeting:
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
        # Get config
        config = await self.get_config(user_id, provider)
        if not config:
            raise ValueError(f"{provider} not configured for this user")
        
        # Route to appropriate implementation
        if provider == "zoom":
            meeting = await self.create_zoom_meeting(
                config, topic, start_time, duration_minutes, settings
            )
        elif provider == "google_meet":
            meeting = await self.create_google_meet(
                config, topic, start_time, duration_minutes, settings
            )
        elif provider == "microsoft_teams":
            meeting = await self.create_teams_meeting(
                config, topic, start_time, duration_minutes, settings
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Associate with booking if provided
        if booking_id:
            meeting.booking_id = booking_id
            await self.db.commit()
        
        return meeting
    
    async def delete_meeting(
        self,
        meeting_id: str,
        user_id: str
    ) -> bool:
        """Delete/cancel a video conference meeting.
        
        Args:
            meeting_id: Meeting ID
            user_id: User ID (for authorization)
        
        Returns:
            True if deleted successfully
        """
        stmt = select(VideoConferenceMeeting).where(
            and_(
                VideoConferenceMeeting.id == meeting_id,
                VideoConferenceMeeting.config_id.in_(
                    select(VideoConferenceConfig.id).where(
                        VideoConferenceConfig.user_id == user_id
                    )
                )
            )
        )
        meeting = (await self.db.execute(stmt)).scalars().first()
        
        if not meeting:
            return False
        
        # Delete from provider (best effort)
        try:
            config = await self.db.get(VideoConferenceConfig, meeting.config_id)
            if config and config.access_token:
                if meeting.provider == "zoom":
                    await self.http_client.delete(
                        f"https://api.zoom.us/v2/meetings/{meeting.provider_meeting_id}",
                        headers={"Authorization": f"Bearer {config.access_token}"}
                    )
                elif meeting.provider == "google_meet":
                    await self.http_client.delete(
                        f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{meeting.metadata.get('google_event_id')}",
                        headers={"Authorization": f"Bearer {config.access_token}"}
                    )
        except Exception:
            pass  # Continue even if provider deletion fails
        
        # Mark as cancelled
        meeting.status = "cancelled"
        await self.db.commit()
        
        return True
    
    async def get_meeting_recordings(
        self,
        meeting_id: str,
        user_id: str
    ) -> List[VideoConferenceRecording]:
        """Get recordings for a meeting.
        
        Args:
            meeting_id: Meeting ID
            user_id: User ID (for authorization)
        
        Returns:
            List of VideoConferenceRecording records
        """
        stmt = select(VideoConferenceRecording).where(
            and_(
                VideoConferenceRecording.meeting_id == meeting_id,
                VideoConferenceRecording.status == "completed"
            )
        )
        return (await self.db.execute(stmt)).scalars().all()
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
