from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from backend.auth.schemes import get_current_user
from backend.services.zoom import zoom_service

router = APIRouter(prefix="/zoom", tags=["zoom"])

class CreateMeetingRequest(BaseModel):
    topic: str = Field(..., example="GraftAI Strategy Session")
    start_time: str = Field(..., description="ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ", example="2026-03-31T10:00:00Z")
    duration: int = Field(60, description="Duration in minutes", example=60)
    timezone: str = Field("UTC", example="UTC")

class CreateMeetingResponse(BaseModel):
    id: int
    topic: str
    join_url: str
    start_url: Optional[str] = None
    status: str

@router.post("/create-meeting", response_model=CreateMeetingResponse)
async def create_zoom_meeting(
    payload: CreateMeetingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    SaaS-Grade endpoint to create a Zoom meeting.
    Requires authentication. Uses Server-to-Server OAuth.
    """
    try:
        meeting_data = await zoom_service.create_meeting(
            topic=payload.topic,
            start_time=payload.start_time,
            duration=payload.duration,
            timezone=payload.timezone
        )
        
        if not meeting_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Zoom meeting. Check backend logs for details."
            )
            
        return {
            "id": meeting_data.get("id"),
            "topic": meeting_data.get("topic"),
            "join_url": meeting_data.get("join_url"),
            "start_url": meeting_data.get("start_url"),
            "status": meeting_data.get("status")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
