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
    category = (event_data.get("category") or "meeting").lower()
    event_url = event_data.get("event_url") or os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

    # 1. Define Visual Specs (Strategy Pattern)
    themes = {
        "meeting":    {"color": "#4f46e5", "icon": "🗓️", "label": "Calendar Invite"},
        "deep_work":  {"color": "#7c3aed", "icon": "🧠", "label": "Deep Work Block"},
        "task":       {"color": "#16a34a", "icon": "✅", "label": "Task Reminder"},
        "birthday":   {"color": "#eab308", "icon": "🎂", "label": "Celebration"},
        "personal":   {"color": "#0d9488", "icon": "👤", "label": "Personal Time"},
        "out_of_office": {"color": "#dc2626", "icon": "✈️", "label": "Away"},
    }
    theme = themes.get(category, themes["meeting"])

    # 2. Build Category-Specific Hero Blocks
    is_meeting = event_data.get("is_meeting", False)
    meeting_link = event_data.get("meeting_link")
    meeting_platform = event_data.get("meeting_platform", "").replace("_", " ").title()
    agenda = event_data.get("agenda", "No agenda provided.")
    attendees = event_data.get("attendees", [])
    attendee_str = ", ".join([a.get("email", "") for a in attendees]) if attendees else "None"

    meeting_block = ""
    meeting_text = ""
    if is_meeting and meeting_link:
        meeting_block = (
            f"<div style='margin-top: 20px; padding: 15px; background: #f0f4ff; border-radius: 12px; border-left: 5px solid {theme['color']};'>"
            f"<h3 style='margin:0; color:{theme['color']};'>{theme['icon']} {meeting_platform} Connection</h3>"
            f"<p style='margin:10px 0;'><strong>Agenda:</strong> {agenda}</p>"
            f"<p style='margin:10px 0;'><strong>Coordination:</strong> {attendee_str}</p>"
            f"<a href='{meeting_link}' style='display:inline-block; margin-top:10px; padding:12px 24px; background:{theme['color']}; color:white; text-decoration:none; border-radius:8px; font-weight:600;'>Join {meeting_platform}</a>"
            f"</div>"
        )
        meeting_text = f"\nPLATFORM: {meeting_platform}\nAGENDA: {agenda}\nJOIN: {meeting_link}\n"
    elif category == "deep_work":
        meeting_block = (
            f"<div style='margin-top: 20px; padding: 15px; background: #faf5ff; border-radius: 12px; border: 1px dashed {theme['color']};'>"
            f"<h3 style='margin:0; color:{theme['color']};'>{theme['icon']} Focus Protocol Active</h3>"
            f"<p style='margin:10px 0;'>Notifications will be silenced to protect your flow state.</p>"
            f"</div>"
        )
        meeting_text = "\n[Focus Protocol Activated]\n"

    # 3. Handle Notification Type Logic
    if notification_type == "created":
        subject = f"{theme['icon']} New {category.title()}: {title}"
        html_body = (
            f"<div style=\"font-family: 'Inter', sans-serif; color: #1e293b;\">"
            f"<h1 style=\"color: {theme['color']};\">{theme['label']} Created</h1>"
            f"<p>Hello {user_name}, your <strong>{title}</strong> is now secured.</p>"
            f"<div style=\"background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;\">"
            f"<p style=\"margin:0;\">🕤 <strong>Timing:</strong> {start_time} - {end_time}</p>"
            f"<p style=\"margin:5px 0 0 0;\">📍 <strong>Category:</strong> {category.replace('_', ' ').title()}</p>"
            f"</div>"
            f"{meeting_block}"
            f"<p style=\"margin-top:20px;\"><a href=\"{event_url}\" style=\"color: {theme['color']}; font-weight: 600;\">→ View Full Workspace</a></p>"
            f"</div>"
        )
        text_body = f"[{theme['label']}] New event: '{title}' from {start_time} to {end_time}.\n{meeting_text}"

    elif notification_type == "updated":
        subject = f"🔄 {category.title()} Updated: '{title}'"
        html_body = (
            f"<div style=\"font-family: 'Inter', sans-serif; color: #1e293b;\">"
            f"<h1 style=\"color: {theme['color']};\">Schedule Adjustment</h1>"
            f"<p>The following {category.replace('_', ' ')} has been synchronized:</p>"
            f"<h3>{theme['icon']} {title}</h3>"
            f"<p>New Timing: <strong>{start_time} - {end_time}</strong></p>"
            f"{meeting_block}"
            f"<p><a href=\"{event_url}\">Check Dashboard</a></p>"
            f"</div>"
        )
        text_body = f"UPDATE: '{title}' time changed to {start_time} - {end_time}.\n{meeting_text}"

    elif notification_type == "deleted":
        subject = f"🗑️ {category.title()} Removed: {title}"
        html_body = (
            f"<div style=\"font-family: 'Inter', sans-serif;\">"
            f"<h1 style=\"color: #64748b;\">Session Canceled</h1>"
            f"<p>Your <strong>{category.replace('_', ' ')}</strong> titled '{title}' has been removed from your active schedule.</p>"
            f"<p><a href=\"{event_url}\">Re-book or Review Schedule</a></p>"
            f"</div>"
        )
        text_body = f"REMOVED: Your {category} '{title}' has been deleted. Link: {event_url}"

    elif notification_type == "reminder":
        subject = f"⏳ {theme['icon']} Starting Soon: '{title}'"
        html_body = (
            f"<div style=\"font-family: 'Inter', sans-serif; border: 2px solid {theme['color']}; padding: 25px; border-radius: 16px;\">"
            f"<h2 style=\"margin:0; color: {theme['color']};\">{theme['icon']} 15m Countdown</h2>"
            f"<p style=\"font-size: 18px;\"><strong>{title}</strong> starts at {start_time}.</p>"
            f"{meeting_block}"
            f"</div>"
        )
        text_body = f"REMINDER: '{title}' starts soon at {start_time}.\n{meeting_text}"
    else:
        subject = f"Notification: {title}"
        html_body = f"<p>Hello {user_name},</p><p>{event_data.get('message', 'You have a new notification.')}</p>"
        text_body = f"Hello {user_name},\n\n{event_data.get('message', 'You have a new notification.')}\n"

    return subject, html_body, text_body

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
        await publish(channel, str(payload))
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
    frontend_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
    
    html_body = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1e293b; line-height: 1.6;">
        <div style="text-align: center; padding-bottom: 20px;">
            <h1 style="color: #6366f1; margin-bottom: 10px;">Welcome to the Future of Scheduling, {full_name}!</h1>
            <p style="font-size: 18px; color: #64748b;">Your GraftAI account is now active and your workspace is ready for action.</p>
        </div>
        
        <div style="background-color: #f8fafc; border-radius: 16px; padding: 24px; border: 1px solid #e2e8f0; margin-bottom: 24px;">
            <h2 style="font-size: 16px; text-transform: uppercase; letter-spacing: 0.05em; color: #6366f1; margin-top: 0;">What's Next?</h2>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="margin-bottom: 12px; display: flex; align-items: flex-start;">
                    <span style="font-size: 20px; margin-right: 12px;">🗓️</span>
                    <div><strong>Connect Your Calendar:</strong> Sync Google or Microsoft to enable seamless AI-powered scheduling.</div>
                </li>
                <li style="margin-bottom: 12px; display: flex; align-items: flex-start;">
                    <span style="font-size: 20px; margin-right: 12px;">🤖</span>
                    <div><strong>Meet Your Copilot:</strong> Head to the Chat tab and ask GraftAI to "Schedule a meeting with the team tomorrow at 10 AM".</div>
                </li>
                <li style="margin-bottom: 12px; display: flex; align-items: flex-start;">
                    <span style="font-size: 20px; margin-right: 12px;">📊</span>
                    <div><strong>Smart Analytics:</strong> Gain real-time insights into your time management on your custom dashboard.</div>
                </li>
            </ul>
        </div>
        
        <div style="text-align: center;">
            <a href="{frontend_url}" style="background-color: #6366f1; color: white; padding: 14px 28px; border-radius: 12px; text-decoration: none; font-weight: 600; display: inline-block; transition: background-color 0.2s;">Go to My Dashboard</a>
        </div>
        
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 32px 0;">
        
        <p style="font-size: 12px; color: #94a3b8; text-align: center;">
            You received this email because you signed up for GraftAI.<br>
            Level 12, Innovation Hub, Tech City.
        </p>
    </div>
    """
    
    text_body = f"""
    Welcome to GraftAI, {full_name}!
    
    Your AI Copilot is ready to help you reclaim your time.
    
    KEY FEATURES:
    - Real-time AI Scheduling via natural language
    - Smart Analytics & Time Insights
    - One-click Calendar Synchronization
    - Proactive Meeting Recommendations
    
    Get started here: {frontend_url}
    
    Best,
    The GraftAI Team
    """
    
    await send_custom_notification(user_email, subject, "Welcome to GraftAI", html_body, text_body)


async def notify_account_deleted_email(user_email: str, full_name: str):
    subject = "Account successfully deleted - GraftAI"
    html_body = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1e293b; line-height: 1.6;">
        <h1 style="color: #6366f1;">Farewell, {full_name}</h1>
        <p>This email confirms that your GraftAI account and all associated data have been permanently deleted from our servers as per your request.</p>
        <p>We're sorry to see you go, but we wish you the best in your productivity journey! If you ever want to come back, you can register a new account at any time.</p>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 32px 0;">
        <p style="font-size: 12px; color: #94a3b8; text-align: center;">GraftAI Team • Productivity First</p>
    </div>
    """
    text_body = f"Farewell {full_name},\n\nThis email confirms that your GraftAI account has been permanently deleted. We wish you the best!"
    await send_custom_notification(user_email, subject, "Account deleted", html_body, text_body)

