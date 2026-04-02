import hashlib
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.tables import EventTable
from backend.models.user_token import UserTokenTable
from backend.services.integrations import google_calendar, ms_graph

logger = logging.getLogger(__name__)

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

async def upsert_event(db: AsyncSession, user_id: str, source: str, event_data: Dict[str, Any]) -> EventTable:
    """
    Smart-upsert that handles both provider-specific updates and cross-provider merging.
    """
    external_id = event_data.get("external_id")
    fingerprint = generate_fingerprint(event_data)
    
    # 1. Check for exact match (same source + external_id)
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
        # 2. Check for cross-provider match (same fingerprint, different source)
        # This handles cases where a meeting is in both Google and Outlook.
        stmt = select(EventTable).where(
            and_(
                EventTable.user_id == user_id,
                EventTable.fingerprint == fingerprint
            )
        )
        result = await db.execute(stmt)
        existing_event = result.scalars().first()
        
    if existing_event:
        # Update existing record
        for key, value in event_data.items():
            if hasattr(existing_event, key):
                setattr(existing_event, key, value)
        
        # Ensure sync fields are updated
        existing_event.fingerprint = fingerprint
        if not existing_event.external_id:
             existing_event.external_id = external_id
        # We keep the original 'source' if it was already set, or update if this is primary
        
        logger.debug(f"Updated event {existing_event.id} for user {user_id} (source: {source})")
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
        await db.flush() # Flush immediately so subsequent checks in this loop see the new ID
        logger.info(f"Created NEW sync event for user {user_id} (source: {source})")
        return new_event

async def sync_google_events(db: AsyncSession, token_record: UserTokenTable):
    """
    Perform incremental sync for Google Calendar.
    """
    user_id = token_record.user_id
    try:
        # 1. Fetch events from Google (using sync_token if available)
        # Note: google_calendar service needs update to support syncToken
        results = await google_calendar.list_google_events(
            token_record.access_token, 
            sync_token=token_record.sync_token
        )
        
        items = results.get("items", [])
        next_sync_token = results.get("nextSyncToken")
        
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
            event_payload = {
                "external_id": item.get("id"),
                "title": item.get("summary", "Untitled Meeting"),
                "description": item.get("description"),
                "start_time": datetime.fromisoformat(item["start"].get("dateTime", item["start"].get("date")).replace("Z", "+00:00")),
                "end_time": datetime.fromisoformat(item["end"].get("dateTime", item["end"].get("date")).replace("Z", "+00:00")),
                "is_meeting": True,
                "meeting_platform": "google_meet",
                "meeting_link": item.get("hangoutLink"),
                "attendees": item.get("attendees", []),
            }
            
            await upsert_event(db, user_id, "google", event_payload)
            
        # 2. Store next sync token BEFORE commit to ensure progression
        if next_sync_token:
            token_record.sync_token = next_sync_token
            db.add(token_record)
            
        await db.commit()
        logger.info(f"Google Sync completed for user {user_id}. Synced {len(items)} items.")
        
    except Exception as e:
        logger.error(f"Google Sync FAILED for user {user_id}: {e}")
        await db.rollback()

async def sync_ms_graph_events(db: AsyncSession, token_record: UserTokenTable):
    """
    Perform incremental sync for Microsoft Graph.
    """
    user_id = token_record.user_id
    try:
        # 1. Fetch events from MS Graph (using delta token if available)
        results = await ms_graph.list_ms_events(
            token_record.access_token, 
            delta_link=token_record.sync_token
        )
        
        items = results.get("value", [])
        next_delta_link = results.get("@odata.deltaLink")
        
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
                "external_id": item.get("id"),
                "title": item.get("subject", "Untitled Meeting"),
                "description": item.get("body", {}).get("content"),
                "start_time": datetime.fromisoformat(item["start"].get("dateTime").replace("Z", "+00:00")),
                "end_time": datetime.fromisoformat(item["end"].get("dateTime").replace("Z", "+00:00")),
                "is_meeting": True,
                "meeting_platform": "teams",
                "meeting_link": item.get("onlineMeeting", {}).get("joinUrl"),
                "attendees": item.get("attendees", []),
            }
            
            await upsert_event(db, user_id, "microsoft", event_payload)
            
        # 2. Store next delta link
        if next_delta_link:
            token_record.sync_token = next_delta_link
            
        await db.commit()
        logger.info(f"Microsoft Sync completed for user {user_id}. Synced {len(items)} items.")
        
    except Exception as e:
        logger.error(f"Microsoft Sync FAILED for user {user_id}: {e}")
        await db.rollback()

async def sync_user_calendar(db: AsyncSession, user_id: str):
    """
    High-level orchestrator to sync ALL active integrations for a user.
    Designed to be called from a background task worker.
    """
    logger.info(f"🔄 Starting full calendar sync orchestration for user {user_id}")
    
    # Fetch all active tokens for this user
    stmt = select(UserTokenTable).where(
        and_(UserTokenTable.user_id == user_id, UserTokenTable.is_active == True)
    )
    result = await db.execute(stmt)
    tokens = result.scalars().all()
    
    if not tokens:
        logger.warning(f"⚠️ No active integrations found for user {user_id}. Skipping sync.")
        return

    for token in tokens:
        if token.provider == "google":
            await sync_google_events(db, token)
        elif token.provider == "microsoft":
            await sync_ms_graph_events(db, token)
        else:
            logger.warning(f"❓ Unknown provider '{token.provider}' for token {token.id}")

    logger.info(f"✨ Orchestration completed for user {user_id}")
