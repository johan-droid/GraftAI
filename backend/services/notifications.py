import logging
import os
from typing import Optional
from backend.services.mail_service import send_email, render_template
from backend.services.redis_client import publish
from backend.utils.db import AsyncSessionLocal
from backend.models.tables import NotificationTable

logger = logging.getLogger(__name__)

# OneSignal integration removed: keep a no-op fallback to preserve call sites.
async def send_push_notification(user_player_ids: list[str], heading: str, content: str, data: Optional[dict] = None):
    logger.debug("Push notification skipped: OneSignal integration removed.")
    return None


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
        subject = f"📅 Meeting Confirmed: {title}"
        html_body = render_template("confirmation.html", template_context)
        text_body = f"Hello {user_name},\n\nYour meeting '{title}' has been confirmed for {start_time}.\n"

    elif notification_type == "updated":
        subject = f"🔄 Update: Meeting Details Changed - {title}"
        html_body = render_template("update.html", template_context)
        text_body = f"Hello {user_name},\n\nYour meeting '{title}' has been updated to {start_time}.\n"

    elif notification_type == "deleted":
        subject = f"🗑️ Meeting Cancelled: {title}"
        html_body = render_template("cancellation.html", template_context)
        text_body = f"Hello {user_name},\n\nYour meeting '{title}' has been removed from the schedule.\n"

    elif notification_type == "reminder":
        subject = f"⏳ Reminder: '{title}' starting in 30 minutes"
        html_body = render_template("reminder.html", template_context)
        text_body = f"Hello {user_name},\n\nReminder: '{title}' is starting soon at {start_time}.\n"

    else:
        subject = f"Notification: {title}"
        html_body = f"<p>Hello {user_name},</p><p>{event_data.get('message', 'You have a new notification.')}</p>"
        text_body = f"Hello {user_name},\n\n{event_data.get('message', 'You have a new notification.')}\n"

    return subject, html_body, text_body


async def _send_notification(recipient_emails: list[str], user_player_ids: list[str], content_type: str, event_data: dict):
    # We only treat this as event notification if event id is present and not placeholder.
    event_id = event_data.get("id")
    if event_id is None or (isinstance(event_id, int) and event_id < 0):
        logger.info("Skipping event notification for non-event payload")
        return

    subject, html_body, text_body = _build_event_templates(content_type, event_data)

    # Email
    try:
        for email in recipient_emails:
            await send_email(email, subject, html_body, text_body)
        logger.info(f"Email notification queued for {len(recipient_emails)} recipients")
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
            await send_push_notification(
                user_player_ids,
                heading=headings.get(content_type, "Notification"),
                content=f"{event_data.get('title')} {content_type}",
                data={"event_id": str(event_data.get('id'))},
            )
            logger.info("Push notification triggered")
        except Exception as e:
            logger.warning(f"Push notification failed: {e}")

    # Realtime pub/sub
    try:
        channel = f"user_notifications_{event_data.get('user_id')}"
        payload = {"type": f"event_{content_type}", "event": event_data}
        await publish(channel, str(payload))
    except Exception as e:
        logger.warning(f"Realtime publish failed: {e}")

    # Persist an in-app notification record for the user
    try:
        # create a DB session and write notification
        async with AsyncSessionLocal() as session:
            notif = NotificationTable(
                user_id=str(event_data.get("user_id")),
                type=("event" if event_data.get("id") is not None else "system"),
                title=(event_data.get("title") or "Notification"),
                body=event_data.get("message") or "",
                data=event_data,
            )
            session.add(notif)
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to persist in-app notification: {e}")


async def notify_event_created(recipient_emails: list[str], user_player_ids: list[str], event_data: dict):
    await _send_notification(recipient_emails, user_player_ids, "created", event_data)


async def notify_event_updated(recipient_emails: list[str], user_player_ids: list[str], event_data: dict):
    await _send_notification(recipient_emails, user_player_ids, "updated", event_data)


async def notify_event_deleted(recipient_emails: list[str], user_player_ids: list[str], event_data: dict):
    await _send_notification(recipient_emails, user_player_ids, "deleted", event_data)


async def notify_event_reminder(recipient_emails: list[str], user_player_ids: list[str], event_data: dict):
    await _send_notification(recipient_emails, user_player_ids, "reminder", event_data)


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


async def notify_quota_warning(
    user_id: str,
    user_email: str,
    full_name: str,
    feature: str,
    current_count: int,
    limit: int,
):
    feature_map = {
        "ai_messages": "AI Copilot Messages",
        "calendar_syncs": "Calendar Syncs",
    }
    feature_label = feature_map.get(feature, feature.replace("_", " ").title())
    usage_percent = min(100, int((current_count / max(limit, 1)) * 100))
    subject = f"⚠️ {feature_label} usage is at {usage_percent}% — upgrade to keep going"

    template_context = {
        "full_name": full_name,
        "feature_label": feature_label,
        "current_count": current_count,
        "limit": limit,
        "usage_percent": usage_percent,
        "upgrade_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/") + "/pricing",
        "billing_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/") + "/dashboard/settings/billing",
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/"),
    }

    html_body = render_template("quota_warning.html", template_context)
    text_body = (
        f"Hello {full_name},\n\n"
        f"You are using {current_count} of {limit} available {feature_label.lower()} today ({usage_percent}%). "
        "Upgrade to the Pro plan to remove this limit and keep GraftAI working without interruption. "
        f"Visit {template_context['billing_url']} to upgrade now.\n\n"
        "Thank you,\nThe GraftAI team"
    )

    await send_custom_notification(user_email, subject, text_body, html_body, text_body)

    # Persist an in-app quota warning for the user
    try:
        async with AsyncSessionLocal() as session:
            notif = NotificationTable(
                user_id=user_id,
                type="quota",
                title=f"Quota alert: {feature_label} at {usage_percent}%",
                body=(
                    f"Your {feature_label} usage is at {current_count}/{limit} today. "
                    "Upgrade your plan to continue without interruption."
                ),
                data={
                    "feature": feature,
                    "current_count": current_count,
                    "limit": limit,
                    "usage_percent": usage_percent,
                    "upgrade_url": template_context["upgrade_url"],
                },
            )
            session.add(notif)
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to persist quota warning notification: {e}")


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

