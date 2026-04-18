"""Apple Calendar sync provider for the calendar sync system."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from backend.services.integrations.calendar_provider import CalendarSyncProvider
from backend.services.integrations.apple_calendar import AppleCalendarClient
from backend.models.tables import UserTokenTable


class AppleCalendarSyncProvider(CalendarSyncProvider):
    """Apple iCloud Calendar sync provider using CalDAV."""

    provider = "apple"
    name = "Apple Calendar"

    def __init__(self, token_record: UserTokenTable):
        super().__init__(token_record)
        # Apple uses app-specific password stored in metadata
        metadata = token_record.metadata or {}
        self.apple_user_id = metadata.get("apple_user_id")
        self.app_specific_password = metadata.get("app_specific_password")

    async def fetch_events(
        self,
        access_token: str,
        sync_token: Optional[str],
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch events from Apple Calendar.

        Note: Apple CalDAV doesn't have a sync token concept like Google/Microsoft.
        We use a date-based approach for incremental sync.
        """
        if not self.apple_user_id or not self.app_specific_password:
            return [], None

        client = AppleCalendarClient(self.apple_user_id, self.app_specific_password)

        # Parse sync token as date range (last sync time)
        if sync_token:
            try:
                last_sync = datetime.fromisoformat(sync_token)
            except ValueError:
                last_sync = datetime.utcnow() - timedelta(days=30)
        else:
            last_sync = datetime.utcnow() - timedelta(days=30)

        end = datetime.utcnow() + timedelta(days=365)

        # Get all calendars
        calendars = await client.list_calendars()

        all_events = []
        for cal in calendars:
            events = await client.get_events(cal["id"], last_sync, end)
            for event in events:
                event["calendar_id"] = cal["id"]
                all_events.append(event)

        # Return new sync token (current timestamp)
        new_sync_token = datetime.utcnow().isoformat()

        return all_events, new_sync_token

    async def get_busy_windows(
        self,
        db: Any,  # AsyncSession - avoid circular import
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Get busy time windows from Apple Calendar."""
        if not self.apple_user_id or not self.app_specific_password:
            return []

        client = AppleCalendarClient(self.apple_user_id, self.app_specific_password)
        return await client.get_busy_times(start, end)

    def normalize_event(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Apple Calendar event to standard format."""
        if item.get("status") == "cancelled":
            return {"removed": True, "external_id": item.get("icalendar_uid")}

        start_time = item.get("start_time")
        end_time = item.get("end_time")

        # Handle date-only events (all-day)
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        return {
            "external_id": item.get("icalendar_uid") or item.get("id"),
            "title": item.get("title", "Untitled Event"),
            "description": item.get("description"),
            "location": item.get("location"),
            "start_time": start_time,
            "end_time": end_time,
            "source": "apple",
            "meeting_url": None,  # Apple Calendar doesn't auto-generate meeting links
            "attendees": item.get("attendees", []),
        }


# Register provider
def get_apple_provider(
    token_record: UserTokenTable,
) -> Optional[AppleCalendarSyncProvider]:
    """Factory function to create Apple calendar provider."""
    if token_record.provider != "apple":
        return None

    # Check if we have required credentials
    metadata = token_record.metadata or {}
    if not metadata.get("apple_user_id") or not metadata.get("app_specific_password"):
        return None

    return AppleCalendarSyncProvider(token_record)
