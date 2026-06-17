"""Apple iCloud Calendar integration via CalDAV."""
import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import caldav

logger = logging.getLogger(__name__)
ICLOUD_CALDAV_URL = "https://caldav.icloud.com"
ICLOUD_CALENDAR_HOME = "https://caldav.icloud.com/{apple_user_id}/calendars"

class AppleCalendarClient:
    """Client for Apple iCloud Calendar via CalDAV."""

    def __init__(self, apple_user_id: str, app_specific_password: str):
        """
        Initialize Apple Calendar client.

        Note: Apple requires app-specific passwords for CalDAV access.
        Users must generate this at https://appleid.apple.com
        """
        self.apple_user_id = apple_user_id
        self.app_specific_password = app_specific_password
        self.caldav_url = ICLOUD_CALENDAR_HOME.format(apple_user_id=apple_user_id)
        self.client = caldav.DAVClient(url=self.caldav_url, username=apple_user_id, password=app_specific_password)

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous caldav call in a thread to avoid blocking the event loop."""
        return await asyncio.to_thread(lambda: func(*args, **kwargs))

    async def list_calendars(self) -> list[dict[str, Any]]:
        """List all calendars for the user."""
        try:
            principal = await self._run_sync(self.client.principal)
            calendars = await self._run_sync(principal.calendars)
            result = []
            for cal in calendars:
                result.append({"id": cal.id, "name": cal.name, "url": str(cal.url), "supported_components": cal.get_supported_components() if hasattr(cal, "get_supported_components") else ["VEVENT"]})
            return result
        except Exception as e:
            logger.exception("Failed to list Apple calendars: %s", e)
            return []

    async def get_events(self, calendar_id: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        """Get events from a specific calendar within date range."""
        try:
            calendar = await self._run_sync(self.client.calendar, cal_id=calendar_id)
            if not calendar:
                logger.warning("Calendar not found: %s", calendar_id)
                return []
            events = await asyncio.to_thread(lambda: calendar.date_search(start=start, end=end))
            result = []
            for event in events:
                vevent = event.vobject_instance.vevent
                event_data = {"id": event.id, "icalendar_uid": str(vevent.uid.value) if hasattr(vevent, "uid") else None, "title": str(vevent.summary.value) if hasattr(vevent, "summary") else "Untitled", "description": str(vevent.description.value) if hasattr(vevent, "description") else None, "location": str(vevent.location.value) if hasattr(vevent, "location") else None, "start_time": vevent.dtstart.value if hasattr(vevent, "dtstart") else None, "end_time": vevent.dtend.value if hasattr(vevent, "dtend") else None, "created": vevent.created.value if hasattr(vevent, "created") else None, "last_modified": vevent.last_modified.value if hasattr(vevent, "last_modified") else None, "organizer": str(vevent.organizer.value) if hasattr(vevent, "organizer") else None, "attendees": [str(att.value) for att in vevent.attendee_list] if hasattr(vevent, "attendee_list") else [], "status": str(vevent.status.value) if hasattr(vevent, "status") else "confirmed", "recurrence_id": str(vevent.recurrence_id.value) if hasattr(vevent, "recurrence_id") else None, "is_recurring": hasattr(vevent, "rrule")}
                result.append(event_data)
            return result
        except Exception as e:
            logger.exception("Failed to get Apple calendar events: %s", e)
            return []

    async def create_event(self, calendar_id: str, title: str, start: datetime, end: datetime, description: str | None=None, location: str | None=None, attendees: list[str] | None=None) -> str | None:
        """Create a new event in the specified calendar."""
        try:
            calendar = await self._run_sync(self.client.calendar, cal_id=calendar_id)
            if not calendar:
                logger.error("Calendar not found: %s", calendar_id)
                return None
            ical_data = self._build_ical_event(title=title, start=start, end=end, description=description, location=location, attendees=attendees)
            event = await asyncio.to_thread(calendar.add_event, ical_data)
            logger.info("Created Apple Calendar event: %s", event.id)
            return event.id
        except Exception as e:
            logger.exception("Failed to create Apple calendar event: %s", e)
            return None

    async def update_event(self, calendar_id: str, event_id: str, title: str | None=None, start: datetime | None=None, end: datetime | None=None, description: str | None=None, location: str | None=None) -> bool:
        """Update an existing event."""
        try:
            calendar = await self._run_sync(self.client.calendar, cal_id=calendar_id)
            if not calendar:
                logger.error("Calendar not found: %s", calendar_id)
                return False
            event = await asyncio.to_thread(calendar.event_by_uid, event_id)
            if not event:
                logger.warning("Event not found: %s", event_id)
                return False
            vevent = event.vobject_instance.vevent
            if title:
                vevent.summary.value = title
            if start:
                vevent.dtstart.value = start
            if end:
                vevent.dtend.value = end
            if description:
                vevent.description.value = description
            if location:
                vevent.location.value = location
            await asyncio.to_thread(event.save)
            logger.info("Updated Apple Calendar event: %s", event_id)
            return True
        except Exception as e:
            logger.exception("Failed to update Apple calendar event: %s", e)
            return False

    async def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event from the calendar."""
        try:
            calendar = await self._run_sync(self.client.calendar, cal_id=calendar_id)
            if not calendar:
                logger.error("Calendar not found: %s", calendar_id)
                return False
            event = await asyncio.to_thread(calendar.event_by_uid, event_id)
            if not event:
                logger.warning("Event not found: %s", event_id)
                return False
            await asyncio.to_thread(event.delete)
            logger.info("Deleted Apple Calendar event: %s", event_id)
            return True
        except Exception as e:
            logger.exception("Failed to delete Apple calendar event: %s", e)
            return False

    async def get_busy_times(self, start: datetime, end: datetime, calendar_ids: list[str] | None=None) -> list[dict[str, Any]]:
        """Get busy time windows from calendars."""
        busy_windows = []
        try:
            if not calendar_ids:
                calendars = await self.list_calendars()
                calendar_ids = [cal["id"] for cal in calendars]
            for cal_id in calendar_ids:
                events = await self.get_events(cal_id, start, end)
                for event in events:
                    if event.get("status") == "cancelled":
                        continue
                    start_time = event.get("start_time")
                    end_time = event.get("end_time")
                    if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                        busy_windows.append({"start": start_time, "end": end_time, "title": event.get("title"), "calendar_id": cal_id})
            busy_windows.sort(key=lambda x: x["start"])
            return busy_windows
        except Exception as e:
            logger.exception("Failed to get Apple busy times: %s", e)
            return []

    def _build_ical_event(self, title: str, start: datetime, end: datetime, description: str | None=None, location: str | None=None, attendees: list[str] | None=None) -> str:
        """Build iCalendar VEVENT string."""
        uid = f"graftai-{datetime.now(UTC).timestamp()}-{title[:20]}"
        dtstamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GraftAI//Calendar//EN", "BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{dtstamp}", f"SUMMARY:{title}", f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}", f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}"]
        if description:
            lines.append(f"DESCRIPTION:{description}")
        if location:
            lines.append(f"LOCATION:{location}")
        if attendees:
            for attendee in attendees:
                lines.append(f"ATTENDEE;ROLE=REQ-PARTICIPANT:mailto:{attendee}")
        lines.extend(["END:VEVENT", "END:VCALENDAR"])
        return "\r\n".join(lines)

async def list_apple_calendars(token_data: dict[str, Any]) -> list[dict[str, Any]]:
    """List calendars using token data."""
    client = await asyncio.to_thread(lambda: AppleCalendarClient(apple_user_id=token_data.get("apple_user_id"), app_specific_password=token_data.get("app_specific_password")))
    return await client.list_calendars()

async def get_apple_events(token_data: dict[str, Any], calendar_id: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Get events from Apple calendar."""
    client = await asyncio.to_thread(lambda: AppleCalendarClient(apple_user_id=token_data.get("apple_user_id"), app_specific_password=token_data.get("app_specific_password")))
    return await client.get_events(calendar_id, start, end)

async def get_apple_busy_times(token_data: dict[str, Any], start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Get busy times from all Apple calendars."""
    client = await asyncio.to_thread(lambda: AppleCalendarClient(apple_user_id=token_data.get("apple_user_id"), app_specific_password=token_data.get("app_specific_password")))
    return await client.get_busy_times(start, end)
