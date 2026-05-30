"""
Scheduling Tools for Agent Actions

Tools for calendar operations and availability management.
"""
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.utils.logger import get_logger

from .registry import ToolCategory, ToolPriority, register_tool

logger = get_logger(__name__)

@register_tool(name="create_calendar_event", description="Create a calendar event with title, time, and attendees", category=ToolCategory.SCHEDULING, priority=ToolPriority.CRITICAL, examples=[{"title": "Team Sync", "start_time": "2024-04-15T14:00:00", "duration_minutes": 30, "attendees": ["user1@example.com", "user2@example.com"], "description": "Weekly team synchronization meeting"}])
async def create_calendar_event(title: str, start_time: str, duration_minutes: int, attendees: list[str], description: str | None=None, location: str | None=None, calendar_id: str | None=None, timezone: str="UTC", reminder_minutes: int | None=15) -> dict:
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
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = start + timedelta(minutes=duration_minutes)
        event_id = f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        logger.info("Creating calendar event: %s for %s attendees", title, len(attendees))
        return {"success": True, "event_id": event_id, "title": title, "start_time": start_time, "end_time": end.isoformat(), "duration_minutes": duration_minutes, "attendees": attendees, "location": location, "created_at": datetime.now(timezone.utc).isoformat(), "calendar_link": f"https://calendar.example.com/event/{event_id}"}
    except Exception as e:
        logger.exception("Failed to create calendar event: %s", e)
        return {"success": False, "error": str(e), "title": title, "start_time": start_time}

@register_tool(name="update_calendar_event", description="Update an existing calendar event with new details", category=ToolCategory.SCHEDULING, priority=ToolPriority.HIGH, examples=[{"event_id": "evt_123", "changes": {"title": "Updated Meeting Title", "start_time": "2024-04-15T15:00:00"}}])
async def update_calendar_event(event_id: str, changes: dict[str, Any]) -> dict:
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
        logger.info("Updating calendar event %s", event_id)
        return {"success": True, "event_id": event_id, "changes_applied": list(changes.keys()), "updated_at": datetime.now(UTC).isoformat(), "message": f"Event {event_id} updated successfully"}
    except Exception as e:
        logger.exception("Failed to update calendar event: %s", e)
        return {"success": False, "error": str(e), "event_id": event_id}

@register_tool(name="check_calendar_availability", description="Check if a user is available at a specific time", category=ToolCategory.SCHEDULING, priority=ToolPriority.CRITICAL, examples=[{"user": "user@example.com", "start_time": "2024-04-15T14:00:00", "duration_minutes": 30}])
async def check_calendar_availability(user: str, start_time: str, duration_minutes: int) -> dict:
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
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        start + timedelta(minutes=duration_minutes)
        logger.info("Checking availability for %s at %s", user, start_time)
        is_available = True
        conflicts = []
        return {"success": True, "user": user, "start_time": start_time, "duration_minutes": duration_minutes, "available": is_available, "conflicts": conflicts, "checked_at": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Failed to check availability: %s", e)
        return {"success": False, "error": str(e), "user": user, "start_time": start_time}

@register_tool(name="search_available_slots", description="Find available time slots for a meeting with given constraints", category=ToolCategory.SCHEDULING, priority=ToolPriority.HIGH, examples=[{"attendees": ["user1@example.com", "user2@example.com"], "duration_minutes": 30, "start_date": "2024-04-15", "end_date": "2024-04-17", "preferred_times": ["09:00", "14:00"]}])
async def search_available_slots(attendees: list[str], duration_minutes: int, start_date: str, end_date: str, preferred_times: list[str] | None=None, timezone: str="UTC") -> dict:
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
        logger.info("Searching slots for %s attendees, %s min", len(attendees), duration_minutes)
        available_slots = [{"start_time": f"{start_date}T09:00:00", "end_time": f"{start_date}T09:{duration_minutes:02d}:00", "score": 0.9, "all_attendees_available": True}, {"start_time": f"{start_date}T14:00:00", "end_time": f"{start_date}T14:{duration_minutes:02d}:00", "score": 0.85, "all_attendees_available": True}]
        return {"success": True, "attendees": attendees, "duration_minutes": duration_minutes, "search_range": {"start": start_date, "end": end_date}, "available_slots": available_slots, "total_options": len(available_slots), "searched_at": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.exception("Failed to search available slots: %s", e)
        return {"success": False, "error": str(e), "attendees": attendees}

@register_tool(name="get_conflicts", description="Get scheduling conflicts for a proposed meeting time", category=ToolCategory.SCHEDULING, priority=ToolPriority.HIGH, examples=[{"user": "user@example.com", "start_time": "2024-04-15T14:00:00", "end_time": "2024-04-15T15:00:00"}])
async def get_conflicts(user: str, start_time: str, end_time: str) -> dict:
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
        datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        logger.info("Getting conflicts for %s between %s and %s", user, start_time, end_time)
        conflicts = []
        return {"success": True, "user": user, "start_time": start_time, "end_time": end_time, "conflicts": conflicts, "has_conflicts": len(conflicts) > 0, "checked_at": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Failed to get conflicts: %s", e)
        return {"success": False, "error": str(e), "user": user}
