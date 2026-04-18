import logging
import os
from typing import Optional
from backend.auth.logic import create_public_action_token
from backend.services.mail_service import send_email, render_template
# Removed: redis_client and NotificationTable deleted

logger = logging.getLogger(__name__)


# OneSignal integration removed: keep a no-op fallback to preserve call sites.
async def send_push_notification(
    user_player_ids: list[str], heading: str, content: str, data: Optional[dict] = None
):
    logger.debug("Push notification skipped: OneSignal integration removed.")
    return None


def _build_event_templates(
    notification_type: str, event_data: dict
) -> tuple[str, str, str]:
    user_name = (
        event_data.get("user_name") or event_data.get("full_name") or "GraftAI user"
    )
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
        if "zoom.us" in link_low:
            meeting_platform = "Zoom"
        elif "meet.google.com" in link_low:
            meeting_platform = "Google Meet"
        elif "teams.microsoft.com" in link_low:
            meeting_platform = "Microsoft Teams"

    platform_label = (meeting_platform or "Digital Hub").replace("_", " ").title()

    template_context = {
        "full_name": user_name,
        "event_title": title,
        "start_time": start_time,
        "end_time": end_time,
        "is_meeting": is_meeting or bool(meeting_link),
        "meeting_platform": platform_label,
        "meeting_link": meeting_link,
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "https://graftai.tech").rstrip(
            "/"
        ),
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


async def _send_notification(
    recipient_emails: list[str],
    user_player_ids: list[str],
    content_type: str,
    event_data: dict,
):
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
                data={"event_id": str(event_data.get("id"))},
            )
            logger.info("Push notification triggered")
        except Exception as e:
            logger.warning(f"Push notification failed: {e}")

    # Realtime pub/sub REMOVED
    pass

    # Persist an in-app notification record for the user
    # REMOVED: NotificationTable deleted in bare-minimum schema refactor.
    return


async def notify_event_created(
    recipient_emails: list[str], user_player_ids: list[str], event_data: dict
):
    await _send_notification(recipient_emails, user_player_ids, "created", event_data)


async def notify_event_updated(
    recipient_emails: list[str], user_player_ids: list[str], event_data: dict
):
    await _send_notification(recipient_emails, user_player_ids, "updated", event_data)


async def notify_event_deleted(
    recipient_emails: list[str], user_player_ids: list[str], event_data: dict
):
    await _send_notification(recipient_emails, user_player_ids, "deleted", event_data)


async def notify_event_reminder(
    recipient_emails: list[str], user_player_ids: list[str], event_data: dict
):
    await _send_notification(recipient_emails, user_player_ids, "reminder", event_data)


class NotificationService:
    """Compatibility wrapper for route-level notification use."""

    def __init__(self, db=None):
        self.db = db

    async def send_booking_confirmation(self, to_email: str, booking_data: dict):
        title = booking_data.get("title") or "Booking"
        attendee_name = booking_data.get("attendee_name") or "there"
        start_time = booking_data.get("start_time") or "as scheduled"
        end_time = booking_data.get("end_time") or ""
        confirmation_code = booking_data.get("confirmation_code") or ""

        subject = f"Booking confirmed: {title}"
        message = (
            f"Hello {attendee_name},\n\n"
            f"Your booking '{title}' is confirmed for {start_time}"
            f"{(' to ' + end_time) if end_time else ''}.\n"
            f"Confirmation code: {confirmation_code}\n"
        )

        import html

        escaped_attendee = html.escape(attendee_name)
        escaped_title = html.escape(title)
        escaped_start = html.escape(start_time)
        escaped_end = html.escape(end_time) if end_time else ""
        escaped_code = html.escape(confirmation_code)

        await send_custom_notification(
            user_email=to_email,
            subject=subject,
            message=message,
            html_body=(
                f"<p>Hello {escaped_attendee},</p>"
                f"<p>Your booking <strong>{escaped_title}</strong> is confirmed for {escaped_start}"
                f"{(' to ' + escaped_end) if escaped_end else ''}.</p>"
                f"<p>Confirmation code: <strong>{escaped_code}</strong></p>"
            ),
            text_body=message,
        )

    async def send_event_reminder(self, to_email: str, event_data: dict):
        title = event_data.get("title") or "Upcoming event"
        start_time = event_data.get("start_time") or "soon"
        user_name = event_data.get("user_name") or "there"

        subject = f"Reminder: {title}"
        message = f"Hello {user_name},\n\nReminder: '{title}' starts at {start_time}.\n"

        await send_custom_notification(
            user_email=to_email,
            subject=subject,
            message=message,
            html_body=f"<p>Hello {user_name},</p><p>Reminder: <strong>{title}</strong> starts at {start_time}.</p>",
            text_body=message,
        )

    async def send_team_invite(self, to_email: str, invite_data: dict):
        inviter_name = invite_data.get("inviter_name") or "A teammate"
        team_name = invite_data.get("team_name") or "your team"
        invite_link = invite_data.get("invite_link") or ""

        subject = f"You're invited to join {team_name}"
        message = (
            f"Hello,\n\n"
            f"{inviter_name} invited you to join {team_name}.\n"
            f"{('Accept invite: ' + invite_link) if invite_link else ''}\n"
        )

        import html
        from urllib.parse import urlparse

        escaped_inviter_name = html.escape(inviter_name)
        escaped_team_name = html.escape(team_name)

        link_html = ""
        if invite_link:
            parsed = urlparse(invite_link)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                escaped_link = html.escape(invite_link, quote=True)
                link_html = f'<p><a href="{escaped_link}">Accept invite</a></p>'
            else:
                link_html = "<p>Invite link is invalid or expired</p>"

        await send_custom_notification(
            user_email=to_email,
            subject=subject,
            message=message,
            html_body=(
                f"<p>Hello,</p>"
                f"<p>{escaped_inviter_name} invited you to join <strong>{escaped_team_name}</strong>.</p>"
                f"{link_html}"
            ),
            text_body=message,
        )


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


async def send_email_verification_code(user_email: str, full_name: str, code: str):
    subject = "Verify your GraftAI email address"
    template_context = {
        "full_name": full_name,
        "code": code,
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        ),
    }
    html_body = render_template("verification.html", template_context)
    text_body = (
        f"Hello {full_name},\n\n"
        f"Your GraftAI verification code is: {code}\n\n"
        "Enter this code on the verification page to complete your registration. "
        "This code expires in 15 minutes.\n\n"
        "If you did not request this, please ignore this email.\n"
    )
    await send_custom_notification(user_email, subject, text_body, html_body, text_body)


def _public_booking_links(booking_id: str, attendee_email: str) -> dict[str, str]:
    base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    token = create_public_action_token(booking_id, attendee_email)
    return {
        "token": token,
        "manage_url": f"{base}/public/bookings/{booking_id}?token={token}",
        "reschedule_url": f"{base}/public/bookings/{booking_id}/reschedule?token={token}",
        "cancel_url": f"{base}/public/bookings/{booking_id}/cancel?token={token}",
    }


async def send_booking_confirmation_to_attendee(
    attendee_email: str,
    attendee_name: str,
    organizer_name: str,
    event_title: str,
    attendee_start_time: str,
    attendee_end_time: str,
    attendee_zone: str,
    meeting_url: Optional[str] = None,
    booking_id: Optional[str] = None,
):
    links = (
        _public_booking_links(booking_id, attendee_email)
        if booking_id
        else {
            "manage_url": "",
            "reschedule_url": "",
            "cancel_url": "",
        }
    )
    subject = f"Booking confirmed: {event_title}"
    template_context = {
        "full_name": attendee_name,
        "organizer_name": organizer_name,
        "event_title": event_title,
        "start_time": attendee_start_time,
        "end_time": attendee_end_time,
        "attendee_zone": attendee_zone,
        "meeting_url": meeting_url,
        "manage_url": links.get("manage_url"),
        "reschedule_url": links.get("reschedule_url"),
        "cancel_url": links.get("cancel_url"),
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        ),
    }
    html_body = render_template("booking_confirmation_attendee.html", template_context)
    text_body = (
        f"Hello {attendee_name},\n\n"
        f"Your booking with {organizer_name} is confirmed.\n"
        f"Event: {event_title}\n"
        f"Time: {attendee_start_time} - {attendee_end_time} ({attendee_zone})\n"
        f"Manage booking: {links.get('manage_url', '')}\n"
        f"Reschedule: {links.get('reschedule_url', '')}\n"
        f"Cancel: {links.get('cancel_url', '')}\n"
    )
    await send_custom_notification(
        attendee_email, subject, text_body, html_body, text_body
    )


async def send_booking_confirmation_to_organizer(
    organizer_email: str,
    organizer_name: str,
    attendee_name: str,
    attendee_email: str,
    event_title: str,
    organizer_start_time: str,
    organizer_end_time: str,
    meeting_url: Optional[str] = None,
    booking_id: Optional[str] = None,
):
    links = (
        _public_booking_links(booking_id, attendee_email)
        if booking_id
        else {
            "manage_url": "",
        }
    )
    subject = f"New booking: {event_title}"
    template_context = {
        "full_name": organizer_name,
        "attendee_name": attendee_name,
        "attendee_email": attendee_email,
        "event_title": event_title,
        "start_time": organizer_start_time,
        "end_time": organizer_end_time,
        "meeting_url": meeting_url,
        "manage_url": links.get("manage_url"),
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        ),
    }
    html_body = render_template("booking_confirmation_organizer.html", template_context)
    text_body = (
        f"Hello {organizer_name},\n\n"
        f"A new booking has been created.\n"
        f"Attendee: {attendee_name} <{attendee_email}>\n"
        f"Event: {event_title}\n"
        f"Time: {organizer_start_time} - {organizer_end_time}\n"
        f"Manage booking: {links.get('manage_url', '')}\n"
    )
    await send_custom_notification(
        organizer_email, subject, text_body, html_body, text_body
    )


async def send_booking_rescheduled_to_both(
    organizer_email: str,
    organizer_name: str,
    attendee_email: str,
    attendee_name: str,
    event_title: str,
    old_time: str,
    new_time: str,
    meeting_url: Optional[str] = None,
    booking_id: Optional[str] = None,
):
    links = (
        _public_booking_links(booking_id, attendee_email)
        if booking_id
        else {
            "manage_url": "",
            "reschedule_url": "",
            "cancel_url": "",
        }
    )
    subject = f"Booking rescheduled: {event_title}"

    organizer_context = {
        "full_name": organizer_name,
        "event_title": event_title,
        "old_time": old_time,
        "new_time": new_time,
        "meeting_url": meeting_url,
        "manage_url": links.get("manage_url"),
        "reschedule_url": links.get("reschedule_url"),
        "cancel_url": links.get("cancel_url"),
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        ),
    }
    attendee_context = {
        **organizer_context,
        "full_name": attendee_name,
    }

    organizer_html = render_template("booking_rescheduled.html", organizer_context)
    attendee_html = render_template("booking_rescheduled.html", attendee_context)

    organizer_text = (
        f"Hello {organizer_name},\n\n"
        f"Booking '{event_title}' has been rescheduled.\n"
        f"Old: {old_time}\n"
        f"New: {new_time}\n"
        f"Manage booking: {links.get('manage_url', '')}\n"
    )
    attendee_text = (
        f"Hello {attendee_name},\n\n"
        f"Booking '{event_title}' has been rescheduled.\n"
        f"Old: {old_time}\n"
        f"New: {new_time}\n"
        f"Manage booking: {links.get('manage_url', '')}\n"
    )

    await send_custom_notification(
        organizer_email, subject, organizer_text, organizer_html, organizer_text
    )
    await send_custom_notification(
        attendee_email, subject, attendee_text, attendee_html, attendee_text
    )


async def send_booking_cancelled_to_both(
    organizer_email: str,
    organizer_name: str,
    attendee_email: str,
    attendee_name: str,
    event_title: str,
    original_time: str,
    cancelled_by: str,
    cancellation_reason: Optional[str] = None,
    booking_id: Optional[str] = None,
):
    links = (
        _public_booking_links(booking_id, attendee_email)
        if booking_id
        else {
            "reschedule_url": "",
        }
    )
    subject = f"Booking cancelled: {event_title}"

    organizer_context = {
        "full_name": organizer_name,
        "event_title": event_title,
        "original_time": original_time,
        "cancelled_by": cancelled_by,
        "cancellation_reason": cancellation_reason,
        "reschedule_url": links.get("reschedule_url"),
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        ),
    }
    attendee_context = {
        **organizer_context,
        "full_name": attendee_name,
    }

    organizer_html = render_template("booking_cancelled.html", organizer_context)
    attendee_html = render_template("booking_cancelled.html", attendee_context)

    organizer_text = (
        f"Hello {organizer_name},\n\n"
        f"Booking '{event_title}' at {original_time} was cancelled by {cancelled_by}.\n"
        + (f"Reason: {cancellation_reason}.\n" if cancellation_reason else "")
    )
    attendee_text = (
        f"Hello {attendee_name},\n\n"
        f"Booking '{event_title}' at {original_time} was cancelled by {cancelled_by}.\n"
        + (f"Reason: {cancellation_reason}.\n" if cancellation_reason else "")
    )

    await send_custom_notification(
        organizer_email, subject, organizer_text, organizer_html, organizer_text
    )
    await send_custom_notification(
        attendee_email, subject, attendee_text, attendee_html, attendee_text
    )


async def send_booking_reminder_to_organizer(
    organizer_email: str,
    organizer_name: str,
    attendee_name: str,
    attendee_email: str,
    event_title: str,
    organizer_start_time: str,
    organizer_end_time: str,
    organizer_timezone: str,
    booking_id: Optional[str] = None,
):
    base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    manage_url = f"{base}/dashboard/calendar"
    subject = f"Reminder: {event_title} starts in 24 hours"

    template_context = {
        "full_name": organizer_name,
        "attendee_name": attendee_name,
        "attendee_email": attendee_email,
        "event_title": event_title,
        "start_time": organizer_start_time,
        "end_time": organizer_end_time,
        "organizer_timezone": organizer_timezone,
        "booking_id": booking_id,
        "manage_url": manage_url,
        "frontend_url": base,
    }

    html_body = render_template("booking_reminder_organizer.html", template_context)
    text_body = (
        f"Hello {organizer_name},\n\n"
        f"Reminder: '{event_title}' is scheduled for {organizer_start_time} - {organizer_end_time} ({organizer_timezone}).\n"
        f"Attendee: {attendee_name} <{attendee_email}>\n"
        f"Manage in dashboard: {manage_url}\n"
    )

    await send_custom_notification(
        organizer_email, subject, text_body, html_body, text_body
    )


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
        "upgrade_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        )
        + "/pricing",
        "billing_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        )
        + "/dashboard/settings/billing",
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip(
            "/"
        ),
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

    # Persist an in-app quota warning REMOVED
    return


async def notify_welcome_email(user_email: str, full_name: str):
    subject = "🚀 Welcome to GraftAI - Your AI Copilot is Ready!"
    template_context = {
        "full_name": full_name,
        "frontend_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000"),
    }

    html_body = render_template("welcome.html", template_context)
    text_body = f"Welcome to GraftAI, {full_name}! Your AI Copilot is ready to help you reclaim your time."

    await send_custom_notification(
        user_email, subject, "Welcome to GraftAI", html_body, text_body
    )


async def notify_account_deleted_email(user_email: str, full_name: str):
    subject = "Account successfully deleted - GraftAI"
    html_body = f"<h1>Farewell, {full_name}</h1><p>Your GraftAI account has been permanently deleted.</p>"
    text_body = f"Farewell {full_name},\n\nThis email confirms that your GraftAI account has been permanently deleted. We wish you the best!"
    await send_custom_notification(
        user_email, subject, "Account deleted", html_body, text_body
    )
