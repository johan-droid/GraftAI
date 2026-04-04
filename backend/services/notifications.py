import logging
import os
from backend.services.email import send_email, render_template

logger = logging.getLogger(__name__)


def _build_event_templates(notification_type: str, event_data: dict) -> tuple[str, str, str]:
    user_name = event_data.get("user_name") or event_data.get("full_name") or "GraftAI user"
    title = event_data.get("title") or "Untitled Event"
    start_time = event_data.get("start_time") or "as scheduled"
    end_time = event_data.get("end_time") or ""
    
    # Meeting details
    is_meeting = event_data.get("is_meeting", False)
    meeting_link = event_data.get("meeting_link")
    
    # Auto-detect platform from link
    meeting_platform = event_data.get("meeting_platform", "")
    if meeting_link and not meeting_platform:
        link_low = meeting_link.lower()
        if "zoom.us" in link_low: meeting_platform = "Zoom"
        elif "meet.google.com" in link_low: meeting_platform = "Google Meet"
        elif "teams.microsoft.com" in link_low: meeting_platform = "Microsoft Teams"
    
    platform_label = (meeting_platform or "Digital Hub").replace("_", " ").title()

    template_context = {
        "full_name": user_name,
        "event_title": title,
        "start_time": start_time,
        "end_time": end_time,
        "is_meeting": is_meeting or bool(meeting_link),
        "meeting_platform": platform_label,
        "meeting_link": meeting_link,
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "https://graftai.tech").rstrip("/")
    }

    if notification_type == "created":
        subject = f"🎉 New event created: {title}"
        template_context["action_title"] = "New Event Scheduled"
        template_context["summary_text"] = f"A new event has been added to your calendar: {title}."
        html_body = render_template("event_alert.html", template_context)
        text_body = f"Hello {user_name},\n\nAn event has been added: '{title}'\nTime: {start_time} - {end_time}\n"

    elif notification_type == "updated":
        subject = f"✅ Event Updated: '{title}'"
        template_context["action_title"] = "Event Details Modified"
        template_context["summary_text"] = f"Your event '{title}' has been updated with new information."
        html_body = render_template("event_alert.html", template_context)
        text_body = f"Hello {user_name},\n\nYour event '{title}' has been updated.\nTime: {start_time} - {end_time}\n"

    elif notification_type == "deleted":
        subject = f"🗑 Event Removed: {title}"
        template_context["action_title"] = "Event Canceled"
        template_context["summary_text"] = f"Your event '{title}' has been removed from your calendar."
        html_body = render_template("event_alert.html", template_context)
        text_body = f"Hello {user_name},\n\nYour event '{title}' was deleted.\n"

    elif notification_type == "reminder":
        subject = f"⏳ Reminder: '{title}' starting soon"
        html_body = render_template("reminder.html", template_context)
        text_body = f"Hello {user_name},\n\nReminder: '{title}' is starting soon at {start_time}.\n"

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


async def notify_event_reminder(user_email: str, user_player_ids: list[str], event_data: dict):
    await _send_notification(user_email, user_player_ids, "reminder", event_data)


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
    subject = "🚀 Welcome to GraftAI - Your AI Copilot is Ready!"
    template_context = {
        "full_name": full_name,
        "frontend_url": os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
    }
    
    html_body = render_template("welcome.html", template_context)
    text_body = f"Welcome to GraftAI, {full_name}! Your AI Copilot is ready to help you reclaim your time."
    
    await send_custom_notification(user_email, subject, "Welcome to GraftAI", html_body, text_body)


async def notify_account_deleted_email(user_email: str, full_name: str):
    subject = "Account successfully deleted - GraftAI"
    html_body = f"<h1>Farewell, {full_name}</h1><p>Your GraftAI account has been permanently deleted.</p>"
    text_body = f"Farewell {full_name},\n\nThis email confirms that your GraftAI account has been permanently deleted. We wish you the best!"
    await send_custom_notification(user_email, subject, "Account deleted", html_body, text_body)

