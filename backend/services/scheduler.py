import logging
from datetime import datetime
from typing import List, Optional
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import pytz

from backend.models.tables import EventTable, UserTable, UserTokenTable
from backend.services.notifications import notify_event_created, notify_event_updated, notify_event_deleted
from backend.services.integrations.google_calendar import create_google_event, update_google_event, delete_google_event
from backend.services.integrations.ms_graph import create_ms_event, update_ms_event, delete_ms_event
from backend.services.integrations.zoom import create_zoom_meeting, update_zoom_meeting, delete_zoom_meeting

logger = logging.getLogger(__name__)

def to_utc(dt: datetime) -> datetime:
    if dt is None: return None
    if dt.tzinfo is None: return pytz.UTC.localize(dt)
    return dt.astimezone(pytz.UTC)

async def _create_external_event(db: AsyncSession, user_id: str, provider: str, event_details: dict) -> Optional[dict]:
    stmt = select(UserTokenTable).where(
        and_(
            UserTokenTable.user_id == user_id,
            UserTokenTable.provider == provider,
            UserTokenTable.is_active == True,
        )
    )
    token = (await db.execute(stmt)).scalars().first()
    if not token:
        return None

    try:
        if provider == "google":
            res = await create_google_event({
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "scopes": token.scopes if hasattr(token, "scopes") else None,
            }, event_details)
            return {
                "external_id": res.get("id"),
                "meeting_url": (
                    res.get("hangoutLink")
                    or res.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
                    or res.get("htmlLink")
                ),
                "source": "google"
            }
        if provider == "microsoft":
            res = await create_ms_event({
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "scopes": token.scopes if hasattr(token, "scopes") else None,
            }, event_details)
            return {
                "external_id": res.get("id"),
                "meeting_url": (
                    res.get("onlineMeeting", {}).get("joinUrl")
                    or res.get("onlineMeetingUrl")
                    or res.get("webLink")
                ),
                "source": "microsoft"
            }
        if provider == "zoom":
            res = await create_zoom_meeting(db, user_id, event_details)
            return {
                "external_id": res.get("id"),
                "meeting_url": res.get("join_url"),
                "source": "zoom"
            }
    except Exception as e:
        logger.error(f"External event creation failed for {provider}: {e}")
    return None

async def _safe_notify(db: AsyncSession, action: str, user_id: str, event: EventTable):
    """Triggers email and in-app notifications directly."""
    try:
        user = await db.get(UserTable, user_id)
        if not user:
            return
        
        recipients = [user.email]
        event_dict = {
            "id": event.id,
            "title": event.title,
            "start_time": event.start_time.strftime("%A, %B %d at %I:%M %p"),
            "end_time": event.end_time.strftime("%A, %B %d at %I:%M %p"),
            "meeting_link": event.meeting_url,
            "is_meeting": event.is_meeting,
        }
        
        if action == "created":
            await notify_event_created(recipients, [], event_dict)
        elif action == "updated":
            await notify_event_updated(recipients, [], event_dict)
        elif action == "deleted":
            await notify_event_deleted(recipients, [], event_dict)
    except Exception as e:
        logger.error(f"Notification failed: {e}")


async def push_event_to_external_calendar(db: AsyncSession, event_id: str) -> Optional[EventTable]:
    """Pushes a local event to the user's configured external calendar provider."""
    event = await db.get(EventTable, event_id)
    if not event or not event.meeting_provider or event.external_id:
        return event

    event_details = {
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "attendees": event.attendees or [],
        "is_meeting": event.is_meeting,
    }

    result = await _create_external_event(db, event.user_id, event.meeting_provider, event_details)
    if not result:
        return event

    event.external_id = result.get("external_id") or event.external_id
    event.meeting_url = result.get("meeting_url") or event.meeting_url
    event.source = result.get("source") or event.source
    await db.commit()
    await db.refresh(event)
    return event


async def get_events_for_range(db: AsyncSession, user_id: str, start: datetime, end: datetime) -> List[dict]:
    """Direct DB fetch without caching layers."""
    stmt = select(EventTable).where(
        and_(
            EventTable.user_id == user_id,
            EventTable.start_time < end,
            EventTable.end_time > start
        )
    ).order_by(EventTable.start_time.asc())
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    # Return as simple dicts for the frontend
    return [{c.name: getattr(e, c.name) for c in e.__table__.columns} for e in events]

async def create_event(
    db: AsyncSession,
    event_data: dict,
    background_tasks: Optional[BackgroundTasks] = None,
    commit: bool = True,
    perform_external: bool = True,
    notify: bool = True,
) -> EventTable:
    """Synchronous-first event creation with direct conflict check."""
    user_id = event_data.get("user_id")
    st, et = to_utc(event_data.get("start_time")), to_utc(event_data.get("end_time"))

    # Conflict check
    conflict_stmt = select(EventTable).where(
        and_(EventTable.user_id == user_id, EventTable.start_time < et, EventTable.end_time > st)
    )
    if (await db.execute(conflict_stmt)).scalars().first():
        logger.warning(f"Conflict detected for user {user_id}")

    db_event_data = {k: v for k, v in event_data.items() if k in EventTable.__table__.columns.keys()}
    new_event = EventTable(**db_event_data)
    new_event.start_time, new_event.end_time = st, et
    db.add(new_event)
    await db.flush()  # Get ID

    should_push_external = bool(event_data.get("is_meeting") or event_data.get("meeting_provider"))
    if perform_external and should_push_external:
        provider_preference = ["google", "microsoft", "zoom"]
        event_provider = event_data.get("meeting_provider")
        if event_provider:
            provider_preference = [event_provider]

        for provider in provider_preference:
            result = await _create_external_event(db, user_id, provider, event_data)
            if result:
                new_event.external_id = result.get("external_id") or new_event.external_id
                new_event.meeting_url = result.get("meeting_url") or new_event.meeting_url
                new_event.is_meeting = True
                new_event.meeting_provider = new_event.meeting_provider or provider
                new_event.source = result.get("source")
                break

    if commit:
        await db.commit()
    await db.refresh(new_event)

    if notify:
        if background_tasks:
            background_tasks.add_task(_safe_notify, db, "created", user_id, new_event)
        else:
            await _safe_notify(db, "created", user_id, new_event)

    return new_event

async def update_event(db: AsyncSession, event_id: str, user_id: str, update_data: dict, background_tasks: Optional[BackgroundTasks] = None) -> Optional[EventTable]:
    event = await db.get(EventTable, event_id)
    if not event or str(event.user_id) != str(user_id): return None
    
    for k, v in update_data.items():
        if hasattr(event, k): setattr(event, k, v)
    
    event.start_time = to_utc(event.start_time)
    event.end_time = to_utc(event.end_time)
    
    # Push update or create external event for new meeting requests
    try:
        if event.external_id:
            if event.source == "google":
                await update_google_event(db, user_id, event.external_id, update_data)
            elif event.source == "microsoft":
                await update_ms_event(db, user_id, event.external_id, update_data)
            elif event.source == "zoom":
                await update_zoom_meeting(db, user_id, event.external_id, update_data)
        elif event.is_meeting and event.meeting_provider:
            provider = event.meeting_provider
            event_details = {
                "title": event.title,
                "description": event.description,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "attendees": event.attendees or [],
                "is_meeting": True,
            }
            if provider == "google":
                result = await _create_external_event(db, user_id, "google", event_details)
            elif provider == "microsoft":
                result = await _create_external_event(db, user_id, "microsoft", event_details)
            elif provider == "zoom":
                result = await _create_external_event(db, user_id, "zoom", event_details)
            else:
                result = None

            if result:
                event.external_id = result.get("external_id")
                event.meeting_url = result.get("meeting_url")
                event.source = result.get("source")
    except Exception as e:
        logger.error(f"External update/create failed: {e}")

    await db.commit()
    await db.refresh(event)
    
    if background_tasks:
        background_tasks.add_task(_safe_notify, db, "updated", user_id, event)
    else:
        await _safe_notify(db, "updated", user_id, event)
        
    return event

async def delete_event(db: AsyncSession, event_id: str, user_id: str, background_tasks: Optional[BackgroundTasks] = None) -> bool:
    event = await db.get(EventTable, event_id)
    if not event or str(event.user_id) != str(user_id): return False
    
    if event.external_id:
        try:
            if event.source == "google": await delete_google_event(db, user_id, event.external_id)
            elif event.source == "microsoft": await delete_ms_event(db, user_id, event.external_id)
            elif event.source == "zoom": await delete_zoom_meeting(db, user_id, event.external_id)
        except Exception as e:
            logger.error(f"External delete failed: {e}")

    await _safe_notify(db, "deleted", user_id, event) # Notify before deletion
    await db.delete(event)
    await db.commit()
    return True
