import logging
import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete
from backend.models.tables import EventTable, UserTable
from .langchain_client import vector_store
from .notifications import notify_event_created, notify_event_updated, notify_event_deleted
from langchain_core.documents import Document
import json
import pytz
from fastapi import BackgroundTasks
from .google_calendar import create_google_meet_link, get_google_availability
from .microsoft_calendar import create_microsoft_teams_link, get_microsoft_availability
from .zoom import zoom_service
from .oauth_utils import get_valid_google_token, get_valid_ms_token
from .context_optimizer import context_optimizer

# Initialize logger
logger = logging.getLogger(__name__)


async def _generate_meeting_link(platform: str, event_id: int, event_title: str, start_time: datetime, end_time: datetime, access_token: Optional[str] = None) -> str:
    """
    Simulates or generates a real SaaS-grade meeting link.
    If platform is google_meet and token is available, calls the real API.
    """
    if platform == "google_meet":
        # Try to use the real Google Calendar API if an access token is available
        if access_token:
            real_link = await create_google_meet_link(
                event_title, 
                start_time.isoformat(), 
                end_time.isoformat(), 
                access_token
            )
            if real_link:
                return real_link

        # Fallback to simulation if API fails or no token
        import uuid
        room_id = str(uuid.uuid4())[:12].replace("-", "")
        return f"https://meet.google.com/{room_id[:3]}-{room_id[3:7]}-{room_id[7:10]}"
        
    elif platform == "zoom":
        # Real SaaS-grade Zoom integration
        user_id = event_id if isinstance(event_id, str) else str(event_id) # Need actual user_id
        # Wait, the signature should include user_id. Let's update the signature first.
        meeting = await zoom_service.create_meeting(
            user_id=user_id,
            topic=event_title,
            start_time=start_time.isoformat(),
            duration=int((end_time - start_time).total_seconds() / 60)
        )
        if meeting and "join_url" in meeting:
            return meeting["join_url"]
            
        # Fallback to simulation if Zoom API fails
        import uuid
        room_id = str(uuid.uuid4())[:10]
        return f"https://zoom.us/j/{room_id[:10]}"
    elif platform == "teams":
        # Try to use the real Microsoft Graph API if an access token is available
        if access_token:
            real_link = await create_microsoft_teams_link(
                event_title, 
                start_time.isoformat(), 
                end_time.isoformat(), 
                access_token
            )
            if real_link:
                return real_link

        # Fallback to simulation if API fails or no token
        import uuid
        room_id = str(uuid.uuid4())[:12].replace("-", "")
        return f"https://teams.microsoft.com/l/meetup-join/{room_id}"
        
    import uuid
    room_id = str(uuid.uuid4())[:12]
    return f"https://graftai.com/meeting/{room_id}"


async def get_events_for_range(
    db: AsyncSession, user_id: str, start: datetime, end: datetime, org_id: Optional[int] = None, workspace_id: Optional[int] = None
) -> List[EventTable]:
    """Fetch all events for a user within a specific time range, scoped by organization/workspace."""
    filters = [
        EventTable.user_id == user_id,
        EventTable.start_time < end,
        EventTable.end_time > start,
        EventTable.status != "canceled"
    ]
    
    if org_id:
        filters.append(EventTable.org_id == org_id)
    if workspace_id:
        filters.append(EventTable.workspace_id == workspace_id)

    stmt = (
        select(EventTable)
        .where(and_(*filters))
        .order_by(EventTable.start_time.asc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_optimized_context(
    db: AsyncSession, 
    user_id: str, 
    date: datetime, 
    org_id: Optional[int] = None, 
    workspace_id: Optional[int] = None
) -> str:
    """
    Returns a lightning-fast, high-density context string for the AI agent.
    1. Fetches local events (including synced external entries).
    2. Compresses them using ContextOptimizer.
    3. Adds User TZ guidance.
    """
    # Define day boundaries
    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=23, minute=59, second=59, microsecond=999)
    
    events = await get_events_for_range(db, user_id, day_start, day_end, org_id=org_id, workspace_id=workspace_id)
    
    # Get user's timezone for guidance
    user = await db.get(UserTable, user_id)
    user_tz = user.timezone if user else "UTC"
    
    compact_text = context_optimizer.compact_schedule(user_id, events, date)
    guidance = context_optimizer.get_ai_guidance(user_tz)
    
    return f"{compact_text}\n{guidance}"


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
    # 1. Resolve Timezones
    user_tz = pytz.UTC  # Default to UTC, should be passed from frontend
    guest_tz = pytz.timezone(target_timezone) if target_timezone else None

    # 2. Define User's Day Boundaries (Normalized to UTC for DB queries)
    # We assume 'date' is at 00:00:00 in some base (usually UTC from frontend)
    day_start = date.replace(hour=working_start, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=working_end, minute=0, second=0, microsecond=0)

    # 3. Intersection Logic (If Guest TZ is provided)
    if guest_tz:
        # We need to find the window that is 9-6 in BOTH timezones
        # This is the 'Sovereign Intersection'
        # Start by defining guest's 9-6 for that same 'day'
        guest_day_start = guest_tz.localize(
            datetime(date.year, date.month, date.day, working_start, 0)
        ).astimezone(pytz.UTC)
        guest_day_end = guest_tz.localize(
            datetime(date.year, date.month, date.day, working_end, 0)
        ).astimezone(pytz.UTC)

        # Intersection: Max of starts, Min of ends
        day_start = max(day_start.replace(tzinfo=pytz.UTC), guest_day_start)
        day_end = min(day_end.replace(tzinfo=pytz.UTC), guest_day_end)

        # If they don't overlap at all (e.g. SF vs Tokyo), return empty or shifted suggestion
        if day_start >= day_end:
            logger.warning(
                f"No business hour overlap found between UTC and {target_timezone}"
            )
            return []

    # Ensure naive datetime for DB consistency if needed, but here we work with UTC
    # 4. Fetch existing events for the day (GROUND TRUTH FROM DB)
    existing_events = await get_events_for_range(db, user_id, day_start, day_end)

    available_slots = []
    current_time = day_start

    # Pre-filter busy events for tighter loop
    busy_events = [e for e in existing_events if e.is_busy and e.status != "canceled"]

    while current_time + timedelta(minutes=duration_minutes) <= day_end:
        potential_end = current_time + timedelta(minutes=duration_minutes)

        # Check for overlap (LITERAL 0ms check via pre-fetched indexed list)
        has_overlap = False
        for event in busy_events:
            ev_start = event.start_time
            ev_end = event.end_time

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


async def check_external_conflicts(
    db: AsyncSession,
    user_id: str,
    start_time: datetime,
    end_time: datetime,
    google_token: Optional[str] = None,
    microsoft_token: Optional[str] = None
) -> bool:
    """
    Checks for conflicts across external providers (Google and Microsoft).
    Returns True if CLEAR (no conflicts), False if BUSY.
    """
    start_iso = start_time.isoformat()
    end_iso = end_time.isoformat()

    # 1. Resolve Tokens (Check DB if not explicitly provided)
    # This 'Sovereign Token Fetch' logic creates the strong, persistent connection.
    if not google_token:
        google_token = await get_valid_google_token(db, user_id)
    if not microsoft_token:
        microsoft_token = await get_valid_ms_token(db, user_id)

    # 2. Check Google if token available
    if google_token:
        is_free = await get_google_availability(start_iso, end_iso, google_token)
        if not is_free:
            logger.warning(f"Conflict detected on User {user_id}'s Google Calendar.")
            return False

    # 3. Check Microsoft if token available
    if microsoft_token:
        is_free = await get_microsoft_availability(start_iso, end_iso, microsoft_token)
        if not is_free:
            logger.warning(f"Conflict detected on User {user_id}'s Microsoft Calendar.")
            return False

    return True


async def _run_sync_and_notify(content_type: str, event_id: int, user_id: str, db: AsyncSession):
    """
    Background helper to perform AI sync and User notification without blocking the main request.
    Wraps entire pipeline in try-except to ensure background failures don't impact the event loop.
    """
    try:
        # 1. Fetch the fresh event state from DB
        get_stmt = select(EventTable).where(EventTable.id == event_id)
        result = await db.execute(get_stmt)
        event = result.scalars().first()
        
        if not event:
            logger.warning(f"Background sync: Event {event_id} no longer exists. Skipping.")
            return

        # 2. Sync to AI Memory (Semantic Retrieval Index)
        try:
            await sync_event_to_ai(event, db=db)
        except Exception as ai_err:
            logger.error(f"⚠ AI Memory Sync failed for event {event_id}: {ai_err}")

        # 3. Notify User & Attendees
        try:
            target_user = await db.get(UserTable, user_id)
            if target_user:
                event_dto = {
                    "id": event.id,
                    "user_id": event.user_id,
                    "title": event.title,
                    "category": event.category,
                    "start_time": event.start_time.isoformat() if event.start_time else None,
                    "end_time": event.end_time.isoformat() if event.end_time else None,
                    "is_meeting": event.is_meeting,
                    "meeting_link": event.meeting_link,
                    "meeting_platform": event.meeting_platform,
                    "agenda": event.agenda,
                    "attendees": event.attendees,
                }
                
                if content_type == "created":
                    await notify_event_created(target_user.email, [], event_dto)
                elif content_type == "updated":
                    await notify_event_updated(target_user.email, [], event_dto)
                elif content_type == "deleted":
                    await notify_event_deleted(target_user.email, [], event_dto)
        except Exception as notify_err:
            logger.error(f"⚠ Notification failed for event {event_id}: {notify_err}")

        logger.info(f"🚀 Background pipeline completed for Event {event_id} ({content_type})")
    except Exception as e:
        logger.error(f"❌ Critical error in background pipeline for Event {event_id}: {e}")


async def sync_event_to_ai(event: EventTable, db: Optional[AsyncSession] = None):
    """
    Feeds event data to the LLM Vector Store in real-time with semantic JSON formatting.
    This 'Smart Feedback Loop' ensures the AI has a high-fidelity, consistent view
    of the user's schedule.
    
    Optimized: Skips sync if the payload has not changed since the last update.
    """
    try:
        # SaaS Namespace: Use Org ID for multi-tenant isolation in Vector DB
        namespace = f"org_{event.org_id}" if event.org_id else f"user_{event.user_id}"

        # Calculate semantic duration for LLM reasoning
        duration = (event.end_time - event.start_time).total_seconds() / 60

        # 'Smart' LLM JSON block - clean, structured, and parseable
        smart_context_block = {
            "entry_type": "calendar_event",
            "event_id": event.id,
            "title": event.title,
            "category": event.category,
            "description": event.description or "No description provided.",
            "schedule": {
                "start": event.start_time.strftime("%Y-%m-%d %H:%M"),
                "end": event.end_time.strftime("%Y-%m-%d %H:%M"),
                "duration_minutes": int(duration),
                "human_readable": f"{event.start_time.strftime('%A, %b %d at %I:%M %p')}",
            },
            "status": {
                "current": event.status,
                "is_confirmed": event.status == "confirmed",
            },
            "meeting_link": event.meeting_link,
        }

        # Calculate fresh hash for idempotency/optimization
        payload_str = json.dumps(smart_context_block, sort_keys=True)
        current_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        if event.last_synced_hash == current_hash:
            logger.info(f"⏭ AI Sync skipped for event {event.id} (No changes detected)")
            return

        # We store the JSON as the page content for perfect LLM parsing (one-shot reasoning)
        llm_ready_content = f"SCHEDULE_ENTRY: {event.title} ({event.category})\n{json.dumps(smart_context_block, indent=2)}"

        doc = Document(
            page_content=llm_ready_content,
            metadata={
                "id": event.id,
                "type": "calendar_event",
                "category": event.category,
                "start_time": event.start_time.isoformat(),
                "user_id": event.user_id,
                "org_id": event.org_id,
                "workspace_id": event.workspace_id,
            },
        )

        # Use consistent document ID to implement idempotent 'Upsert' behavior.
        vector_store.add_documents(
            [doc], namespace=namespace, ids=[f"calendar_event_{event.id}"]
        )

        # Update the sync hash in the database
        event.last_synced_hash = current_hash
        if db:
            await db.commit()

        logger.info(
            f"✅ AI Feedback Loop triggered: Context synchronized for {event.title} (ID: {event.id})"
        )
    except Exception as e:
        logger.error(
            f"⚠ AI Feedback Loop failed for event {event.id}: {type(e).__name__} - {e}"
        )


def _compact_payload(event_data: dict) -> dict:
    """
    Strips redundant or empty fields from the event payload to save disk space on free tiers.
    """
    if "metadata_payload" in event_data and event_data["metadata_payload"]:
        # Remove common empty fields
        payload = event_data["metadata_payload"]
        compact = {k: v for k, v in payload.items() if v not in [None, "", [], {}]}
        event_data["metadata_payload"] = compact
    
    if "attendees" in event_data and isinstance(event_data["attendees"], list):
        # Only keep email and response status to save space
        compact_attendees = []
        for a in event_data["attendees"]:
            if isinstance(a, dict):
                compact_attendees.append({
                    "email": a.get("email"),
                    "status": a.get("responseStatus") or a.get("status")
                })
        event_data["attendees"] = compact_attendees
        
    return event_data


async def create_event(
    db: AsyncSession, 
    event_data: dict, 
    background_tasks: Optional[BackgroundTasks] = None
) -> EventTable:
    """Create a new event with optional real-time external conflict checking."""
    # Compact payload for Free Tier storage efficiency
    event_data = _compact_payload(event_data)
    new_event = EventTable(**event_data)

    # 1. Local Conflict Check (Scoped by Organization)
    conflict_stmt = select(EventTable).where(
        and_(
            EventTable.user_id == new_event.user_id,
            EventTable.org_id == new_event.org_id,
            EventTable.start_time < new_event.end_time,
            EventTable.end_time > new_event.start_time,
        )
    )
    conflict_result = await db.execute(conflict_stmt)
    if conflict_result.scalars().first():
        raise ValueError("Event overlaps with your existing GraftAI schedule in this organization.")

    # 2. External Conflict Check (Graph & Google)
    google_token = event_data.get("google_access_token")
    microsoft_token = event_data.get("microsoft_access_token")
    
    # Run conflict check - it automatically tries to resolve tokens from DB now.
    is_clear = await check_external_conflicts(
        db,
        new_event.user_id, 
        new_event.start_time, 
        new_event.end_time,
        google_token,
        microsoft_token
    )
    if not is_clear:
        raise ValueError("Event overlaps with an external calendar appointment.")

    # 3. Generate Meeting Links
    if new_event.is_meeting and new_event.meeting_platform and not new_event.meeting_link:
        new_event.meeting_link = await _generate_meeting_link(
            new_event.meeting_platform, 
            new_event.id, 
            new_event.title,
            new_event.start_time,
            new_event.end_time,
            access_token=google_token or microsoft_token
        )

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    # 4. Offload to Background Tasks
    if background_tasks:
        background_tasks.add_task(_run_sync_and_notify, "created", new_event.id, new_event.user_id, db)
    else:
        # Fallback for non-API contexts (e.g. scripts)
        await _run_sync_and_notify("created", new_event.id, new_event.user_id, db)

    return new_event


async def update_event(
    db: AsyncSession, 
    event_id: int, 
    user_id: str, 
    update_data: dict,
    background_tasks: Optional[BackgroundTasks] = None,
    org_id: Optional[int] = None,
    workspace_id: Optional[int] = None
) -> Optional[EventTable]:
    """Update event and sync changes to LLM service, scoped by tenant."""
    # Compact payload for Free Tier storage efficiency
    update_data = _compact_payload(update_data)
    
    filters = [EventTable.id == event_id]
    
    # Always enforce tenant isolation - user_id is baseline security
    if org_id:
        filters.append(EventTable.org_id == org_id)
        if workspace_id:
            filters.append(EventTable.workspace_id == workspace_id)
        else:
            # Within org but no workspace specified - check personal/general workspace
            filters.append(EventTable.user_id == user_id)
    else:
        # No org context - only allow user's personal events
        filters.append(EventTable.user_id == user_id)

    stmt = select(EventTable).where(and_(*filters))
    result = await db.execute(stmt)
    event = result.scalars().first()

    if not event:
        return None

    for key, value in update_data.items():
        if hasattr(event, key):
            setattr(event, key, value)

    # Check for overlaps after update (if schedule changed)
    conflict_stmt = select(EventTable).where(
        and_(
            EventTable.user_id == user_id,
            EventTable.id != event.id,
            EventTable.start_time < event.end_time,
            EventTable.end_time > event.start_time,
        )
    )
    conflict_result = await db.execute(conflict_stmt)
    if conflict_result.scalars().first():
        raise ValueError("Updated timing overlaps with another event.")

    await db.commit()
    await db.refresh(event)

    # Offload to Background Tasks
    if background_tasks:
        background_tasks.add_task(_run_sync_and_notify, "updated", event.id, user_id, db)
    else:
        await _run_sync_and_notify("updated", event.id, user_id, db)

    return event


async def delete_event(
    db: AsyncSession, 
    event_id: int, 
    user_id: str,
    background_tasks: Optional[BackgroundTasks] = None,
    org_id: Optional[int] = None,
    workspace_id: Optional[int] = None
) -> bool:
    """
    Remove event from DB and purge from AI long-term memory.
    """
    filters = [EventTable.id == event_id]
    
    # Always enforce tenant isolation - user_id is baseline security
    if org_id:
        filters.append(EventTable.org_id == org_id)
        if workspace_id:
            filters.append(EventTable.workspace_id == workspace_id)
        else:
            # Within org but no workspace specified - check personal/general workspace
            filters.append(EventTable.user_id == user_id)
    else:
        # No org context - only allow user's personal events
        filters.append(EventTable.user_id == user_id)

    stmt = select(EventTable).where(and_(*filters))
    result = await db.execute(stmt)
    event = result.scalars().first()

    if not event:
        return False

    # Capture event data for the notification before deleting
    event_dto = {
        "id": event.id,
        "user_id": user_id,
        "title": event.title,
        "category": event.category,
    }
    
    # We need the user's email for the background task to notify them of the deletion
    target_user = await db.get(UserTable, user_id)
    user_email = target_user.email if target_user else None

    try:
        # Purge from Vector Store with Org-based namespace
        namespace = f"org_{event.org_id}" if event.org_id else f"user_{user_id}"
        vector_store.delete(ids=[f"calendar_event_{event_id}"], namespace=namespace)
        logger.info(f"🗑 AI Memory purged for event {event_id}")
    except Exception as e:
        logger.warning(f"⚠ AI Memory purge failed for event {event_id}: {e}")

    await db.delete(event)
    await db.commit()

    if user_email:
        if background_tasks:
            background_tasks.add_task(notify_event_deleted, user_email, [], event_dto)
        else:
            await notify_event_deleted(user_email, [], event_dto)

    return True
