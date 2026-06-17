import logging
from datetime import datetime
from typing import Any

from datetime import timezone
from fastapi import BackgroundTasks
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import BookingTable, EventTable, UserTable, UserTokenTable
from backend.services.integrations.google_calendar import (
    create_google_event,
    delete_google_event,
    update_google_event,
)
from backend.services.integrations.ms_graph import (
    create_ms_event,
    delete_ms_event,
    update_ms_event,
)
from backend.services.integrations.zoom import (
    create_zoom_meeting,
    delete_zoom_meeting,
    update_zoom_meeting,
)
from backend.services.notifications import (
    notify_event_created,
    notify_event_deleted,
    notify_event_updated,
)
from backend.services.token_encryption import decrypt_token_value
from backend.services.usage import increment_usage

logger = logging.getLogger(__name__)

def _normalize_event_title(value: Any, default: str="Untitled event") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default

def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

async def _get_active_token(db: AsyncSession, user_id: str, provider: str) -> UserTokenTable | None:
    stmt = select(UserTokenTable).where(and_(UserTokenTable.user_id == user_id, UserTokenTable.provider == provider, UserTokenTable.is_active))
    return (await db.execute(stmt)).scalars().first()

def _build_token_data(token: UserTokenTable) -> dict:
    access_token, _ = decrypt_token_value(token.access_token)
    refresh_token, _ = decrypt_token_value(token.refresh_token)
    if access_token is None:
        msg = f"Failed to decrypt access_token for token ID {token.id}"
        raise ValueError(msg)
    if refresh_token is None:
        msg = f"Failed to decrypt refresh_token for token ID {token.id}"
        raise ValueError(msg)
    return {"access_token": access_token, "refresh_token": refresh_token, "scopes": getattr(token, "scopes", None)}

def _normalize_provider(provider: str | None) -> str | None:
    if not provider:
        return provider
    provider = provider.strip().lower()
    if provider in {"outlook", "microsoft_outlook"}:
        return "microsoft"
    if provider in {"google_meet", "google_calendar"}:
        return "google"
    return provider

async def _create_external_event(db: AsyncSession, user_id: str, provider: str, event_details: dict) -> dict | None:
    provider = _normalize_provider(provider)
    if not provider:
        return None
    token = await _get_active_token(db, user_id, provider)
    if not token:
        return None
    token_data = _build_token_data(token)
    try:
        if provider == "google":
            res = await create_google_event(token_data, event_details)
            return {"external_id": res.get("id"), "meeting_url": res.get("hangoutLink") or res.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri") or res.get("htmlLink"), "source": "google"}
        if provider == "microsoft":
            res = await create_ms_event(token_data, event_details)
            return {"external_id": res.get("id"), "meeting_url": res.get("onlineMeeting", {}).get("joinUrl") or res.get("onlineMeetingUrl") or res.get("webLink"), "source": "microsoft"}
        if provider == "zoom":
            res = await create_zoom_meeting(db, user_id, event_details)
            return {"external_id": res.get("id"), "meeting_url": res.get("join_url"), "source": "zoom"}
    except Exception as e:
        logger.exception("External event creation failed for %s: %s", provider, e)
    return None

async def _update_external_event(db: AsyncSession, user_id: str, provider: str, external_id: str, event_details: dict) -> None:
    token = await _get_active_token(db, user_id, provider)
    if not token:
        logger.warning("No active %s token for user %s, skipping external update", provider, user_id)
        return
    token_data = _build_token_data(token)
    try:
        if provider == "google":
            await update_google_event(token_data, external_id, event_details)
        elif provider == "microsoft":
            await update_ms_event(token_data, external_id, event_details)
        elif provider == "zoom" and external_id:
            await update_zoom_meeting(db, user_id, external_id, event_details)
    except Exception as e:
        logger.exception("External event update failed for %s/%s: %s", provider, external_id, e)

async def _delete_external_event(db: AsyncSession, user_id: str, provider: str, external_id: str) -> None:
    token = await _get_active_token(db, user_id, provider)
    if not token:
        logger.warning("No active %s token for user %s, skipping external delete", provider, user_id)
        return
    token_data = _build_token_data(token)
    try:
        if provider == "google":
            await delete_google_event(token_data, external_id)
        elif provider == "microsoft":
            await delete_ms_event(token_data, external_id)
        elif provider == "zoom" and external_id:
            await delete_zoom_meeting(db, user_id, external_id)
    except Exception as e:
        logger.exception("External event delete failed for %s/%s: %s", provider, external_id, e)

async def _safe_notify(db: AsyncSession, action: str, user_id: str, event: EventTable):
    try:
        user = await db.get(UserTable, user_id)
        if not user:
            return
        recipients = [user.email]
        if event.attendees and isinstance(event.attendees, list):
            for attendee in event.attendees:
                if isinstance(attendee, dict) and attendee.get("email"):
                    recipients.append(attendee["email"])
                elif isinstance(attendee, str) and "@" in attendee:
                    recipients.append(attendee)
        recipients = list(set(recipients))
        event_dict = {"id": event.id, "title": _normalize_event_title(event.title), "start_time": event.start_time.strftime("%A, %B %d at %I:%M %p"), "end_time": event.end_time.strftime("%A, %B %d at %I:%M %p"), "meeting_link": event.meeting_url or "Local Event (No link)", "is_meeting": event.is_meeting}
        if action == "created":
            await notify_event_created(recipients, [], event_dict)
        elif action == "updated":
            await notify_event_updated(recipients, [], event_dict)
        elif action == "deleted":
            await notify_event_deleted(recipients, [], event_dict)
    except Exception as e:
        logger.exception("Notification failed: %s", e)

async def push_event_to_external_calendar(db: AsyncSession, event_id: str) -> EventTable | None:
    event = await db.get(EventTable, event_id)
    if not event or not event.meeting_provider or event.external_id:
        return event
    event_details = {"title": _normalize_event_title(event.title), "description": event.description, "start_time": event.start_time, "end_time": event.end_time, "attendees": event.attendees or [], "is_meeting": event.is_meeting}
    result = await _create_external_event(db, event.user_id, event.meeting_provider, event_details)
    if not result:
        return event
    event.external_id = result.get("external_id") or event.external_id
    event.meeting_url = result.get("meeting_url") or event.meeting_url
    event.source = result.get("source") or event.source
    await db.commit()
    await db.refresh(event)
    return event

async def get_events_for_range(db: AsyncSession, user_id: str, start: datetime, end: datetime, limit: int=100, offset: int=0) -> list[dict]:
    stmt = select(EventTable).where(and_(EventTable.user_id == user_id, not EventTable.is_deleted, EventTable.start_time < end, EventTable.end_time > start)).order_by(EventTable.start_time.asc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    events = result.scalars().all()
    rows = [{c.name: getattr(e, c.name) for c in e.__table__.columns} for e in events]
    for row in rows:
        row["title"] = _normalize_event_title(row.get("title"))
    return rows

async def create_event(db: AsyncSession, event_data: dict, background_tasks: BackgroundTasks | None=None, commit: bool=True, perform_external: bool=True, notify: bool=True) -> EventTable:
    user_id = event_data.get("user_id")
    if not isinstance(user_id, str):
        msg = "user_id is required and must be a string"
        raise ValueError(msg)
    start_time = event_data.get("start_time")
    end_time = event_data.get("end_time")
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        msg = "start_time and end_time are required and must be datetime values"
        raise ValueError(msg)
    st = to_utc(start_time)
    et = to_utc(end_time)
    conflict_stmt = select(EventTable).where(and_(EventTable.user_id == user_id, not EventTable.is_deleted, EventTable.start_time < et, EventTable.end_time > st))
    if (await db.execute(conflict_stmt)).scalars().first():
        logger.warning("Conflict detected in EventTable for user %s", user_id)
        msg = "Schedule conflict: You already have an event at this time."
        raise ValueError(msg)
    booking_conflict_stmt = select(BookingTable).where(and_(BookingTable.user_id == user_id, BookingTable.status == "confirmed", BookingTable.start_time < et, BookingTable.end_time > st))
    if (await db.execute(booking_conflict_stmt)).scalars().first():
        logger.warning("Conflict detected in BookingTable for user %s", user_id)
        msg = "Schedule conflict: A public booking already exists at this time."
        raise ValueError(msg)
    db_event_data = {k: v for k, v in event_data.items() if k in EventTable.__table__.columns}
    db_event_data["title"] = _normalize_event_title(db_event_data.get("title"))
    new_event = EventTable(**db_event_data)
    new_event.start_time = st
    new_event.end_time = et
    db.add(new_event)
    await db.flush()
    should_push_external = bool(event_data.get("is_meeting") or event_data.get("meeting_provider"))
    if perform_external and should_push_external:
        external_event_data = dict(event_data)
        external_event_data["title"] = _normalize_event_title(external_event_data.get("title"))
        provider_preference = ["google", "microsoft", "zoom"]
        event_provider = _normalize_provider(event_data.get("meeting_provider"))
        if event_provider:
            provider_preference = [event_provider]
        for provider in provider_preference:
            result = await _create_external_event(db, user_id, provider, external_event_data)
            if result:
                new_event.external_id = result.get("external_id") or new_event.external_id
                new_event.meeting_url = result.get("meeting_url") or new_event.meeting_url
                new_event.is_meeting = True
                new_event.meeting_provider = new_event.meeting_provider or provider
                source = result.get("source")
                if source:
                    new_event.source = source
    if notify:
        if background_tasks:
            background_tasks.add_task(_safe_notify, db, "created", user_id, new_event)
        else:
            await _safe_notify(db, "created", user_id, new_event)
    try:
        await increment_usage(db, user_id, "scheduling")
        await increment_usage(db, user_id, "api_calls")
    except Exception as e:
        logger.warning("Failed to increment usage for scheduling: %s", e)
    if commit:
        await db.commit()
        await db.refresh(new_event)
    return new_event

async def update_event(db: AsyncSession, event_id: str, user_id: str, update_data: dict, background_tasks: BackgroundTasks | None=None) -> EventTable | None:
    event = await db.get(EventTable, event_id)
    if not event or str(event.user_id) != str(user_id):
        return None
    if "start_time" in update_data or "end_time" in update_data:
        start_time = update_data.get("start_time")
        end_time = update_data.get("end_time")
        if start_time is None or end_time is None:
            msg = "Both start_time and end_time must be provided and non-null when updating event schedule."
            raise ValueError(msg)
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            msg = "start_time and end_time must be datetime values."
            raise ValueError(msg)
    for k, v in update_data.items():
        if hasattr(event, k):
            setattr(event, k, v)
    event.title = _normalize_event_title(event.title)
    event.start_time = to_utc(event.start_time)
    event.end_time = to_utc(event.end_time)
    event_details = {"title": _normalize_event_title(event.title), "description": event.description, "start_time": event.start_time, "end_time": event.end_time, "attendees": event.attendees or [], "is_meeting": event.is_meeting}
    try:
        if event.external_id and event.source:
            await _update_external_event(db, user_id, event.source, event.external_id, event_details)
        elif event.is_meeting and event.meeting_provider:
            result = await _create_external_event(db, user_id, event.meeting_provider, event_details)
            if result:
                event.external_id = result.get("external_id")
                event.meeting_url = result.get("meeting_url")
                source = result.get("source")
                if source:
                    event.source = source
    except Exception as e:
        logger.exception("External update/create failed: %s", e)
    await db.commit()
    await db.refresh(event)
    if background_tasks:
        background_tasks.add_task(_safe_notify, db, "updated", user_id, event)
    else:
        await _safe_notify(db, "updated", user_id, event)
    return event

async def delete_event(db: AsyncSession, event_id: str, user_id: str, background_tasks: BackgroundTasks | None=None) -> bool:
    event = await db.get(EventTable, event_id)
    if not event or str(event.user_id) != str(user_id):
        return False
    if event.external_id and event.source:
        await _delete_external_event(db, user_id, event.source, event.external_id)
    await _safe_notify(db, "deleted", user_id, event)
    if hasattr(event, "soft_delete"):
        await event.soft_delete(db, deleted_by=user_id)
    else:
        await db.delete(event)
        await db.commit()
    return True
