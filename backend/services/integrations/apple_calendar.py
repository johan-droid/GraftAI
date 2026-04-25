"""Apple iCloud Calendar integration via CalDAV."""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import caldav


logger = logging.getLogger(__name__)

# iCloud CalDAV URLs
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

        # Initialize CalDAV client
        self.client = caldav.DAVClient(
            url=self.caldav_url,
            username=apple_user_id,
            password=app_specific_password,
        )

    async def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars for the user."""
        try:
            principal = self.client.principal()
            calendars = principal.calendars()

            result = []
            for cal in calendars:
                result.append(
                    {
                        "id": cal.id,
                        "name": cal.name,
                        "url": str(cal.url),
                        "supported_components": cal.get_supported_components()
                        if hasattr(cal, "get_supported_components")
                        else ["VEVENT"],
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Failed to list Apple calendars: {e}")
            return []

    async def get_events(
        self,
        calendar_id: str,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Get events from a specific calendar within date range."""
        try:
            # Get calendar object
            calendar = self.client.calendar(cal_id=calendar_id)
            if not calendar:
                logger.warning(f"Calendar not found: {calendar_id}")
                return []

            # Search for events
            events = calendar.date_search(start=start, end=end)

            result = []
            for event in events:
                vevent = event.vobject_instance.vevent

                # Extract event data
                event_data = {
                    "id": event.id,
                    "icalendar_uid": str(vevent.uid.value)
                    if hasattr(vevent, "uid")
                    else None,
                    "title": str(vevent.summary.value)
                    if hasattr(vevent, "summary")
                    else "Untitled",
                    "description": str(vevent.description.value)
                    if hasattr(vevent, "description")
                    else None,
                    "location": str(vevent.location.value)
                    if hasattr(vevent, "location")
                    else None,
                    "start_time": vevent.dtstart.value
                    if hasattr(vevent, "dtstart")
                    else None,
                    "end_time": vevent.dtend.value
                    if hasattr(vevent, "dtend")
                    else None,
                    "created": vevent.created.value
                    if hasattr(vevent, "created")
                    else None,
                    "last_modified": vevent.last_modified.value
                    if hasattr(vevent, "last_modified")
                    else None,
                    "organizer": str(vevent.organizer.value)
                    if hasattr(vevent, "organizer")
                    else None,
                    "attendees": [str(att.value) for att in vevent.attendee_list]
                    if hasattr(vevent, "attendee_list")
                    else [],
                    "status": str(vevent.status.value)
                    if hasattr(vevent, "status")
                    else "confirmed",
                    "recurrence_id": str(vevent.recurrence_id.value)
                    if hasattr(vevent, "recurrence_id")
                    else None,
                    "is_recurring": hasattr(vevent, "rrule"),
                }
                result.append(event_data)

            return result
        except Exception as e:
            logger.error(f"Failed to get Apple calendar events: {e}")
            return []

    async def create_event(
        self,
        calendar_id: str,
        title: str,
        start: datetime,
        end: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Create a new event in the specified calendar."""
        try:
            calendar = self.client.calendar(cal_id=calendar_id)
            if not calendar:
                logger.error(f"Calendar not found: {calendar_id}")
                return None

            # Build iCalendar data
            ical_data = self._build_ical_event(
                title=title,
                start=start,
                end=end,
                description=description,
                location=location,
                attendees=attendees,
            )

            # Add event to calendar
            event = calendar.add_event(ical_data)

            logger.info(f"Created Apple Calendar event: {event.id}")
            return event.id

        except Exception as e:
            logger.error(f"Failed to create Apple calendar event: {e}")
            return None

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        title: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> bool:
        """Update an existing event."""
        try:
            calendar = self.client.calendar(cal_id=calendar_id)
            if not calendar:
                logger.error(f"Calendar not found: {calendar_id}")
                return False

            # Get existing event
            event = calendar.event_by_uid(event_id)
            if not event:
                logger.warning(f"Event not found: {event_id}")
                return False

            # Update vevent
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

            # Save changes
            event.save()

            logger.info(f"Updated Apple Calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Apple calendar event: {e}")
            return False

    async def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event from the calendar."""
        try:
            calendar = self.client.calendar(cal_id=calendar_id)
            if not calendar:
                logger.error(f"Calendar not found: {calendar_id}")
                return False

            event = calendar.event_by_uid(event_id)
            if not event:
                logger.warning(f"Event not found: {event_id}")
                return False

            event.delete()

            logger.info(f"Deleted Apple Calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete Apple calendar event: {e}")
            return False

    async def get_busy_times(
        self,
        start: datetime,
        end: datetime,
        calendar_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get busy time windows from calendars."""
        busy_windows = []

        try:
            # Get all calendars if not specified
            if not calendar_ids:
                calendars = await self.list_calendars()
                calendar_ids = [cal["id"] for cal in calendars]

            # Query each calendar
            for cal_id in calendar_ids:
                events = await self.get_events(cal_id, start, end)

                for event in events:
                    # Skip cancelled events
                    if event.get("status") == "cancelled":
                        continue

                    # Skip all-day events (no specific times)
                    start_time = event.get("start_time")
                    end_time = event.get("end_time")

                    if isinstance(start_time, datetime) and isinstance(
                        end_time, datetime
                    ):
                        busy_windows.append(
                            {
                                "start": start_time,
                                "end": end_time,
                                "title": event.get("title"),
                                "calendar_id": cal_id,
                            }
                        )

            # Sort by start time
            busy_windows.sort(key=lambda x: x["start"])

            return busy_windows

        except Exception as e:
            logger.error(f"Failed to get Apple busy times: {e}")
            return []

    def _build_ical_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> str:
        """Build iCalendar VEVENT string."""
        uid = f"graftai-{datetime.now(timezone.utc).timestamp()}-{title[:20]}"
        dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//GraftAI//Calendar//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"SUMMARY:{title}",
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
        ]

        if description:
            lines.append(f"DESCRIPTION:{description}")

        if location:
            lines.append(f"LOCATION:{location}")

        if attendees:
            for attendee in attendees:
                lines.append(f"ATTENDEE;ROLE=REQ-PARTICIPANT:mailto:{attendee}")

        lines.extend(
            [
                "END:VEVENT",
                "END:VCALENDAR",
            ]
        )

        return "\r\n".join(lines)


# Legacy compatibility functions for calendar provider interface
async def list_apple_calendars(token_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List calendars using token data."""
    client = AppleCalendarClient(
        apple_user_id=token_data.get("apple_user_id"),
        app_specific_password=token_data.get("app_specific_password"),
    )
    return await client.list_calendars()


async def get_apple_events(
    token_data: Dict[str, Any],
    calendar_id: str,
    start: datetime,
    end: datetime,
) -> List[Dict[str, Any]]:
    """Get events from Apple calendar."""
    client = AppleCalendarClient(
        apple_user_id=token_data.get("apple_user_id"),
        app_specific_password=token_data.get("app_specific_password"),
    )
    return await client.get_events(calendar_id, start, end)


async def get_apple_busy_times(
    token_data: Dict[str, Any],
    start: datetime,
    end: datetime,
) -> List[Dict[str, Any]]:
    """Get busy times from all Apple calendars."""
    client = AppleCalendarClient(
        apple_user_id=token_data.get("apple_user_id"),
        app_specific_password=token_data.get("app_specific_password"),
    )
    return await client.get_busy_times(start, end)
