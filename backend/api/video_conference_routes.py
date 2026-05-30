"""API routes for video conference integration (Zoom, Meet, Teams)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.tables import UserTable
from backend.models.video_conference import (
    VideoConferenceConfig,
    VideoConferenceMeeting,
)
from backend.services.integrations.video_conference_service import (
    VideoConferenceService,
)

router = APIRouter(prefix="/video-conference", tags=["video-conference"])

class VideoProviderConfig(BaseModel):
    """Video provider configuration."""
    provider: str = Field(..., pattern="^(zoom|google_meet|microsoft_teams|webex)$")
    is_enabled: bool = True
    is_default: bool = False
    default_settings: dict | None = None

class CreateMeetingRequest(BaseModel):
    """Create video meeting request."""
    provider: str = Field(..., pattern="^(zoom|google_meet|microsoft_teams)$")
    topic: str = Field(..., min_length=1, max_length=200)
    start_time: datetime
    duration_minutes: int = Field(default=30, ge=15, le=480)
    settings: dict | None = Field(default=None)
    booking_id: str | None = None

class MeetingResponse(BaseModel):
    """Meeting response."""
    id: str
    provider: str
    topic: str
    join_url: str
    host_url: str | None
    password: str | None
    start_time: datetime
    end_time: datetime | None
    status: str
    settings: dict

class ProviderStatusResponse(BaseModel):
    """Provider connection status."""
    provider: str
    is_connected: bool
    is_default: bool
    last_used_at: str | None

@router.get("/providers", response_model=list[dict])
async def list_providers():
    """List available video conference providers."""
    return [{"id": "zoom", "name": "Zoom", "description": "Create Zoom meetings with waiting rooms, recordings", "features": ["waiting_room", "recording", "password", "breakout_rooms"], "auth_type": "oauth"}, {"id": "google_meet", "name": "Google Meet", "description": "Native Google Meet integration via Calendar API", "features": ["live_caption", "recording", "hand_raise"], "auth_type": "oauth"}, {"id": "microsoft_teams", "name": "Microsoft Teams", "description": "Teams meetings via Microsoft Graph API", "features": ["lobby", "recording", "screen_sharing", "whiteboard"], "auth_type": "oauth"}, {"id": "webex", "name": "Cisco Webex", "description": "Webex meetings for enterprise", "features": ["waiting_room", "recording", "polling"], "auth_type": "oauth", "coming_soon": True}, {"id": "jitsi", "name": "Jitsi (meet.jit.si or self-hosted)", "description": "Lightweight Jitsi meetings; supports public meet.jit.si rooms or self-hosted Jitsi with JWT", "features": ["open_source", "no_account_required"], "auth_type": "none_or_jwt"}]

@router.get("/status", response_model=list[ProviderStatusResponse])
async def get_connection_status(db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get video conference provider connection status."""
    stmt = select(VideoConferenceConfig).where(VideoConferenceConfig.user_id == current_user.id)
    configs = (await db.execute(stmt)).scalars().all()
    return [ProviderStatusResponse(provider=c.provider, is_connected=bool(c.access_token), is_default=c.is_default, last_used_at=c.last_used_at.isoformat() if c.last_used_at else None) for c in configs]

@router.post("/connect/{provider}")
async def connect_provider(provider: str, config: VideoProviderConfig, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Connect a video conference provider."""
    stmt = select(VideoConferenceConfig).where(and_(VideoConferenceConfig.user_id == current_user.id, VideoConferenceConfig.provider == provider))
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{provider} already connected")
    new_config = VideoConferenceConfig(user_id=current_user.id, provider=provider, is_enabled=config.is_enabled, is_default=config.is_default, default_settings=config.default_settings or {})
    if config.is_default:
        stmt = select(VideoConferenceConfig).where(and_(VideoConferenceConfig.user_id == current_user.id, VideoConferenceConfig.is_default))
        existing_defaults = (await db.execute(stmt)).scalars().all()
        for ed in existing_defaults:
            ed.is_default = False
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    service = VideoConferenceService(db)
    oauth_info = service.OAUTH_ENDPOINTS.get(provider, {})
    return {"status": "pending_oauth", "config_id": new_config.id, "oauth_url": oauth_info.get("auth_url"), "scopes": oauth_info.get("scopes"), "message": f"Please complete OAuth authorization for {provider}"}

@router.post("/meetings", response_model=MeetingResponse)
async def create_meeting(request: CreateMeetingRequest, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Create a video conference meeting."""
    service = VideoConferenceService(db)
    try:
        meeting = await service.create_meeting(user_id=current_user.id, provider=request.provider, topic=request.topic, start_time=request.start_time, duration_minutes=request.duration_minutes, settings=request.settings, booking_id=request.booking_id)
        return MeetingResponse(id=meeting.id, provider=meeting.provider, topic=meeting.topic, join_url=meeting.join_url, host_url=meeting.host_url, password=meeting.password, start_time=meeting.start_time, end_time=meeting.end_time, status=meeting.status, settings=meeting.settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/meetings", response_model=list[MeetingResponse])
async def list_meetings(provider: str | None=None, status: str | None=None, limit: int=Query(default=20, le=100), db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """List video conference meetings."""
    stmt = select(VideoConferenceMeeting).join(VideoConferenceConfig).where(VideoConferenceConfig.user_id == current_user.id).order_by(desc(VideoConferenceMeeting.created_at)).limit(limit)
    if provider:
        stmt = stmt.where(VideoConferenceMeeting.provider == provider)
    if status:
        stmt = stmt.where(VideoConferenceMeeting.status == status)
    meetings = (await db.execute(stmt)).scalars().all()
    return [MeetingResponse(id=m.id, provider=m.provider, topic=m.topic, join_url=m.join_url, host_url=m.host_url, password=m.password, start_time=m.start_time, end_time=m.end_time, status=m.status, settings=m.settings) for m in meetings]

@router.get("/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get meeting details."""
    stmt = select(VideoConferenceMeeting).join(VideoConferenceConfig).where(and_(VideoConferenceMeeting.id == meeting_id, VideoConferenceConfig.user_id == current_user.id))
    meeting = (await db.execute(stmt)).scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingResponse(id=meeting.id, provider=meeting.provider, topic=meeting.topic, join_url=meeting.join_url, host_url=meeting.host_url, password=meeting.password, start_time=meeting.start_time, end_time=meeting.end_time, status=meeting.status, settings=meeting.settings)

@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Cancel/delete a meeting."""
    service = VideoConferenceService(db)
    success = await service.delete_meeting(meeting_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "success", "message": "Meeting cancelled"}

@router.get("/meetings/{meeting_id}/recordings")
async def get_meeting_recordings(meeting_id: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Get recordings for a meeting."""
    service = VideoConferenceService(db)
    recordings = await service.get_meeting_recordings(meeting_id, current_user.id)
    return [{"id": r.id, "recording_type": r.recording_type, "play_url": r.play_url, "download_url": r.download_url, "duration_seconds": r.duration_seconds, "file_size_bytes": r.file_size_bytes, "status": r.status, "created_at": r.created_at.isoformat()} for r in recordings]

@router.post("/default/{provider}")
async def set_default_provider(provider: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Set a provider as the default for new meetings."""
    stmt = select(VideoConferenceConfig).where(and_(VideoConferenceConfig.user_id == current_user.id, VideoConferenceConfig.is_default))
    existing_defaults = (await db.execute(stmt)).scalars().all()
    for ed in existing_defaults:
        ed.is_default = False
    stmt = select(VideoConferenceConfig).where(and_(VideoConferenceConfig.user_id == current_user.id, VideoConferenceConfig.provider == provider))
    config = (await db.execute(stmt)).scalars().first()
    if not config:
        raise HTTPException(status_code=404, detail=f"{provider} not connected")
    config.is_default = True
    await db.commit()
    return {"status": "success", "message": f"{provider} set as default"}

@router.delete("/disconnect/{provider}")
async def disconnect_provider(provider: str, db: AsyncSession=Depends(get_db), current_user: UserTable=Depends(get_current_user)):
    """Disconnect a video conference provider."""
    stmt = select(VideoConferenceConfig).where(and_(VideoConferenceConfig.user_id == current_user.id, VideoConferenceConfig.provider == provider))
    config = (await db.execute(stmt)).scalars().first()
    if not config:
        raise HTTPException(status_code=404, detail=f"{provider} not connected")
    if config.access_token:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                if provider == "zoom":
                    await client.post("https://zoom.us/oauth/revoke", headers={"Authorization": f"Bearer {config.access_token}"})
        except Exception:
            pass
    await db.delete(config)
    await db.commit()
    return {"status": "success", "message": f"{provider} disconnected"}
