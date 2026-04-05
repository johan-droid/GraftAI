import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import EventTable
from backend.services.langchain_client import vector_store

logger = logging.getLogger(__name__)

async def sync_event_to_vector_store(event: EventTable):
    """
    Core logic to transform an EventTable model into a semantic JSON block
    and upsert it into the Pinecone Vector Store.
    """
    try:
        namespace = f"user_{event.user_id}"
        duration = (event.end_time - event.start_time).total_seconds() / 60

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
            "meeting": {
                "is_meeting": event.is_meeting,
                "platform": event.meeting_platform,
                "link": event.meeting_link,
            }
        }

        llm_ready_content = f"SCHEDULE_ENTRY: {event.title} ({event.category})\n{json.dumps(smart_context_block, indent=2)}"

        try:
            from langchain_core.documents import Document
        except Exception as exc:
            logger.warning(f"AI sync skipped because langchain_core is unavailable: {exc}")
            return False

        if not hasattr(vector_store, "add_documents"):
            logger.warning("AI sync skipped because vector_store does not support add_documents")
            return False

        doc = Document(
            page_content=llm_ready_content,
            metadata={
                "id": event.id,
                "type": "calendar_event",
                "category": event.category,
                "start_time": event.start_time.isoformat(),
                "user_id": event.user_id,
            },
        )

        vector_store.add_documents(
            [doc], namespace=namespace, ids=[f"calendar_event_{event.id}"]
        )
        logger.info(f"✅ AI Context synchronized in background for event {event.id}")
        return True
    except Exception as e:
        logger.error(f"❌ AI Feedback Loop background sync failed for event {event.id}: {e}")
        return False

async def purge_event_from_vector_store(event_id: int, user_id: str):
    """Purges a specific event from the user's AI memory."""
    try:
        namespace = f"user_{user_id}"
        vector_store.delete(ids=[f"calendar_event_{event_id}"], namespace=namespace)
        logger.info(f"🗑 AI Memory purged in background for event {event_id}")
        return True
    except Exception as e:
        logger.warning(f"⚠ AI Memory purge failed in background for event {event_id}: {e}")
        return False
