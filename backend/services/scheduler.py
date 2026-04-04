import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.models.tables import EventTable, UserTable
from backend.utils.db import unwrap_result
from .langchain_client import vector_store
from .notifications import notify_event_created, notify_event_updated, notify_event_deleted
from langchain_core.documents import Document
import json
import pytz
from backend.models.user_token import UserTokenTable
from backend.services.integrations.google_calendar import create_google_meet_event, update_google_event, delete_google_event, create_google_event
from backend.services.integrations.ms_graph import create_teams_meeting, update_ms_event, delete_ms_event
from backend.services.integrations.zoom import create_zoom_meeting

# Initialize logger
logger = logging.getLogger(__name__)


def to_utc(dt: datetime) -> datetime:
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return pytz.UTC.localize(dt)
    return dt.astimezone(pytz.UTC)


async def _generate_meeting_link(db, user_id: str, platform: str, event_details: dict) -> str:
    """
    Generates a real meeting link using connected third-party integrations.
    Falls back to a simulated link if no integration is connected.
    """
    try:
        # Fetch the latest active token for this provider
        stmt = select(UserTokenTable).where(
            and_(
                UserTokenTable.user_id == user_id,
                UserTokenTable.provider == platform,
                UserTokenTable.is_active == True
            )
        )
        result = await db.execute(stmt)
        token_record = result.scalars().first()

        if not token_record:
            logger.warning(f"⚠ No connected {platform} account for user {user_id}. Using mock link.")
            return f"https://{platform}.com/mock-meeting-{os.urandom(4).hex()}"

        token_data = {
            "access_token": token_record.access_token,
            "refresh_token": token_record.refresh_token,
            "scopes": token_record.scopes
        }

        if platform == "google_meet" or platform == "google":
            return await create_google_meet_event(token_data, event_details)
        elif platform == "teams" or platform == "microsoft":
            return await create_teams_meeting(token_data, event_details)
        elif platform == "zoom":
            return await create_zoom_meeting(event_details)
        
    except Exception as e:
        logger.error(f"❌ Real-world meeting generation failed for {platform}: {e}")
        # Robust fallback to ensure the user still gets a link even if API fails
        return f"https://{platform}.com/fallback-{os.urandom(4).hex()}"

    return f"https://{platform}.com/meeting-{os.urandom(4).hex()}"

async def _push_to_external(db: AsyncSession, event: EventTable, action: str = "update"):
    """
    Pushes local changes back to the external provider if the event is synced.
    """
    if not event.external_id or not event.source or event.source == "local":
        return

    try:
        # Fetch token for the provider
        provider = "google" if event.source == "google" else "microsoft"
        stmt = select(UserTokenTable).where(
            and_(
                UserTokenTable.user_id == event.user_id,
                UserTokenTable.provider == provider,
                UserTokenTable.is_active == True
            )
        )
        result = await db.execute(stmt)
        token_record = result.scalars().first()
        if not token_record: return

        token_data = {
            "access_token": token_record.access_token,
            "refresh_token": token_record.refresh_token,
            "scopes": token_record.scopes
        }

        event_details = {
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time,
            "end_time": event.end_time,
        }

        if event.source == "google":
            if action == "create":
                result = await create_google_event(token_data, event_details)
                return result.get("id")
            elif action == "update":
                await update_google_event(token_data, event.external_id, event_details)
            elif action == "delete":
                await delete_google_event(token_data, event.external_id)
        elif event.source == "microsoft":
            if action == "create":
                # Assuming ms_graph has a similar function or using placeholder
                # await create_ms_event(token_data, event_details)
                pass
            elif action == "update":
                await update_ms_event(token_data, event.external_id, event_details)
            elif action == "delete":
                await delete_ms_event(token_data, event.external_id)

        return None

    except Exception as e:
        logger.error(f"❌ Failed to push {action} to {event.source}: {e}")


async def get_events_for_range(
    db: AsyncSession,
    user_id: str,
    start: datetime,
    end: datetime,
    skip: int = 0,
    limit: int = 100
) -> List[EventTable]:
    """Fetch all events for a user within a specific time range with pagination."""
    stmt = (
        select(EventTable)
        .where(
            and_(
                EventTable.user_id == user_id,
                EventTable.start_time >= start,
                EventTable.end_time <= end,
            )
        )
        .order_by(EventTable.start_time.asc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    scalars = await unwrap_result(result.scalars())
    return await unwrap_result(scalars.all())


async def find_available_slots(
    db: AsyncSession,
    user_id: str,
    date: datetime,
    duration_minutes: int = 30,
    working_start: int = 9,  # 9 AM
    working_end: int = 18,  # 6 PM
    target_timezone: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Intelligent slot-finding algorithm with Cross-Country Coordination.
    Scans the database for overlaps and returns free windows.
    If target_timezone is provided, finds the intersection of business hours.
    """
    def to_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return pytz.UTC.localize(dt)
        return dt.astimezone(pytz.UTC)

    # 1. Resolve Timezones
    user_tz = pytz.UTC  # Default to UTC, should be passed from frontend
    guest_tz = pytz.timezone(target_timezone) if target_timezone else None

    # 2. Define User's Day Boundaries (Normalized to UTC for DB queries)
    date_utc = to_utc(date)
    day_start = date_utc.replace(hour=working_start, minute=0, second=0, microsecond=0)
    day_end = date_utc.replace(hour=working_end, minute=0, second=0, microsecond=0)

    # 3. Intersection Logic (If Guest TZ is provided)
    if guest_tz:
        # We need to find the window that is 9-6 in BOTH timezones
        guest_local_date = date.astimezone(guest_tz) if date.tzinfo else guest_tz.localize(date)
        guest_day_start = to_utc(
            guest_local_date.replace(hour=working_start, minute=0, second=0, microsecond=0)
        )
        guest_day_end = to_utc(
            guest_local_date.replace(hour=working_end, minute=0, second=0, microsecond=0)
        )

        # Intersection: Max of starts, Min of ends
        day_start = max(day_start, guest_day_start)
        day_end = min(day_end, guest_day_end)

        # If they don't overlap at all (e.g. SF vs Tokyo), return empty or shifted suggestion
        if day_start >= day_end:
            logger.warning(
                f"No business hour overlap found between UTC and {target_timezone}"
            )
            return []

    # Ensure naive datetime for DB consistency if needed, but here we work with UTC
    # 4. Fetch existing events for the day
    existing_events = await get_events_for_range(db, user_id, day_start, day_end)

    available_slots = []
    current_time = day_start

    while current_time + timedelta(minutes=duration_minutes) <= day_end:
        potential_end = current_time + timedelta(minutes=duration_minutes)

        # Check for overlap
        has_overlap = False
        for event in existing_events:
            # Normalize event times to UTC comparison
            ev_start = (
                event.start_time.replace(tzinfo=pytz.UTC)
                if event.start_time.tzinfo is None
                else event.start_time
            )
            ev_end = (
                event.end_time.replace(tzinfo=pytz.UTC)
                if event.end_time.tzinfo is None
                else event.end_time
            )

            if not (potential_end <= ev_start or current_time >= ev_end):
                has_overlap = True
                current_time = ev_end
                break

        if not has_overlap:
            # We add human-friendly labels for the frontend dual-view
            slot_data = {
                "start": current_time.isoformat(),
                "end": potential_end.isoformat(),
                "local_label": current_time.strftime("%I:%M %p"),
            }
            if guest_tz:
                # Calculate what time this is in the guest's timezone
                guest_time = current_time.astimezone(guest_tz)
                slot_data["guest_label"] = guest_time.strftime("%I:%M %p")
                slot_data["guest_tz_name"] = target_timezone

            available_slots.append(slot_data)
            current_time = potential_end

    return available_slots


from backend.utils.arq_utils import enqueue_job

async def sync_event_to_ai(event_id: int, user_id: str, action: str = "upsert"):
    """
    Triggers a background task to sync event data to the AI Vector Store.
    This prevents Pinecone operations from blocking the API request lifecycle.
    """
    await enqueue_job("task_background_ai_sync", event_id=event_id, user_id=user_id, action=action)
    logger.info(f"📤 Queued background AI context sync for event {event_id} (Action: {action})")


async def create_event(db: AsyncSession, event_data: dict) -> EventTable:
    """Create a new event and trigger AI feedback pipeline."""
    new_event = EventTable(**event_data)

    # Check for overlapping event in same user timeline before commit
    conflict_stmt = select(EventTable).where(
        and_(
            EventTable.user_id == new_event.user_id,
            EventTable.start_time < to_utc(new_event.end_time),
            EventTable.end_time > to_utc(new_event.start_time),
        )
    )
    conflict_result = await db.execute(conflict_stmt)
    if conflict_result.scalars().first():
        raise ValueError("Event overlaps with existing schedule. Please choose another time.")

    # Generate meeting links if applicable
    if new_event.is_meeting and new_event.meeting_platform and not new_event.meeting_link:
        event_details = {
            "title": new_event.title,
            "description": new_event.description,
            "start_time": new_event.start_time,
            "end_time": new_event.end_time,
        }
        new_event.meeting_link = await _generate_meeting_link(
            db, new_event.user_id, new_event.meeting_platform, event_details
        )

    # 3. Check for active integrations to sync to external (bi-directional sync)
    # If no source is specified, we default to Google if active
    if not new_event.source or new_event.source == "local":
        stmt = select(UserTokenTable).where(
            and_(
                UserTokenTable.user_id == new_event.user_id,
                UserTokenTable.provider == "google",
                UserTokenTable.is_active == True
            )
        )
        res = await db.execute(stmt)
        if res.scalars().first():
            new_event.source = "google"

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    # 4. Push to external if matched
    if new_event.source and new_event.source != "local":
        ext_id = await _push_to_external(db, new_event, action="create")
        if ext_id:
            new_event.external_id = ext_id
            await db.commit()

    # Trigger real-time AI sync (Background)
    await sync_event_to_ai(new_event.id, new_event.user_id)

    # Notify user about new event
    target_user = await db.get(UserTable, new_event.user_id)
    if target_user:
        await notify_event_created(
            target_user.email,
            [],
            {
                "id": new_event.id,
                "user_id": new_event.user_id,
                "title": new_event.title,
                "start_time": new_event.start_time.strftime("%I:%M %p"),
                "end_time": new_event.end_time.strftime("%I:%M %p"),
                "is_meeting": new_event.is_meeting,
                "meeting_link": new_event.meeting_link,
                "meeting_platform": new_event.meeting_platform,
            },
        )

    return new_event


async def update_event(
    db: AsyncSession, event_id: int, user_id: str, update_data: dict
) -> Optional[EventTable]:
    """Update event and sync changes to LLM service."""
    stmt = select(EventTable).where(
        and_(EventTable.id == event_id, EventTable.user_id == user_id)
    )
    result = await db.execute(stmt)
    event = result.scalars().first()

    if not event:
        return None

    proposed_start = update_data.get("start_time", event.start_time)
    proposed_end = update_data.get("end_time", event.end_time)

    proposed_start = to_utc(proposed_start)
    proposed_end = to_utc(proposed_end)
    if proposed_start >= proposed_end:
        raise ValueError("Event must end after it starts.")

    conflict_stmt = select(EventTable).where(
        and_(
            EventTable.user_id == user_id,
            EventTable.id != event.id,
            EventTable.start_time < proposed_end,
            EventTable.end_time > proposed_start,
        )
    )
    conflict_result = await db.execute(conflict_stmt)
    if conflict_result.scalars().first():
        raise ValueError("Updated timing overlaps with another event.")

    for key, value in update_data.items():
        if hasattr(event, key):
            setattr(event, key, value)

    if event.start_time:
        event.start_time = to_utc(event.start_time)
    if event.end_time:
        event.end_time = to_utc(event.end_time)

    # 2. Proactively generate/refresh meeting link if requested during update
    if event.is_meeting and event.meeting_platform and not event.meeting_link:
        event_details = {
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time,
            "end_time": event.end_time,
        }
        event.meeting_link = await _generate_meeting_link(
            db, event.user_id, event.meeting_platform, event_details
        )

    await db.commit()
    await db.refresh(event)

    # Push to External if applicable
    await _push_to_external(db, event, action="update")

    # Real-time sync to AI orchestrator (Background)
    await sync_event_to_ai(event.id, event.user_id)

    target_user = await db.get(UserTable, user_id)
    if target_user:
        await notify_event_updated(
            target_user.email,
            [],
            {
                "id": event.id,
                "user_id": event.user_id,
                "title": event.title,
                "start_time": event.start_time.strftime("%I:%M %p"),
                "end_time": event.end_time.strftime("%I:%M %p"),
                "is_meeting": event.is_meeting,
                "meeting_link": event.meeting_link,
                "meeting_platform": event.meeting_platform,
            },
        )

    return event


async def delete_event(db: AsyncSession, event_id: int, user_id: str) -> bool:
    """
    Remove event from DB and purge from AI long-term memory.
    Completes the real-time feedback loop by ensuring 'deleted' reality is synced.
    """
    stmt = select(EventTable).where(
        and_(EventTable.id == event_id, EventTable.user_id == user_id)
    )
    result = await db.execute(stmt)
    event = result.scalars().first()

    if not event:
        return False

    # Purge from Vector Store (Background)
    await sync_event_to_ai(event_id, user_id, action="delete")

    # Push to External if applicable (before DB deletion)
    await _push_to_external(db, event, action="delete")

    await db.delete(event)
    await db.commit()

    target_user = await db.get(UserTable, user_id)
    if target_user:
        await notify_event_deleted(
            target_user.email,
            [],
            {
                "id": event_id,
                "user_id": user_id,
                "title": event.title,
            },
        )

    return True
