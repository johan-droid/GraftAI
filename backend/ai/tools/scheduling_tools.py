"""
Scheduling Tools for Agent Actions

Tools for calendar operations and availability management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from backend.utils.logger import get_logger
from .registry import register_tool, ToolCategory, ToolPriority

logger = get_logger(__name__)


@register_tool(
    name="create_calendar_event",
    description="Create a calendar event with title, time, and attendees",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.CRITICAL,
    examples=[
        {
            "title": "Team Sync",
            "start_time": "2024-04-15T14:00:00",
            "duration_minutes": 30,
            "attendees": ["user1@example.com", "user2@example.com"],
            "description": "Weekly team synchronization meeting"
        }
    ]
)
async def create_calendar_event(
    title: str,
    start_time: str,
    duration_minutes: int,
    attendees: List[str],
    description: Optional[str] = None,
    location: Optional[str] = None,
    calendar_id: Optional[str] = None,
    timezone: str = "UTC",
    reminder_minutes: Optional[int] = 15
) -> dict:
    """
    Create a calendar event.
    
    Args:
        title: Event title
        start_time: Event start time (ISO format)
        duration_minutes: Event duration
        attendees: List of attendee email addresses
        description: Optional event description
        location: Optional event location
        calendar_id: Optional calendar ID (uses primary if not specified)
        timezone: Timezone for the event
        reminder_minutes: Minutes before event to send reminder (default 15)
    
    Returns:
        Dict with event_id and details
    """
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = start + timedelta(minutes=duration_minutes)
        
        event_id = f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Creating calendar event: {title} for {len(attendees)} attendees")
        
        # TODO: Integrate with calendar API (Google Calendar, Outlook, etc.)
        # event = calendar_client.events.insert(
        #     calendarId=calendar_id or 'primary',
        #     body={
        #         'summary': title,
        #         'description': description,
        #         'start': {'dateTime': start.isoformat(), 'timeZone': timezone},
        #         'end': {'dateTime': end.isoformat(), 'timeZone': timezone},
        #         'attendees': [{'email': e} for e in attendees],
        #         'location': location,
        #         'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': reminder_minutes}]}
        #     }
        # )
        
        return {
            "success": True,
            "event_id": event_id,
            "title": title,
            "start_time": start_time,
            "end_time": end.isoformat(),
            "duration_minutes": duration_minutes,
            "attendees": attendees,
            "location": location,
"created_at": datetime.now(timezone.utc).isoformat(),
            "calendar_link": f"https://calendar.example.com/event/{event_id}"
        }
    
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        return {
            "success": False,
            "error": str(e),
            "title": title,
            "start_time": start_time
        }


@register_tool(
    name="update_calendar_event",
    description="Update an existing calendar event with new details",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.HIGH,
    examples=[
        {
            "event_id": "evt_123",
            "changes": {"title": "Updated Meeting Title", "start_time": "2024-04-15T15:00:00"}
        }
    ]
)
async def update_calendar_event(
    event_id: str,
    changes: Dict[str, Any]
) -> dict:
    """
    Update an existing calendar event.
    
    Args:
        event_id: ID of the event to update
        changes: Dict of fields to update (title, start_time, duration_minutes, 
                description, location, attendees, etc.)
    
    Returns:
        Dict with update status and new event details
    """
    try:
        logger.info(f"Updating calendar event {event_id}")
        
        # TODO: Integrate with calendar API
        # event = calendar_client.events.get(calendarId='primary', eventId=event_id)
        # for key, value in changes.items():
        #     event[key] = value
        # calendar_client.events.update(calendarId='primary', eventId=event_id, body=event)
        
        return {
            "success": True,
            "event_id": event_id,
            "changes_applied": list(changes.keys()),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Event {event_id} updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to update calendar event: {e}")
        return {
            "success": False,
            "error": str(e),
            "event_id": event_id
        }


@register_tool(
    name="check_calendar_availability",
    description="Check if a user is available at a specific time",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.CRITICAL,
    examples=[
        {
            "user": "user@example.com",
            "start_time": "2024-04-15T14:00:00",
            "duration_minutes": 30
        }
    ]
)
async def check_calendar_availability(
    user: str,
    start_time: str,
    duration_minutes: int
) -> dict:
    """
    Check if a user is available at a specific time.
    
    Args:
        user: User email address
        start_time: Time to check (ISO format)
        duration_minutes: Duration needed
    
    Returns:
        Dict with availability status and conflicting events
    """
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = start + timedelta(minutes=duration_minutes)
        
        logger.info(f"Checking availability for {user} at {start_time}")
        
        # TODO: Query calendar API for availability
        # busy_times = calendar_client.freebusy.query(
        #     timeMin=start.isoformat(),
        #     timeMax=end.isoformat(),
        #     items=[{'id': user}]
        # )
        
        # For demo, assume available
        is_available = True
        conflicts = []
        
        return {
            "success": True,
            "user": user,
            "start_time": start_time,
            "duration_minutes": duration_minutes,
            "available": is_available,
            "conflicts": conflicts,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to check availability: {e}")
        return {
            "success": False,
            "error": str(e),
            "user": user,
            "start_time": start_time
        }


@register_tool(
    name="search_available_slots",
    description="Find available time slots for a meeting with given constraints",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.HIGH,
    examples=[
        {
            "attendees": ["user1@example.com", "user2@example.com"],
            "duration_minutes": 30,
            "start_date": "2024-04-15",
            "end_date": "2024-04-17",
            "preferred_times": ["09:00", "14:00"]
        }
    ]
)
async def search_available_slots(
    attendees: List[str],
    duration_minutes: int,
    start_date: str,
    end_date: str,
    preferred_times: Optional[List[str]] = None,
    timezone: str = "UTC"
) -> dict:
    """
    Search for available meeting slots.
    
    Args:
        attendees: List of attendee emails
        duration_minutes: Meeting duration needed
        start_date: Search start date (YYYY-MM-DD)
        end_date: Search end date (YYYY-MM-DD)
        preferred_times: Optional list of preferred times (HH:MM format)
        timezone: Timezone for search
    
    Returns:
        Dict with available slots ranked by preference
    """
    try:
        logger.info(f"Searching slots for {len(attendees)} attendees, {duration_minutes} min")
        
        # TODO: Query freebusy for all attendees
        # Find overlapping free slots
        # Score by preferred times
        
        # For demo, return sample slots
        available_slots = [
            {
                "start_time": f"{start_date}T09:00:00",
                "end_time": f"{start_date}T09:{duration_minutes:02d}:00",
                "score": 0.9,
                "all_attendees_available": True
            },
            {
                "start_time": f"{start_date}T14:00:00",
                "end_time": f"{start_date}T14:{duration_minutes:02d}:00",
                "score": 0.85,
                "all_attendees_available": True
            }
        ]
        
        return {
            "success": True,
            "attendees": attendees,
            "duration_minutes": duration_minutes,
            "search_range": {"start": start_date, "end": end_date},
            "available_slots": available_slots,
            "total_options": len(available_slots),
            "searched_at": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to search available slots: {e}")
        return {
            "success": False,
            "error": str(e),
            "attendees": attendees
        }


@register_tool(
    name="get_conflicts",
    description="Get scheduling conflicts for a proposed meeting time",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.HIGH,
    examples=[
        {
            "user": "user@example.com",
            "start_time": "2024-04-15T14:00:00",
            "end_time": "2024-04-15T15:00:00"
        }
    ]
)
async def get_conflicts(
    user: str,
    start_time: str,
    end_time: str
) -> dict:
    """
    Get list of conflicting events for a time range.
    
    Args:
        user: User email
        start_time: Start of time range (ISO format)
        end_time: End of time range (ISO format)
    
    Returns:
        Dict with list of conflicting events
    """
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        logger.info(f"Getting conflicts for {user} between {start_time} and {end_time}")
        
        # TODO: Query events in time range
        # events = calendar_client.events.list(
        #     calendarId=user,
        #     timeMin=start.isoformat(),
        #     timeMax=end.isoformat()
        # )
        
        conflicts = []
        
        return {
            "success": True,
            "user": user,
            "start_time": start_time,
            "end_time": end_time,
            "conflicts": conflicts,
            "has_conflicts": len(conflicts) > 0,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get conflicts: {e}")
        return {
            "success": False,
            "error": str(e),
            "user": user
        }
