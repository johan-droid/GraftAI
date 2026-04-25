import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import EventTable, UserTable, UserTokenTable
from backend.services.calendar_utils import simple_upsert_event
from backend.services.integrations.token_service import ensure_valid_token
from backend.services.integrations import google_calendar, ms_graph
from backend.services.token_encryption import decrypt_token_value

logger = logging.getLogger(__name__)


class CalendarSyncProvider(ABC):
    provider: str
    name: str

    def __init__(self, token_record: UserTokenTable):
        self.token_record = token_record

    async def sync(self, db: AsyncSession) -> int:
        access_token = await ensure_valid_token(
            db, self.token_record.user_id, self.provider
        )
        if not access_token:
            logger.warning(
                f"{self.name} sync skipped: invalid or expired token for user {self.token_record.user_id}"
            )
            return 0

        events, next_sync_token = await self.fetch_events(
            access_token, self.token_record.sync_token
        )
        processed = 0

        for item in events:
            normalized = self.normalize_event(item)
            if normalized.get("removed"):
                ext_id = normalized.get("external_id")
                if ext_id:
                    stmt = select(EventTable).where(
                        and_(
                            EventTable.user_id == self.token_record.user_id,
                            EventTable.is_deleted.is_(False),
                            EventTable.external_id == ext_id,
                        )
                    )
                    existing = (await db.execute(stmt)).scalars().first()
                    if existing and hasattr(existing, "soft_delete"):
                        await existing.soft_delete(db, deleted_by=self.token_record.user_id)
                    elif existing:
                        await existing.hard_delete(db)
                continue

            normalized["user_id"] = self.token_record.user_id
            await simple_upsert_event(
                db, self.token_record.user_id, self.provider, normalized
            )
            processed += 1

        if next_sync_token and next_sync_token != self.token_record.sync_token:
            self.token_record.sync_token = next_sync_token

        return processed

    @abstractmethod
    async def fetch_events(
        self,
        access_token: str,
        sync_token: Optional[str],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]: ...

    @abstractmethod
    async def get_busy_windows(
        self, db: AsyncSession, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def normalize_event(self, item: Dict[str, Any]) -> Dict[str, Any]: ...


class GoogleCalendarSyncProvider(CalendarSyncProvider):
    provider = "google"
    name = "Google Calendar"

    async def fetch_events(
        self,
        access_token: str,
        sync_token: Optional[str],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        refresh_token, _ = decrypt_token_value(self.token_record.refresh_token)
        if refresh_token is None:
            logger.error(
                f"Cannot fetch Google events. Token decryption failed for token ID {self.token_record.id}"
            )
            raise ValueError(
                f"Token decryption failed for token ID {self.token_record.id}"
            )

        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        result = await google_calendar.list_google_events(
            token_data, sync_token=sync_token
        )
        return result.get("items", []), result.get("nextSyncToken")

    async def get_busy_windows(
        self, db: AsyncSession, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        refresh_token, _ = decrypt_token_value(self.token_record.refresh_token)
        if refresh_token is None:
            logger.error(
                f"Cannot get Google busy windows. Token decryption failed for token ID {self.token_record.id}"
            )
            raise ValueError(
                f"Token decryption failed for token ID {self.token_record.id}"
            )

        token_data = {
            "access_token": await ensure_valid_token(
                db, self.token_record.user_id, "google"
            ),
            "refresh_token": refresh_token,
        }
        if not token_data["access_token"]:
            return []
        return await google_calendar.get_google_busy_times(token_data, start, end)

    def normalize_event(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if item.get("status") == "cancelled":
            return {"removed": True, "external_id": item.get("id")}

        start_str = item.get("start", {}).get("dateTime") or item.get("start", {}).get(
            "date"
        )
        end_str = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")

        return {
            "external_id": item.get("id"),
            "title": item.get("summary", "Untitled Event"),
            "description": item.get("description"),
            "location": item.get("location"),
            "start_time": self._parse_datetime(start_str),
            "end_time": self._parse_datetime(end_str),
            "source": "google",
            "meeting_url": item.get("hangoutLink") or item.get("htmlLink"),
            "attendees": [
                attendee.get("email")
                for attendee in item.get("attendees", [])
                if attendee.get("email")
            ],
        }

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


class MicrosoftGraphSyncProvider(CalendarSyncProvider):
    provider = "microsoft"
    name = "Microsoft Calendar"

    async def fetch_events(
        self,
        access_token: str,
        sync_token: Optional[str],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        result = await ms_graph.list_ms_events(access_token, delta_link=sync_token)
        return result.get("value", []), result.get("@odata.deltaLink")

    async def get_busy_windows(
        self, db: AsyncSession, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        access_token = await ensure_valid_token(
            db, self.token_record.user_id, "microsoft"
        )
        if not access_token:
            return []

        stmt = select(UserTable).where(UserTable.id == self.token_record.user_id)
        user = (await db.execute(stmt)).scalars().first()
        user_principal_name = user.email if user else None
        if not user_principal_name:
            return []

        return await ms_graph.get_ms_busy_times(
            access_token, user_principal_name, start, end
        )

    def normalize_event(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if item.get("@removed"):
            return {"removed": True, "external_id": item.get("id")}

        start_time = self._parse_datetime(item.get("start", {}).get("dateTime"))
        end_time = self._parse_datetime(item.get("end", {}).get("dateTime"))

        return {
            "external_id": item.get("id"),
            "title": item.get("subject", "Untitled Event"),
            "description": item.get("bodyPreview"),
            "location": item.get("location", {}).get("displayName"),
            "start_time": start_time,
            "end_time": end_time,
            "source": "microsoft",
            "meeting_url": item.get("onlineMeeting", {}).get("joinUrl")
            or item.get("webLink"),
            "attendees": [
                recipient.get("emailAddress", {}).get("address")
                for recipient in item.get("attendees", [])
                if recipient.get("emailAddress")
            ],
        }

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


class CalDavCalendarSyncProvider(CalendarSyncProvider):
    provider = "caldav"
    name = "CalDAV"

    async def fetch_events(
        self,
        access_token: str,
        sync_token: Optional[str],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        logger.warning(
            "CalDAV sync is not yet implemented in this provider abstraction."
        )
        return [], sync_token

    async def get_busy_windows(
        self, db: AsyncSession, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        logger.warning("CalDAV busy time fetching is not implemented.")
        return []

    def normalize_event(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {"removed": False, "external_id": None}


def get_calendar_provider_for_token(
    token_record: UserTokenTable,
) -> Optional[CalendarSyncProvider]:
    if token_record.provider == "google":
        return GoogleCalendarSyncProvider(token_record)
    if token_record.provider == "microsoft":
        return MicrosoftGraphSyncProvider(token_record)
    if token_record.provider == "caldav":
        return CalDavCalendarSyncProvider(token_record)
    if token_record.provider == "apple":
        from backend.services.integrations.apple_calendar_provider import (
            AppleCalendarSyncProvider,
        )

        return AppleCalendarSyncProvider(token_record)
    logger.warning(f"Unsupported calendar provider: {token_record.provider}")
    return None
