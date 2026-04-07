import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.dialects.postgresql import insert

from backend.models.tables import EventTable, UserTable
from backend.models.user_token import UserTokenTable
from backend.services.integrations import google_calendar, ms_graph
from backend.utils.resilience import get_breaker
from backend.utils.serialization import serializer

logger = logging.getLogger(__name__)

# Register 3rd-party breakers
google_breaker = get_breaker("google_calendar", threshold=5, recovery_timeout=120)
ms_breaker = get_breaker("microsoft_calendar", threshold=5, recovery_timeout=120)

def generate_fingerprint(event_data: Dict[str, Any]) -> str:
    """
    Generates a unique hash for an event to identify duplicates across different providers.
    Uses: start_time, end_time, and normalized title.
    """
    start = str(event_data.get("start_time"))
    end = str(event_data.get("end_time"))
    title = str(event_data.get("title", "")).strip().lower()
    
    # Create a canonical string for fingerprinting
    raw = f"{start}|{end}|{title}"
    return hashlib.sha256(raw.encode()).hexdigest()


def classify_google_category(item: Dict[str, Any]) -> str:
    summary = str(item.get("summary", "")).strip().lower()
    description = str(item.get("description", "")).strip().lower()
    event_type = str(item.get("eventType", "")).strip().lower()
    attendees = item.get("attendees") or []
    conference = item.get("conferenceData")

    if "birthday" in summary or "birthday" in description or event_type == "birthday":
        return "birthday"

    if "anniversary" in summary or "anniversary" in description:
        return "birthday"

    task_keywords = ["task", "todo", "reminder", "follow-up", "follow up", "action item", "deadline", "due"]
    if any(keyword in summary for keyword in task_keywords) or any(keyword in description for keyword in task_keywords):
        return "task"

    if event_type in ["focusTime".lower(), "outOfOffice".lower()]:
        return "event"

    if conference or item.get("hangoutLink") or (isinstance(attendees, list) and len(attendees) > 0):
        return "meeting"

    if "party" in summary or "ceremony" in summary or "webinar" in summary or "conference" in summary:
        return "event"

    return "event"

async def upsert_event(db: AsyncSession, user_id: str, source: str, event_data: Dict[str, Any]) -> EventTable:
    """
    Smart-upsert that handles both provider-specific updates and cross-provider merging.
    """
    external_id = event_data.get("external_id")
    fingerprint = generate_fingerprint(event_data)
    
    # 1. Check for primary match (source + external_id)
    stmt = select(EventTable).where(
        and_(
            EventTable.user_id == user_id,
            EventTable.source == source,
            EventTable.external_id == external_id
        )
    )
    result = await db.execute(stmt)
    existing_event = result.scalars().first()
    
    if not existing_event:
        # 2. Check for fingerprint match (cross-provider merging)
        # We use this to detect the same meeting in Google and Outlook
        stmt = select(EventTable).where(
            and_(
                EventTable.user_id == user_id,
                EventTable.fingerprint == fingerprint
            )
        )
        result = await db.execute(stmt)
        existing_event = result.scalars().first()
        
    if existing_event:
        # Smart update: don't overwrite local changes if we have a flag, 
        # but for sync events from external source, we update.
        for key, value in event_data.items():
            if hasattr(existing_event, key) and value is not None:
                setattr(existing_event, key, value)
        
        existing_event.fingerprint = fingerprint
        if external_id and not existing_event.external_id:
             existing_event.external_id = external_id
        
        logger.debug(f"✅ Synced existing event {existing_event.id} (user: {user_id}, source: {source})")
        return existing_event
    else:
        # Create new record
        new_event = EventTable(
            user_id=user_id,
            source=source,
            external_id=external_id,
            fingerprint=fingerprint,
            **{k: v for k, v in event_data.items() if hasattr(EventTable, k) and k not in ["external_id", "fingerprint", "source"]}
        )
        db.add(new_event)
        await db.flush() # Flush so ID is available
        logger.info(f"🆕 Created sync event for user {user_id} (source: {source})")
        return new_event

async def bulk_upsert_events(db: AsyncSession, user_id: str, source: str, events: list[Dict[str, Any]]):
    """
    Perform a high-performance batch upsert to handle 'big masses' of data.
    """
    if not events:
        return
        
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    
    # Chunking for memory safety on weak CPUs
    CHUNK_SIZE = 50
    for i in range(0, len(events), CHUNK_SIZE):
        chunk = events[i:i + CHUNK_SIZE]
        stmt = pg_insert(EventTable).values(chunk)
        
        # Determine cols to update
        cols = {
            c.name: stmt.excluded[c.name] 
            for c in EventTable.__table__.columns 
            if c.name not in ['id', 'user_id', 'external_id', 'source', 'created_at']
        }
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'external_id'],
            set_=cols
        )
        await db.execute(upsert_stmt)
    
    await db.commit()

async def sync_google_events(db: AsyncSession, token_record: UserTokenTable):
    """
    Perform incremental sync for Google Calendar.
    """
    user_id = token_record.user_id
    try:
        # Use full credentials from environment for refresh capability
        token_data = {
            "access_token": token_record.access_token,
            "refresh_token": token_record.refresh_token,
            "scopes": token_record.scopes or "",
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        }

        results = await google_breaker(
            google_calendar.list_google_events,
            token_data,
            sync_token=token_record.sync_token
        )
        
        items = results.get("items", [])
        next_sync_token = results.get("nextSyncToken")
            # Gather events for batch processing
        events_to_sync = []
        for item in items:
            if item.get("status") == "cancelled":
                # Handle deletion
                stmt = select(EventTable).where(
                    and_(EventTable.user_id == user_id, EventTable.external_id == item.get("id"))
                )
                res = await db.execute(stmt)
                evt = res.scalars().first()
                if evt:
                    await db.delete(evt)
                continue
                
            # Map Google item to our schema
            start_data = item.get("start", {})
            end_data = item.get("end", {})
            
            # Extract datetime strings
            start_str = start_data.get("dateTime") or start_data.get("date")
            end_str = end_data.get("dateTime") or end_data.get("date")
            
            event_payload = {
                "user_id": user_id,
                "external_id": item.get("id"),
                "title": item.get("summary", "Untitled Event"),
                "description": item.get("description"),
                "start_time": datetime.fromisoformat(start_str.replace("Z", "+00:00")),
                "end_time": datetime.fromisoformat(end_str.replace("Z", "+00:00")),
                "category": "meeting",
                "source": "google",
            }
            event_payload["fingerprint"] = generate_fingerprint(event_payload)
            events_to_sync.append(event_payload)
            
        if events_to_sync:
            await bulk_upsert_events(db, user_id, "google", events_to_sync)

        # Update token with new sync token
        if next_sync_token:
            token_record.sync_token = next_sync_token
        
        await db.commit()
        logger.info(f"Google Sync completed for user {user_id}. Synced {len(items)} items.")
        
    except Exception as e:
        logger.error(f"Google Sync FAILED for user {user_id}: {e}")
        await db.rollback()
        # Trigger business-grade error notification
        from backend.services.bg_tasks import enqueue_sync_error_alert
        user = await db.get(UserTable, user_id)
        if user:
            await enqueue_sync_error_alert(user.email, str(e))

async def sync_ms_graph_events(db: AsyncSession, token_record: UserTokenTable):
    """
    Perform incremental sync for Microsoft Graph.
    """
    user_id = token_record.user_id
    try:
        # 1. Fetch events from MS Graph with Circuit Breaker
        results = await ms_breaker(
            ms_graph.list_ms_events,
            token_record.access_token, 
            delta_link=token_record.sync_token
        )
        
        items = results.get("value", [])
        next_delta_link = results.get("@odata.deltaLink")
        
        events_to_sync = []
        for item in items:
            if item.get("@removed"):
                # Handle deletion
                stmt = select(EventTable).where(
                    and_(EventTable.user_id == user_id, EventTable.external_id == item.get("id"))
                )
                res = await db.execute(stmt)
                evt = res.scalars().first()
                if evt:
                    await db.delete(evt)
                continue
                
            # Map MS item to our schema
            event_payload = {
                "user_id": user_id,
                "external_id": item.get("id"),
                "title": item.get("subject", "Untitled Meeting"),
                "description": item.get("body", {}).get("content"),
                "start_time": datetime.fromisoformat(item["start"].get("dateTime").replace("Z", "+00:00")),
                "end_time": datetime.fromisoformat(item["end"].get("dateTime").replace("Z", "+00:00")),
                "category": "meeting",
                "source": "microsoft",
                "is_meeting": True,
                "meeting_platform": "teams",
                "meeting_link": item.get("onlineMeeting", {}).get("joinUrl"),
                "attendees": item.get("attendees", []),
            }
            event_payload["fingerprint"] = generate_fingerprint(event_payload)
            events_to_sync.append(event_payload)
            
        if events_to_sync:
            await bulk_upsert_events(db, user_id, "microsoft", events_to_sync)

        # 2. Store next delta link
        if next_delta_link:
            token_record.sync_token = next_delta_link
            
        await db.commit()
        logger.info(f"Microsoft Sync completed for user {user_id}. Synced {len(items)} items.")
        
    except Exception as e:
        logger.error(f"Microsoft Sync FAILED for user {user_id}: {e}")
        await db.rollback()
        # Trigger business-grade error notification
        from backend.services.bg_tasks import enqueue_sync_error_alert
        user = await db.get(UserTable, user_id)
        if user:
            await enqueue_sync_error_alert(user.email, str(e))

import sentry_sdk
from backend.utils.cache import acquire_lock, release_lock, get_redis_client

SYNC_MIN_INTERVAL_SECONDS = int(os.getenv("SYNC_MIN_INTERVAL_SECONDS", "120"))


async def _acquire_sync_cooldown(user_id: str) -> bool:
    """
    Prevents repeated full-provider sync bursts for the same user.
    Returns False when a recent sync already ran within the cooldown window.
    """
    if SYNC_MIN_INTERVAL_SECONDS <= 0:
        return True

    client = await get_redis_client()
    if not client:
        # Fail open when cache infra is unavailable.
        return True

    key = f"sync_cooldown:{user_id}"
    try:
        return bool(
            await client.set(key, "1", ex=SYNC_MIN_INTERVAL_SECONDS, nx=True)
        )
    except Exception as exc:
        logger.warning(f"[SYNC] Cooldown check failed for user {user_id}: {exc}")
        return True

async def sync_user_calendar(db: AsyncSession, user_id: str):
    """
    High-level orchestrator to sync ALL active integrations for a user.
    Uses a Redis-based sync lock to ensure concurrency safety.
    """
    if not await _acquire_sync_cooldown(user_id):
        logger.info(
            f"[SYNC] ⏱ Skipping sync for user {user_id}: recent sync within cooldown ({SYNC_MIN_INTERVAL_SECONDS}s)."
        )
        return

    lock_name = f"sync_user_{user_id}"
    if not await acquire_lock(lock_name, ttl_seconds=300):
        logger.info(f"[SYNC] ⏳ Sync already in progress for user {user_id}. Skipping.")
        return

    # Start a Sentry span for the full sync transaction
    from backend.services.redis_client import publish
    with sentry_sdk.start_span(op="calendar.sync", description=f"Sync for {user_id}"):
        try:
            logger.info(f"[SYNC] 🔄 Starting full calendar sync orchestration for user {user_id}")
            # Binary SSE: Minimal overhead for real-time status
            await publish(f"sse:user:{user_id}", serializer.pack_for_cache({
                "event": "SYNC_STATUS", 
                "status": "syncing", 
                "message": "Starting full calendar sync..."
            }))
            
            # Fetch all active tokens for this user
            stmt = select(UserTokenTable).where(
                and_(UserTokenTable.user_id == user_id, UserTokenTable.is_active == True)
            )
            result = await db.execute(stmt)
            tokens = result.scalars().all()
            
            if not tokens:
                logger.warning(f"[SYNC] ⚠️ No active integrations found for user {user_id}. Skipping sync.")
                await publish(f"sse:user:{user_id}", serializer.pack_for_cache({
                    "event": "SYNC_STATUS", 
                    "status": "no_integrations", 
                    "message": "No active integrations found."
                }))
                return

            for token in tokens:
                # Trace individual provider syncs
                with sentry_sdk.start_span(op=f"sync.{token.provider}", description=f"Provider: {token.provider}"):
                    if token.provider == "google":
                        await sync_google_events(db, token)
                    elif token.provider == "microsoft":
                        await sync_ms_graph_events(db, token)
                    else:
                        logger.warning(f"[SYNC] ❓ Unknown provider '{token.provider}' for token {token.id}")

            logger.info(f"[SYNC] ✨ Orchestration completed for user {user_id}")
            await publish(f"sse:user:{user_id}", serializer.pack_for_cache({
                "event": "SYNC_STATUS", 
                "status": "idle", 
                "message": "Sync completed successfully."
            }))
            
            # 3. Ensure Real-Time Webhooks are active for this user
            with sentry_sdk.start_span(op="webhook.register", description="Webhook Maintenance"):
                try:
                    from backend.services.integrations.webhook_manager import register_user_webhooks
                    await register_user_webhooks(db, user_id)
                except Exception as webhook_err:
                    logger.warning(f"[SYNC] ⚠️ Webhook registration skipped for {user_id}: {webhook_err}")
                    
        finally:
            # Always release the lock
            await release_lock(lock_name)
