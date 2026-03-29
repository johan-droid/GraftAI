from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ScheduleEvent(BaseModel):
    """Schedule a new event or meeting on the user's calendar with intelligent categorization."""
    title: str = Field(..., description="The title of the event")
    category: str = Field(..., description="The type of event. Must be one of: meeting, task, birthday, deep_work, personal, out_of_office")
    start_time: str = Field(..., description="ISO 8601 formatted start time (e.g., 2024-03-28T10:00:00Z)")
    duration_minutes: int = Field(default=30, description="Duration of the event in minutes")
    is_meeting: bool = Field(default=True, description="True if this is a professional meeting requiring a link, False otherwise")
    platform: Optional[str] = Field(None, description="Meeting platform: google_meet, zoom, or teams")
    attendees: List[str] = Field(default_factory=list, description="List of attendee email addresses")
    agenda: Optional[str] = Field(None, description="Brief agenda or description")
    priority: Optional[str] = Field("medium", description="Priority level: high, medium, low")

class UpdateMeeting(BaseModel):
    """Update an existing meeting's time or title."""
    event_id: int = Field(..., description="The numeric ID of the event to update")
    new_start_time: Optional[str] = Field(None, description="New ISO 8601 formatted start time")
    new_title: Optional[str] = Field(None, description="New title for the meeting")

class DeleteMeeting(BaseModel):
    """Remove a meeting from the user's calendar."""
    event_id: int = Field(..., description="The numeric ID of the event to delete")

class SearchSchedule(BaseModel):
    """Search the user's schedule for a specific date or keyword."""
    query: str = Field(..., description="Search query or date (e.g., 'tomorrow', 'next Monday', 'Project X')")

class GetTimeAnalytics(BaseModel):
    """Analyze the user's time expenditure over the last 7-30 days."""
    days: int = Field(default=7, description="Number of days to analyze (max 30)")

class FetchProjectNotes(BaseModel):
    """Retrieve detailed notes and context from uploaded project documents."""
    project_keyword: str = Field(..., description="Keyword or project name to search for in documents")
