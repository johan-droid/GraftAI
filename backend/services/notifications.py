import logging
import os
from typing import Optional
from backend.services.email import send_email
from backend.services.onesignal import send_push_notification
from backend.services.redis_client import publish

logger = logging.getLogger(__name__)


def _build_event_templates(notification_type: str, event_data: dict) -> tuple[str, str, str]:
    user_name = event_data.get("user_name") or event_data.get("full_name") or "GraftAI user"
    title = event_data.get("title") or "Untitled Event"
    start_time = event_data.get("start_time") or "as scheduled"
    end_time = event_data.get("end_time") or ""
    event_url = event_data.get("event_url") or os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

    if notification_type == "created":
        subject = f"🎉 New event created: {title}"
        html_body = (
            f"<h1>Event Created</h1>"
            f"<p>Hello {user_name},</p>"
            f"<p>Your event <strong>{title}</strong> has been scheduled from {start_time} to {end_time}.</p>"
            f"<p><a href=\"{event_url}\">Open your calendar</a></p>"
        )
        text_body = (
            f"Hello {user_name},\n\n"
            f"Your event '{title}' is scheduled from {start_time} to {end_time}.\n"
            f"Open your calendar: {event_url}\n"
        )

    elif notification_type == "updated":
        subject = f"✏️ Event updated: {title}"
        html_body = (
            f"<h1>Event Updated</h1>"
            f"<p>Hello {user_name},</p>"
            f"<p>Your event <strong>{title}</strong> has been updated. New time: {start_time} to {end_time}.</p>"
            f"<p><a href=\"{event_url}\">Review event details</a></p>"
        )
        text_body = (
            f"Hello {user_name},\n\n"
            f"Your event '{title}' was updated. New time: {start_time} to {end_time}.\n"
            f"Review: {event_url}\n"
        )

    elif notification_type == "deleted":
        subject = f"🗑 Event deleted: {title}"
        html_body = (
            f"<h1>Event Deleted</h1>"
            f"<p>Hello {user_name},</p>"
            f"<p>Your event <strong>{title}</strong> has been canceled.</p>"
            f"<p><a href=\"{event_url}\">Manage your schedule</a></p>"
        )
        text_body = (
            f"Hello {user_name},\n\n"
            f"Your event '{title}' was deleted.\n"
            f"Manage your schedule: {event_url}\n"
        )
    else:
        subject = f"Notification: {title}"
        html_body = f"<p>Hello {user_name},</p><p>{event_data.get('message', 'You have a new notification.')}</p>"
        text_body = f"Hello {user_name},\n\n{event_data.get('message', 'You have a new notification.')}\n"

    return subject, html_body, text_body


async def _send_notification(user_email: str, user_player_ids: list[str], content_type: str, event_data: dict):
    # We only treat this as event notification if event id is present and not placeholder.
    event_id = event_data.get("id")
    if event_id is None or (isinstance(event_id, int) and event_id < 0):
        logger.info("Skipping event notification for non-event payload")
        return

    subject, html_body, text_body = _build_event_templates(content_type, event_data)

    # Email
    try:
        await send_email(user_email, subject, html_body, text_body)
        logger.info("Email notification queued")
    except Exception as e:
        logger.warning(f"Email notification failed: {e}")

    # Push
    if user_player_ids:
        try:
            headings = {
                "created": "Event created",
                "updated": "Event updated",
                "deleted": "Event deleted",
            }
            send_push_notification(
                user_player_ids,
                heading=headings.get(content_type, "Notification"),
                content=f"{event_data.get('title')} {content_type}",
                data={"event_id": str(event_data.get('id'))},
            )
            logger.info("Push notification triggered")
        except Exception as e:
            logger.warning(f"OneSignal notification failed: {e}")

    # Realtime pub/sub
    try:
        channel = f"user_notifications_{event_data.get('user_id')}"
        payload = {"type": f"event_{content_type}", "event": event_data}
        publish(channel, str(payload))
    except Exception as e:
        logger.warning(f"Realtime publish failed: {e}")


async def notify_event_created(user_email: str, user_player_ids: list[str], event_data: dict):
    await _send_notification(user_email, user_player_ids, "created", event_data)


async def notify_event_updated(user_email: str, user_player_ids: list[str], event_data: dict):
    await _send_notification(user_email, user_player_ids, "updated", event_data)


async def notify_event_deleted(user_email: str, user_player_ids: list[str], event_data: dict):
    await _send_notification(user_email, user_player_ids, "deleted", event_data)


async def send_custom_notification(
    user_email: str,
    subject: str,
    message: str,
    html_body: Optional[str] = None,
    text_body: Optional[str] = None,
):
    if not html_body:
        html_body = f"<p>{message}</p>"
    if not text_body:
        text_body = message

    await send_email(user_email, subject, html_body, text_body)


async def notify_welcome_email(user_email: str, full_name: str):
    subject = "Welcome to GraftAI"
    html_body = (
        f"<h1>Welcome {full_name}</h1>"
        f"<p>Thanks for joining GraftAI. Your calendar setup is complete.</p>"
        f"<p>Visit <a href=\"{os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')}\">GraftAI Dashboard</a></p>"
    )
    text_body = (
        f"Welcome {full_name}\n\n"
        "Thanks for joining GraftAI. Your calendar setup is complete.\n"
        f"Go to {os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')}\n"
    )
    await send_custom_notification(user_email, subject, "Welcome to GraftAI", html_body, text_body)

