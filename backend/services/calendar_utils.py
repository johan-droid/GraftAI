import hashlib
from typing import Any, Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import EventTable


def _normalize_event_title(value: Any, default: str = "Untitled event") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def generate_fingerprint(event_data: Dict[str, Any]) -> str:
    """Generates a unique hash for a calendar event based on time and title."""
    start = str(event_data.get("start_time"))
    end = str(event_data.get("end_time"))
    title = _normalize_event_title(event_data.get("title")).lower()
    return hashlib.sha256(f"{start}|{end}|{title}".encode("utf-8")).hexdigest()


async def simple_upsert_event(
    db: AsyncSession,
    user_id: str,
    source: str,
    event_data: Dict[str, Any],
) -> EventTable:
    """Upsert a calendar event scanned from an external provider."""
    fingerprint = generate_fingerprint(event_data)
    external_id = event_data.get("external_id")

    stmt = select(EventTable).where(
        and_(
            EventTable.user_id == user_id,
            (EventTable.external_id == external_id)
            | (EventTable.fingerprint == fingerprint),
        )
    )
    existing_event = (await db.execute(stmt)).scalars().first()

    if existing_event:
        for key, value in event_data.items():
            if key == "title":
                value = _normalize_event_title(value)
            if hasattr(existing_event, key) and value is not None:
                setattr(existing_event, key, value)
        existing_event.fingerprint = fingerprint
        return existing_event

    db_event_data = {
        k: v
        for k, v in event_data.items()
        if hasattr(EventTable, k) and k not in ["fingerprint", "source"]
    }
    db_event_data["title"] = _normalize_event_title(db_event_data.get("title"))
    new_event = EventTable(
        user_id=user_id,
        source=source,
        fingerprint=fingerprint,
        **db_event_data,
    )
    db.add(new_event)
    return new_event
