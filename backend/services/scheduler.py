import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete
from backend.models.tables import EventTable
from .langchain_client import vector_store
from langchain_core.documents import Document
import json

# Initialize logger
logger = logging.getLogger(__name__)

async def get_events_for_range(
    db: AsyncSession, 
    user_id: int, 
    start: datetime, 
    end: datetime
) -> List[EventTable]:
    """Fetch all events for a user within a specific time range."""
    stmt = select(EventTable).where(
        and_(
            EventTable.user_id == user_id,
            EventTable.start_time >= start,
            EventTable.end_time <= end
        )
    ).order_by(EventTable.start_time.asc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

async def find_available_slots(
    db: AsyncSession,
    user_id: int,
    date: datetime,
    duration_minutes: int = 30,
    working_start: int = 9, # 9 AM
    working_end: int = 18   # 6 PM
) -> List[Dict[str, str]]:
    """
    Intelligent slot-finding algorithm.
    Scans the database for overlaps and returns free windows.
    """
    # Define the boundaries of the day in UTC
    day_start = date.replace(hour=working_start, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=working_end, minute=0, second=0, microsecond=0)
    
    # Fetch existing events for the day
    existing_events = await get_events_for_range(db, user_id, day_start, day_end)
    
    available_slots = []
    current_time = day_start
    
    while current_time + timedelta(minutes=duration_minutes) <= day_end:
        potential_end = current_time + timedelta(minutes=duration_minutes)
        
        # Check for overlap with any existing event
        has_overlap = False
        for event in existing_events:
            if not (potential_end <= event.start_time or current_time >= event.end_time):
                has_overlap = True
                # Skip to the end of the overlapping event
                current_time = event.end_time
                break
        
        if not has_overlap:
            available_slots.append({
                "start": current_time.isoformat(),
                "end": potential_end.isoformat()
            })
            current_time = potential_end
            
    return available_slots

async def sync_event_to_ai(event: EventTable):
    """
    Feeds event data to the LLM Vector Store in real-time with semantic JSON formatting.
    This 'Smart Feedback Loop' ensures the AI has a high-fidelity, consistent view 
    of the user's schedule for intelligent slot discovery and scheduling assistance.
    """
    try:
        namespace = f"user_{event.user_id}"
        
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
                "start": event.start_time.isoformat(),
                "end": event.end_time.isoformat(),
                "duration_minutes": int(duration),
                "timezone": "UTC"
            },
            "status": {
                "current": event.status,
                "is_remote": event.is_remote,
                "is_confirmed": event.status == "confirmed"
            },
            "context": event.metadata_payload or {}
        }
        
        # We store the JSON as the page content for perfect LLM parsing (one-shot reasoning)
        # We also add a natural language 'summary' line to help with initial embedding relevance
        llm_ready_content = f"SCHEDULE_ENTRY: {event.title} ({event.category})\n{json.dumps(smart_context_block, indent=2)}"
        
        doc = Document(
            page_content=llm_ready_content,
            metadata={
                "id": event.id,
                "type": "calendar_event",
                "category": event.category,
                "start_time": event.start_time.isoformat(),
                "user_id": event.user_id
            }
        )
        
        # Use consistent document ID to implement idempotent 'Upsert' behavior in Pinecone.
        # This prevents 'stale memory' by overwriting the old version of this event.
        vector_store.add_documents(
            [doc], 
            namespace=namespace, 
            ids=[f"calendar_event_{event.id}"]
        )
        
        logger.info(f"✅ AI Feedback Loop triggered: Context synchronized for {event.title} (ID: {event.id})")
    except Exception as e:
        logger.error(f"⚠ AI Feedback Loop failed for event {event.id}: {type(e).__name__} - {e}")

async def create_event(db: AsyncSession, event_data: dict) -> EventTable:
    """Create a new event and trigger AI feedback pipeline."""
    new_event = EventTable(**event_data)
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    
    # Trigger real-time AI sync
    await sync_event_to_ai(new_event)
    return new_event

async def update_event(db: AsyncSession, event_id: int, user_id: int, update_data: dict) -> Optional[EventTable]:
    """Update event and sync changes to LLM service."""
    stmt = select(EventTable).where(
        and_(EventTable.id == event_id, EventTable.user_id == user_id)
    )
    result = await db.execute(stmt)
    event = result.scalars().first()
    
    if not event:
        return None
        
    for key, value in update_data.items():
        if hasattr(event, key):
            setattr(event, key, value)
            
    await db.commit()
    await db.refresh(event)
    
    # Real-time sync to AI orchestrator
    await sync_event_to_ai(event)
    return event
    
async def delete_event(db: AsyncSession, event_id: int, user_id: int) -> bool:
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
        
    try:
        # Purge from Vector Store first (fail-safe)
        namespace = f"user_{user_id}"
        vector_store.delete(ids=[f"calendar_event_{event_id}"], namespace=namespace)
        logger.info(f"🗑 AI Memory purged for event {event_id}")
    except Exception as e:
        logger.warning(f"⚠ AI Memory purge failed for event {event_id}: {e}")

    await db.delete(event)
    await db.commit()
    return True
