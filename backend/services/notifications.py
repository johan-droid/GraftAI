import logging
from typing import Optional
from backend.services.email import send_email
from backend.services.onesignal import send_push_notification
from backend.services.redis_client import publish

logger = logging.getLogger(__name__)


async def notify_event_created(user_email: str, user_player_ids: list[str], event_data: dict):
    """Notify user across email, push, and real-time channel when event is created."""
    # Email
    subject = f"New event created: {event_data.get('title')}"
    html_body = f"<h1>Event Created</h1><p>Your event <strong>{event_data.get('title')}</strong> is set at {event_data.get('start_time')} to {event_data.get('end_time')}.</p>"
    try:
        await send_email(user_email, subject, html_body)
        logger.info("Email notification queued for event creation")
    except Exception as e:
        logger.warning(f"Email notification failed: {e}")

    # Push notification
    if user_player_ids:
        try:
            send_push_notification(
                user_player_ids,
                heading="Event created",
                content=f"{event_data.get('title')} at {event_data.get('start_time')}",
                data={"event_id": str(event_data.get('id'))},
            )
            logger.info("Push notification sent for event creation")
        except Exception as e:
            logger.warning(f"OneSignal push notification failed: {e}")

    # Realtime event pub/sub
    try:
        channel = f"user_notifications_{event_data.get('user_id')}"
        payload = {
            "type": "event_created",
            "event": {
                "id": event_data.get("id"),
                "title": event_data.get("title"),
                "start_time": str(event_data.get("start_time")),
                "end_time": str(event_data.get("end_time")),
            },
        }
        publish(channel, str(payload))
        logger.info("Real-time notification published")
    except Exception as e:
        logger.warning(f"Realtime notification publish failed: {e}")


async def notify_event_updated(user_email: str, user_player_ids: list[str], event_data: dict):
    subject = f"Event updated: {event_data.get('title')}"
    html_body = f"<h1>Event Updated</h1><p>Your event <strong>{event_data.get('title')}</strong> now starts at {event_data.get('start_time')}.</p>"
    try:
        await send_email(user_email, subject, html_body)
    except Exception as e:
        logger.warning(f"Email update notification failed: {e}")

    if user_player_ids:
        try:
            send_push_notification(
                user_player_ids,
                heading="Event updated",
                content=f"{event_data.get('title')} updated", data={"event_id": str(event_data.get('id'))}
            )
        except Exception as e:
            logger.warning(f"OneSignal push update failed: {e}")

    try:
        channel = f"user_notifications_{event_data.get('user_id')}"
        payload = {"type": "event_updated", "event": {"id": event_data.get("id")}}
        publish(channel, str(payload))
    except Exception as e:
        logger.warning(f"Realtime update notify failed: {e}")


async def notify_event_deleted(user_email: str, user_player_ids: list[str], event_data: dict):
    subject = f"Event deleted: {event_data.get('title')}"
    html_body = f"<h1>Event Cancelled</h1><p>Your event <strong>{event_data.get('title')}</strong> has been deleted.</p>"
    try:
        await send_email(user_email, subject, html_body)
    except Exception as e:
        logger.warning(f"Email delete notification failed: {e}")

    if user_player_ids:
        try:
            send_push_notification(
                user_player_ids,
                heading="Event deleted",
                content=f"{event_data.get('title')} removed", data={"event_id": str(event_data.get('id'))}
            )
        except Exception as e:
            logger.warning(f"OneSignal push delete failed: {e}")

    try:
        channel = f"user_notifications_{event_data.get('user_id')}"
        payload = {"type": "event_deleted", "event": {"id": event_data.get("id")}}
        publish(channel, str(payload))
    except Exception as e:
        logger.warning(f"Realtime delete notify failed: {e}")
