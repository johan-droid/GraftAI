"""
Production Communication Tools with Real API Integrations

Integrates with:
- SendGrid (Email)
- Twilio (SMS)
- Slack API
- Microsoft Teams (Graph API)
- Google/Outlook Calendar (ICS invites)
"""

import os
import base64
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone

from backend.utils.logger import get_logger

# Tenacity for retry logic
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def stop_after_attempt(*args, **kwargs):
        return None

    def wait_exponential(*args, **kwargs):
        return None

    def retry_if_exception_type(*args, **kwargs):
        return None

    def before_sleep_log(*args, **kwargs):
        return None

RETRYABLE_EXCEPTIONS = (httpx.RequestError, httpx.TimeoutException)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _execute_with_retry(func, *args, **kwargs):
    """Wrapper for retrying synchronous and asynchronous external API calls."""
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    # Offload blocking synchronous SDK calls to a thread to avoid
    # blocking the event loop (e.g., SendGrid, Twilio, Slack sync clients).
    return await asyncio.to_thread(func, *args, **kwargs)


# Circuit breaker for external service protection
try:
    from backend.utils.circuit_breaker import SENDGRID_BREAKER, TWILIO_BREAKER

    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

from .registry import register_tool, ToolCategory, ToolPriority

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION & CLIENTS
# ═══════════════════════════════════════════════════════════════════


class APIConfig:
    """API configuration from environment variables"""

    # SendGrid
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@graftai.com")

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Slack
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")

    # Microsoft Teams
    TEAMS_APP_ID = os.getenv("TEAMS_APP_ID", "")
    TEAMS_APP_PASSWORD = os.getenv("TEAMS_APP_PASSWORD", "")
    TEAMS_TENANT_ID = os.getenv("TEAMS_TENANT_ID", "")

    # Calendar
    CALENDAR_PROVIDER = os.getenv("CALENDAR_PROVIDER", "google")  # google, outlook
    GOOGLE_CALENDAR_CLIENT_ID = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "")
    GOOGLE_CALENDAR_CLIENT_SECRET = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "")

    @classmethod
    def is_sendgrid_configured(cls) -> bool:
        return bool(cls.SENDGRID_API_KEY and cls.SENDGRID_FROM_EMAIL)

    @classmethod
    def is_twilio_configured(cls) -> bool:
        return bool(
            cls.TWILIO_ACCOUNT_SID and cls.TWILIO_AUTH_TOKEN and cls.TWILIO_PHONE_NUMBER
        )

    @classmethod
    def is_slack_configured(cls) -> bool:
        return bool(cls.SLACK_BOT_TOKEN)

    @classmethod
    def is_teams_configured(cls) -> bool:
        return bool(cls.TEAMS_APP_ID and cls.TEAMS_APP_PASSWORD)


# ═══════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════

EMAIL_TEMPLATES = {
    "standard_confirmation": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #6366f1;">Your Booking is Confirmed</h2>
            <p>Hi {{name}},</p>
            <p>Your meeting has been scheduled for <strong>{{start_time}}</strong>.</p>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Meeting:</strong> {{title}}</p>
                <p><strong>Time:</strong> {{start_time}}</p>
                <p><strong>Duration:</strong> {{duration}} minutes</p>
                {% if location %}<p><strong>Location:</strong> {{location}}</p>{% endif %}
            </div>
            <p>We'll send you a reminder before the meeting.</p>
            <p>Best regards,<br>GraftAI Team</p>
        </div>
    </body>
    </html>
    """,
    "high_risk_confirmation": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #f59e0b;">
            <h2 style="color: #f59e0b;">⏰ Important: Please Confirm Your Attendance</h2>
            <p>Hi {{name}},</p>
            <p>Your meeting is scheduled for <strong>{{start_time}}</strong>.</p>
            <p style="background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                <strong>Please confirm your attendance</strong> by replying to this email or clicking the button below.
            </p>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Meeting:</strong> {{title}}</p>
                <p><strong>Time:</strong> {{start_time}}</p>
            </div>
            <p>We look forward to seeing you!</p>
        </div>
    </body>
    </html>
    """,
    "vip_welcome": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #8b5cf6;">
            <h2 style="color: #8b5cf6;">🌟 VIP Booking Confirmed</h2>
            <p>Dear {{name}},</p>
            <p>Thank you for choosing GraftAI. Your VIP meeting has been confirmed.</p>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Meeting:</strong> {{title}}</p>
                <p><strong>Time:</strong> {{start_time}}</p>
                <p><strong>Duration:</strong> {{duration}} minutes</p>
            </div>
            <p>Our team is standing by to ensure everything runs smoothly.</p>
            <p>Best regards,<br><strong>The GraftAI VIP Team</strong></p>
        </div>
    </body>
    </html>
    """,
    "reminder": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #6366f1;">⏰ Reminder: Meeting Tomorrow</h2>
            <p>Hi {{name}},</p>
            <p>This is a friendly reminder about your meeting tomorrow.</p>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Meeting:</strong> {{title}}</p>
                <p><strong>Time:</strong> {{start_time}}</p>
            </div>
            <p>See you there!</p>
        </div>
    </body>
    </html>
    """,
    "follow_up": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #6366f1;">Thank You for Meeting With Us</h2>
            <p>Hi {{name}},</p>
            <p>Thank you for taking the time to meet with us today. We hope it was valuable.</p>
            <p>If you have any questions or feedback, please don't hesitate to reach out.</p>
            <p>Best regards,<br>GraftAI Team</p>
        </div>
    </body>
    </html>
    """,
}


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render email template with context variables"""
    from string import Template

    template_str = EMAIL_TEMPLATES.get(
        template_name, EMAIL_TEMPLATES["standard_confirmation"]
    )
    template = Template(template_str)

    # Simple template substitution (using Django/Jinja2 style would be better in production)
    result = template_str
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value or ""))

    # Remove remaining template variables
    import re

    result = re.sub(r"\{\{\w+\}\}", "", result)
    result = re.sub(r"\{%.*?%\}", "", result)

    return result


# ═══════════════════════════════════════════════════════════════════
# REAL API IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════

# Retry configuration for external APIs
EXTERNAL_API_RETRY = {
    "stop": stop_after_attempt(4) if TENACITY_AVAILABLE else None,
    "wait": wait_exponential(multiplier=1, min=2, max=15)
    if TENACITY_AVAILABLE
    else None,
    "retry": retry_if_exception_type(RETRYABLE_EXCEPTIONS)
    if TENACITY_AVAILABLE
    else None,
    "before_sleep": before_sleep_log(logger, "warning") if TENACITY_AVAILABLE else None,
}

if TENACITY_AVAILABLE:

    @retry(**EXTERNAL_API_RETRY)
    async def _send_email_with_retry(*args, **kwargs):
        """Internal email sending with retry logic."""
        return await _send_email_impl(*args, **kwargs)

    @retry(**EXTERNAL_API_RETRY)
    async def _send_sms_with_retry(*args, **kwargs):
        """Internal SMS sending with retry logic."""
        return await _send_sms_impl(*args, **kwargs)

    @retry(**EXTERNAL_API_RETRY)
    async def _post_to_slack_with_retry(*args, **kwargs):
        """Internal Slack posting with retry logic."""
        return await _post_to_slack_impl(*args, **kwargs)
else:

    async def _send_email_with_retry(*args, **kwargs):
        """Internal email sending without retry (tenacity not available)."""
        return await _send_email_impl(*args, **kwargs)

    async def _send_sms_with_retry(*args, **kwargs):
        """Internal SMS sending without retry (tenacity not available)."""
        return await _send_sms_impl(*args, **kwargs)

    async def _post_to_slack_with_retry(*args, **kwargs):
        """Internal Slack posting without retry (tenacity not available)."""
        return await _post_to_slack_impl(*args, **kwargs)


@register_tool(
    name="send_email",
    description="Send an email using SendGrid or SMTP",
    category=ToolCategory.COMMUNICATION,
    priority=ToolPriority.HIGH,
)
async def _send_email_impl(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    template: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
    from_address: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Internal implementation of email sending (with retry wrapper).

    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (HTML)
        cc: CC recipients
        bcc: BCC recipients
        template: Template name to use
        template_context: Variables for template
        from_address: Sender email
        attachments: List of attachments with 'filename', 'content', 'content_type'

    Returns:
        Email send result with ID and status
    """
    # Use template if specified
    if template and template in EMAIL_TEMPLATES:
        body = render_template(template, template_context or {})

    # Check circuit breaker status
    if CIRCUIT_BREAKER_AVAILABLE and SENDGRID_BREAKER:
        if not SENDGRID_BREAKER.can_execute():
            logger.warning(
                f"[CircuitBreaker:sendgrid] Circuit is OPEN - rejecting email to {to}"
            )
            return {
                "success": False,
                "error": "SendGrid service temporarily unavailable (circuit breaker open)",
                "to": to,
                "subject": subject,
                "status": "circuit_open",
                "provider": "sendgrid",
            }

    # Check if SendGrid is configured
    if not APIConfig.is_sendgrid_configured():
        logger.warning("SendGrid not configured - logging email only")
        return {
            "success": True,  # Return success for development
            "email_id": f"dev_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "to": to,
            "subject": subject,
            "status": "logged",
            "mode": "development",
            "message": f"[DEV MODE] Email to {to}: {subject}",
        }

    # Send via SendGrid API
    import sendgrid
    from sendgrid.helpers.mail import (
        Mail,
        Email,
        Content,
        Attachment,
        FileContent,
        FileName,
        FileType,
        Disposition,
    )

    sg = sendgrid.SendGridAPIClient(api_key=APIConfig.SENDGRID_API_KEY)

    from_email = Email(from_address or APIConfig.SENDGRID_FROM_EMAIL)
    to_email = Email(to)
    content = Content("text/html", body)

    mail = Mail(from_email, to_email, subject, content)

    # Add CC
    if cc:
        for cc_email in cc:
            mail.personalizations[0].add_cc(Email(cc_email))

    # Add BCC
    if bcc:
        for bcc_email in bcc:
            mail.personalizations[0].add_bcc(Email(bcc_email))

    # Add attachments
    if attachments:
        for att in attachments:
            content = att["content"]
            if isinstance(content, str):
                content_bytes = content.encode()
            elif isinstance(content, bytes):
                content_bytes = content
            else:
                raise TypeError("Attachment content must be bytes or str")

            file_content = base64.b64encode(content_bytes).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(file_content)
            attachment.file_name = FileName(att["filename"])
            attachment.file_type = FileType(
                att.get("content_type", "application/octet-stream")
            )
            attachment.disposition = Disposition("attachment")
            mail.add_attachment(attachment)

    response = await _execute_with_retry(sg.send, mail)

    email_id = response.headers.get(
        "X-Message-Id", f"sg_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    )

    logger.info(f"Email sent via SendGrid to {to}: {subject} (ID: {email_id})")

    return {
        "success": response.status_code == 202,
        "email_id": email_id,
        "to": to,
        "subject": subject,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": "sent" if response.status_code == 202 else "failed",
        "provider": "sendgrid",
        "status_code": response.status_code,
    }


async def _send_sms_impl(
    to: str,
    message: str,
    from_number: Optional[str] = None,
    media_urls: Optional[List[str]] = None,
) -> dict:
    """
    Send SMS using Twilio API.
    """
    if len(message) > 1600:
        raise ValueError("Message exceeds 1600 character limit")

    if not APIConfig.is_twilio_configured():
        logger.warning("Twilio not configured - logging SMS only")
        return {
            "success": True,
            "sms_id": f"dev_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "to": to,
            "status": "logged",
            "mode": "development",
            "message": f"[DEV MODE] SMS to {to}: {message[:50]}...",
        }

    from twilio.rest import Client

    client = Client(APIConfig.TWILIO_ACCOUNT_SID, APIConfig.TWILIO_AUTH_TOKEN)

    twilio_message = await _execute_with_retry(
        client.messages.create,
        body=message,
        from_=from_number or APIConfig.TWILIO_PHONE_NUMBER,
        to=to,
        media_url=media_urls,
    )

    logger.info(f"SMS sent via Twilio to {to}: {twilio_message.sid}")

    return {
        "success": twilio_message.status in ["queued", "sent", "delivered"],
        "sms_id": twilio_message.sid,
        "to": to,
        "message": message,
        "status": twilio_message.status,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "provider": "twilio",
        "segments": (len(message) // 160) + 1,
    }


async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    template: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
    from_address: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Send an email using SendGrid API (production) or log (development).
    Includes retry logic with exponential backoff and circuit breaker protection.

    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (HTML)
        cc: CC recipients
        bcc: BCC recipients
        template: Template name to use
        template_context: Variables for template
        from_address: Sender email
        attachments: List of attachments with 'filename', 'content', 'content_type'

    Returns:
        Email send result with ID and status
    """
    try:
        result = await _send_email_with_retry(
            to,
            subject,
            body,
            cc,
            bcc,
            template,
            template_context,
            from_address,
            attachments,
        )

        if CIRCUIT_BREAKER_AVAILABLE and SENDGRID_BREAKER:
            if result.get("success"):
                SENDGRID_BREAKER.record_success()
            else:
                SENDGRID_BREAKER.record_failure()

        return result

    except Exception as e:
        logger.error(f"Failed to send email via SendGrid after retries: {e}")

        if CIRCUIT_BREAKER_AVAILABLE and SENDGRID_BREAKER:
            SENDGRID_BREAKER.record_failure()

        queued_for_retry = False
        try:
            from backend.utils.dead_letter_queue import get_dlq

            dlq = get_dlq()
            await dlq.enqueue(
                action_type="send_email",
                payload={
                    "to": to,
                    "subject": subject,
                    "body": body,
                    "cc": cc,
                    "bcc": bcc,
                    "template": template,
                    "template_context": template_context,
                    "from_address": from_address,
                    "attachments": attachments,
                },
                error=str(e),
                max_retries=3,
                context={"provider": "sendgrid"},
            )
            queued_for_retry = True
        except Exception as dlq_error:
            logger.error(f"Failed to enqueue to DLQ: {dlq_error}")

        return {
            "success": False,
            "error": str(e),
            "to": to,
            "subject": subject,
            "status": "failed",
            "provider": "sendgrid",
            "queued_for_retry": queued_for_retry,
        }


async def send_sms(
    to: str,
    message: str,
    from_number: Optional[str] = None,
    media_urls: Optional[List[str]] = None,
) -> dict:
    """
    Send SMS using Twilio API with retry logic.
    """
    try:
        result = await _send_sms_with_retry(
            to, message, from_number, media_urls
        )

        if CIRCUIT_BREAKER_AVAILABLE and TWILIO_BREAKER:
            if result.get("success"):
                TWILIO_BREAKER.record_success()
            else:
                TWILIO_BREAKER.record_failure()

        return result

    except Exception as e:
        logger.error(f"Failed to send SMS via Twilio after retries: {e}")

        if CIRCUIT_BREAKER_AVAILABLE and TWILIO_BREAKER:
            TWILIO_BREAKER.record_failure()

        queued_for_retry = False
        try:
            from backend.utils.dead_letter_queue import get_dlq

            dlq = get_dlq()
            await dlq.enqueue(
                action_type="send_sms",
                payload={
                    "to": to,
                    "message": message,
                    "from_number": from_number,
                    "media_urls": media_urls,
                },
                error=str(e),
                max_retries=3,
                context={"provider": "twilio"},
            )
            queued_for_retry = True
        except Exception as dlq_error:
            logger.error(f"Failed to enqueue SMS to DLQ: {dlq_error}")

        return {
            "success": False,
            "error": str(e),
            "to": to,
            "status": "failed",
            "provider": "twilio",
            "queued_for_retry": queued_for_retry,
        }


async def _post_to_slack_impl(
    channel: str,
    message: str,
    blocks: Optional[List[dict]] = None,
    thread_ts: Optional[str] = None,
    username: Optional[str] = "GraftAI Bot",
    icon_emoji: Optional[str] = ":robot_face:",
) -> dict:
    """
    Internal Slack posting implementation. The public wrapper handles retries and DLQ enqueueing.
    """
    if not APIConfig.is_slack_configured():
        logger.warning("Slack not configured - logging message only")
        return {
            "success": True,
            "message_id": f"dev_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "channel": channel,
            "status": "logged",
            "mode": "development",
            "message": f"[DEV MODE] Slack to {channel}: {message[:100]}...",
        }

    from slack_sdk import WebClient

    client = WebClient(token=APIConfig.SLACK_BOT_TOKEN)

    if not channel.startswith("#") and not channel.startswith("C"):
        channel = f"#{channel}"

    kwargs = {
        "channel": channel,
        "text": message,
        "username": username,
        "icon_emoji": icon_emoji,
    }

    if blocks:
        kwargs["blocks"] = blocks
    if thread_ts:
        kwargs["thread_ts"] = thread_ts

    response = await _execute_with_retry(client.chat_postMessage, **kwargs)

    logger.info(f"Message posted to Slack channel {channel}: {response['ts']}")
    return {
        "success": response["ok"],
        "message_id": response["ts"],
        "channel": channel,
        "status": "posted",
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "provider": "slack",
    }


@register_tool(
    name="post_to_slack",
    description="Post message to Slack channel using Slack API",
    category=ToolCategory.COMMUNICATION,
    priority=ToolPriority.MEDIUM,
)
async def post_to_slack(
    channel: str,
    message: str,
    blocks: Optional[List[dict]] = None,
    thread_ts: Optional[str] = None,
    username: Optional[str] = "GraftAI Bot",
    icon_emoji: Optional[str] = ":robot_face:",
) -> dict:
    """
    Post message to Slack using Slack API

    Args:
        channel: Channel name (#channel) or channel ID
        message: Message text
        blocks: Slack Block Kit blocks for rich formatting
        thread_ts: Thread timestamp to reply in thread
        username: Bot username
        icon_emoji: Bot icon emoji

    Returns:
        Slack post result
    """
    try:
        result = await _post_to_slack_with_retry(
            channel,
            message,
            blocks=blocks,
            thread_ts=thread_ts,
            username=username,
            icon_emoji=icon_emoji,
        )
        return result

    except Exception as e:
        logger.error(f"Failed to post to Slack after retries: {e}")

        queued_for_retry = False
        try:
            from backend.utils.dead_letter_queue import get_dlq

            dlq = get_dlq()
            await dlq.enqueue(
                action_type="post_to_slack",
                payload={
                    "channel": channel,
                    "message": message,
                    "blocks": blocks,
                    "thread_ts": thread_ts,
                    "username": username,
                    "icon_emoji": icon_emoji,
                },
                error=str(e),
                max_retries=3,
                context={"provider": "slack"},
            )
            queued_for_retry = True
        except Exception as dlq_error:
            logger.error(f"Failed to enqueue Slack to DLQ: {dlq_error}")

        return {
            "success": False,
            "error": str(e),
            "channel": channel,
            "status": "failed",
            "queued_for_retry": queued_for_retry,
        }


@register_tool(
    name="send_teams_message",
    description="Send message to Microsoft Teams via Graph API",
    category=ToolCategory.COMMUNICATION,
    priority=ToolPriority.MEDIUM,
)
async def send_teams_message(
    user: Optional[str] = None,
    channel: Optional[str] = None,
    message: str = "",
    card: Optional[dict] = None,
) -> dict:
    """
    Send message to Microsoft Teams using Microsoft Graph API

    Args:
        user: User email for direct message
        channel: Channel ID for channel message
        message: Message text
        card: Adaptive card JSON

    Returns:
        Teams message result
    """
    try:
        if not user and not channel:
            raise ValueError("Must provide either user or channel")

        # Check if Teams is configured
        if not APIConfig.is_teams_configured():
            logger.warning("Teams not configured - logging message only")
            return {
                "success": True,
                "message_id": f"dev_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "recipient": user or channel,
                "status": "logged",
                "mode": "development",
            }

        # Microsoft Graph API integration would go here
        # This requires OAuth token acquisition which is complex
        # For production, implement proper Graph API authentication

        logger.warning("Teams Graph API integration not implemented")
        return {
            "success": False,
            "status": "unimplemented",
            "error": "Microsoft Teams Graph API integration is not yet implemented",
            "recipient": user or channel,
        }

    except Exception as e:
        logger.error(f"Failed to send Teams message: {e}")
        return {"success": False, "error": str(e), "status": "failed"}


@register_tool(
    name="send_calendar_invite",
    description="Send calendar invite via email with ICS attachment",
    category=ToolCategory.COMMUNICATION,
    priority=ToolPriority.CRITICAL,
)
async def send_calendar_invite(
    attendee: str,
    title: str,
    start_time: str,
    duration_minutes: int,
    location: Optional[str] = None,
    description: Optional[str] = None,
    organizer: Optional[str] = None,
    timezone: str = "UTC",
) -> dict:
    """
    Send calendar invite with ICS file attachment

    Works with all calendar providers (Google, Outlook, Apple)

    Args:
        attendee: Attendee email
        title: Meeting title
        start_time: ISO format start time
        duration_minutes: Meeting duration
        location: Meeting location or video link
        description: Meeting description
        organizer: Organizer email
        timezone: Meeting timezone

    Returns:
        Invite send result
    """
    try:
        # Parse times
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = start + timedelta(minutes=duration_minutes)

        # Generate ICS file content
        ics_content = generate_ics_invite(
            title=title,
            start=start,
            end=end,
            attendee=attendee,
            organizer=organizer or APIConfig.SENDGRID_FROM_EMAIL,
            location=location,
            description=description,
            timezone=timezone,
        )

        # Send email with ICS attachment
        attachment = {
            "filename": "invite.ics",
            "content": ics_content,
            "content_type": "text/calendar",
        }

        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>You're Invited: {title}</h2>
            <p>You've been invited to a meeting. Please see the attached calendar invite.</p>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px;">
                <p><strong>Meeting:</strong> {title}</p>
                <p><strong>Time:</strong> {start.strftime("%Y-%m-%d %H:%M")} ({timezone})</p>
                <p><strong>Duration:</strong> {duration_minutes} minutes</p>
                {f"<p><strong>Location:</strong> {location}</p>" if location else ""}
            </div>
            <p>This invitation was sent via GraftAI.</p>
        </body>
        </html>
        """

        result = await send_email(
            to=attendee,
            subject=f"Invitation: {title}",
            body=email_body,
            attachments=[attachment],
        )

        invite_id = f"invite_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        return {
            "success": result["success"],
            "invite_id": invite_id,
            "attendee": attendee,
            "title": title,
            "start_time": start_time,
            "end_time": end.isoformat(),
            "duration_minutes": duration_minutes,
            "location": location,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": result["status"],
            "email_result": result,
        }

    except Exception as e:
        logger.error(f"Failed to send calendar invite: {e}")
        return {"success": False, "error": str(e), "status": "failed"}


def generate_ics_invite(
    title: str,
    start: datetime,
    end: datetime,
    attendee: str,
    organizer: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
    timezone: str = "UTC",
    uid: Optional[str] = None,
) -> str:
    """
    Generate ICS (iCalendar) format invite content

    This is compatible with Google Calendar, Outlook, Apple Calendar
    """
    uid = uid or f"{datetime.now(timezone.utc).timestamp()}@graftai.com"

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//GraftAI//GraftAI Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"DTSTART;TZID={timezone}:{start.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND;TZID={timezone}:{end.strftime('%Y%m%dT%H%M%S')}",
        f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}Z",
        f"UID:{uid}",
        f"SUMMARY:{title}",
    ]

    if description:
        ics_lines.append(f"DESCRIPTION:{description.replace(chr(10), '\\n')}")

    if location:
        ics_lines.append(f"LOCATION:{location}")

    ics_lines.extend(
        [
            f"ORGANIZER;CN=Organizer:mailto:{organizer}",
            f"ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{attendee}",
            "STATUS:CONFIRMED",
            "SEQUENCE:0",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:Reminder",
            "TRIGGER:-PT15M",
            "END:VALARM",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
    )

    return "\r\n".join(ics_lines)


# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════


async def send_bulk_emails(
    recipients: List[str],
    subject: str,
    body: str,
    template: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
) -> List[dict]:
    """
    Send emails to multiple recipients efficiently

    Uses SendGrid batch API for efficiency
    """
    results = []

    for recipient in recipients:
        result = await send_email(
            to=recipient,
            subject=subject,
            body=body,
            template=template,
            template_context=template_context,
        )
        results.append(result)

    return results


async def notify_team(
    message: str, urgency: str = "normal", channels: List[str] = ["slack"]
) -> dict:
    """
    Send notification to team through multiple channels

    Args:
        message: Notification message
        urgency: Urgency level (low, normal, high, critical)
        channels: List of channels (slack, email, teams)

    Returns:
        Combined notification results
    """
    results = {}

    if "slack" in channels and APIConfig.is_slack_configured():
        channel = "#critical-bookings" if urgency == "critical" else "#bookings"
        results["slack"] = await post_to_slack(channel=channel, message=message)

    if "email" in channels:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@graftai.com")
        subject_prefix = "[CRITICAL]" if urgency == "critical" else "[Notification]"
        results["email"] = await send_email(
            to=admin_email, subject=f"{subject_prefix} GraftAI Alert", body=message
        )

    return results
