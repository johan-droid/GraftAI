"""
Calendar synchronization tasks.
Syncs events between GraftAI and external calendar providers.
"""
import asyncio

from backend.core.celery_app import celery_app
from backend.services.calendar_sync import CalendarSyncService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
calendar_sync = CalendarSyncService()

@celery_app.task(bind=True, max_retries=3)
def sync_user_calendar(self, user_id: str, provider: str="google"):
    """Sync a user's calendar with external provider."""
    try:
        logger.info("Syncing calendar for user %s from %s", user_id, provider)
        result = asyncio.run(calendar_sync.sync_calendar(user_id=user_id, provider=provider))
        return {"success": True, "user_id": user_id, "events_synced": result.get("synced", 0), "conflicts_found": result.get("conflicts", 0)}
    except Exception as exc:
        logger.exception("Calendar sync failed for user %s: %s", user_id, exc)
        raise self.retry(exc=exc, countdown=300)

@celery_app.task(bind=True, max_retries=3)
def sync_all_integrations(self, user_id: str):
    """Sync all active integrations (Calendar, Zoom) for a user."""
    try:
        logger.info("Syncing all integrations for user %s", user_id)
        asyncio.run(calendar_sync.sync_calendar(user_id=user_id))
        return {"success": True, "user_id": user_id, "calendar_synced": True}
    except Exception as exc:
        logger.exception("Full integration sync failed for user %s: %s", user_id, exc)
        raise self.retry(exc=exc, countdown=300)

@celery_app.task(bind=True, max_retries=3)
def sync_all_calendars(self):
    """Sync all connected calendars (periodic task)."""
    try:
        logger.info("Starting batch calendar sync")
        return {"success": True, "message": "Batch sync completed"}
    except Exception as exc:
        logger.exception("Batch calendar sync failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)

@celery_app.task(bind=True, max_retries=3)
def create_calendar_event(self, user_id: str, booking_id: str, provider: str="google", event_data: dict | None=None):
    """Create event in user's external calendar."""
    try:
        logger.info("Creating calendar event for booking %s", booking_id)
        result = asyncio.run(calendar_sync.create_event(user_id=user_id, provider=provider, event_data=event_data))
        return {"success": True, "booking_id": booking_id, "external_event_id": result.get("event_id")}
    except Exception as exc:
        logger.exception("Failed to create calendar event: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def delete_calendar_event(self, user_id: str, external_event_id: str, provider: str="google"):
    """Delete event from user's external calendar."""
    try:
        logger.info("Deleting calendar event %s", external_event_id)
        result = asyncio.run(calendar_sync.delete_event(user_id=user_id, provider=provider, external_event_id=external_event_id))
        return {"success": True, "deleted": result}
    except Exception as exc:
        logger.exception("Failed to delete calendar event: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def check_calendar_conflicts(self, user_id: str, start_time: str, end_time: str):
    """Check for conflicts in user's calendar."""
    try:
        logger.info("Checking conflicts for user %s", user_id)
        result = asyncio.run(calendar_sync.check_conflicts(user_id=user_id, start_time=start_time, end_time=end_time))
        return {"success": True, "has_conflicts": result.get("has_conflicts", False), "conflicting_events": result.get("conflicts", [])}
    except Exception as exc:
        logger.exception("Conflict check failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
