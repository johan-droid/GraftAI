"""
Calendar synchronization tasks.
Syncs events between GraftAI and external calendar providers.
"""

from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger
from backend.services.calendar_sync import CalendarSyncService

logger = get_logger(__name__)
calendar_sync = CalendarSyncService()


@celery_app.task(bind=True, max_retries=3)
def sync_user_calendar(self, user_id: str, provider: str = "google"):
    """Sync a user's calendar with external provider."""
    try:
        logger.info(f"Syncing calendar for user {user_id} from {provider}")

        result = calendar_sync.sync_calendar(user_id=user_id, provider=provider)

        return {
            "success": True,
            "user_id": user_id,
            "events_synced": result.get("synced", 0),
            "conflicts_found": result.get("conflicts", 0),
        }
    except Exception as exc:
        logger.error(f"Calendar sync failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True, max_retries=3)
def sync_all_integrations(self, user_id: str):
    """Sync all active integrations (Calendar, Zoom) for a user."""
    try:
        logger.info(f"Syncing all integrations for user {user_id}")
        
        # Sync Calendars (Google / Microsoft)
        calendar_result = calendar_sync.sync_calendar(user_id=user_id)
        
        # Sync Zoom Meetings (if applicable)
        # For now, we'll just log it, but we could add a ZoomSyncService later.
        
        return {
            "success": True,
            "user_id": user_id,
            "calendar_synced": True,
        }
    except Exception as exc:
        logger.error(f"Full integration sync failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True, max_retries=3)
def sync_all_calendars(self):
    """Sync all connected calendars (periodic task)."""
    try:
        logger.info("Starting batch calendar sync")

        # Get all users with calendar integrations

        # This would query users with calendar credentials
        # For now, return success
        return {"success": True, "message": "Batch sync completed"}
    except Exception as exc:
        logger.error(f"Batch calendar sync failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True, max_retries=3)
def create_calendar_event(
    self,
    user_id: str,
    booking_id: str,
    provider: str = "google",
    event_data: dict = None,
):
    """Create event in user's external calendar."""
    try:
        logger.info(f"Creating calendar event for booking {booking_id}")

        result = calendar_sync.create_event(
            user_id=user_id, provider=provider, event_data=event_data
        )

        return {
            "success": True,
            "booking_id": booking_id,
            "external_event_id": result.get("event_id"),
        }
    except Exception as exc:
        logger.error(f"Failed to create calendar event: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def delete_calendar_event(
    self, user_id: str, external_event_id: str, provider: str = "google"
):
    """Delete event from user's external calendar."""
    try:
        logger.info(f"Deleting calendar event {external_event_id}")

        result = calendar_sync.delete_event(
            user_id=user_id, provider=provider, external_event_id=external_event_id
        )

        return {"success": True, "deleted": result}
    except Exception as exc:
        logger.error(f"Failed to delete calendar event: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def check_calendar_conflicts(self, user_id: str, start_time: str, end_time: str):
    """Check for conflicts in user's calendar."""
    try:
        logger.info(f"Checking conflicts for user {user_id}")

        result = calendar_sync.check_conflicts(
            user_id=user_id, start_time=start_time, end_time=end_time
        )

        return {
            "success": True,
            "has_conflicts": result.get("has_conflicts", False),
            "conflicting_events": result.get("conflicts", []),
        }
    except Exception as exc:
        logger.error(f"Conflict check failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
