"""Email template rendering and delivery service.

This module provides functionality for:
- Loading and rendering email templates
- Variable substitution
- HTML to text conversion
- Integration with email providers

Example Usage:
    service = EmailTemplateService()

    # Render a template
    html, text = service.render_template(
        template_slug="booking_confirmation",
        user_id="user_123",
        variables={
            "user_name": "John Doe",
            "booking_title": "Team Standup",
            "booking_time": "2024-01-15 10:00 AM"
        }
    )

    # Send email
    await service.send_email(
        to_email="john@example.com",
        subject="Booking Confirmed",
        html_body=html,
        text_body=text
    )
"""
import html
import logging
import os
import re
from datetime import UTC, datetime
import bleach

from jinja2 import BaseLoader, Environment, TemplateError
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.email_template import EmailLog, EmailTemplate
from backend.services.mail_service import send_email as smtp_send_email

logger = logging.getLogger(__name__)

class EmailTemplateService:
    """Service for managing and rendering email templates."""
    DEFAULT_TEMPLATES = {"booking_confirmation": {"name": "Booking Confirmation", "subject": "Your booking is confirmed: {{booking_title}}", "html_body": '\n<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{{subject}}</title>\n    <style>\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }\n        .header { background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }\n        .header h1 { color: white; margin: 0; font-size: 24px; }\n        .content { background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }\n        .booking-details { background: #f9fafb; padding: 20px; border-radius: 6px; margin: 20px 0; }\n        .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }\n        .detail-row:last-child { border-bottom: none; }\n        .button { display: inline-block; background: {{primary_color}}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }\n        .footer { text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }\n    </style>\n</head>\n<body>\n    <div class="header">\n        <h1>✓ Booking Confirmed</h1>\n    </div>\n    <div class="content">\n        <p>Hi {{user_name}},</p>\n        <p>Your booking has been confirmed. Here are the details:</p>\n\n        <div class="booking-details">\n            <div class="detail-row">\n                <strong>Event:</strong>\n                <span>{{booking_title}}</span>\n            </div>\n            <div class="detail-row">\n                <strong>Date & Time:</strong>\n                <span>{{booking_time}}</span>\n            </div>\n            <div class="detail-row">\n                <strong>Duration:</strong>\n                <span>{{booking_duration}} minutes</span>\n            </div>\n            <div class="detail-row">\n                <strong>Location:</strong>\n                <span>{{booking_location}}</span>\n            </div>\n            <div class="detail-row">\n                <strong>Attendee:</strong>\n                <span>{{attendee_name}} ({{attendee_email}})</span>\n            </div>\n        </div>\n\n        <p style="text-align: center;">\n            <a href="{{calendar_link}}" class="button">Add to Calendar</a>\n        </p>\n\n        <div class="footer">\n            <p>Powered by GraftAI · <a href="{{app_url}}">Manage your bookings</a></p>\n            <p>If you didn\'t make this booking, please <a href="{{support_url}}">contact support</a>.</p>\n        </div>\n    </div>\n</body>\n</html>\n            ', "available_variables": ["user_name", "booking_title", "booking_time", "booking_duration", "booking_location", "attendee_name", "attendee_email", "calendar_link", "app_url", "support_url", "primary_color", "secondary_color"]}, "booking_reminder": {"name": "Booking Reminder", "subject": "Reminder: {{booking_title}} in {{time_until}}", "html_body": '\n<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>{{subject}}</title>\n    <style>\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }\n        .reminder-box { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; border-radius: 4px; }\n        .button { display: inline-block; background: {{primary_color}}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }\n    </style>\n</head>\n<body>\n    <h2>⏰ Upcoming Booking Reminder</h2>\n    <div class="reminder-box">\n        <p><strong>{{booking_title}}</strong></p>\n        <p>Starting in {{time_until}} at {{booking_time}}</p>\n    </div>\n    <p>Hi {{user_name}},</p>\n    <p>This is a friendly reminder about your upcoming booking.</p>\n    <p style="text-align: center;">\n        <a href="{{meeting_link}}" class="button">Join Meeting</a>\n    </p>\n</body>\n</html>\n            ', "available_variables": ["user_name", "booking_title", "booking_time", "time_until", "meeting_link", "primary_color"]}, "booking_cancelled": {"name": "Booking Cancelled", "subject": "Booking cancelled: {{booking_title}}", "html_body": '\n<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>{{subject}}</title>\n    <style>\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }\n        .cancelled-box { background: #fee2e2; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; border-radius: 4px; }\n    </style>\n</head>\n<body>\n    <h2>❌ Booking Cancelled</h2>\n    <div class="cancelled-box">\n        <p><strong>{{booking_title}}</strong></p>\n        <p>Scheduled for: {{booking_time}}</p>\n        <p>Cancelled by: {{cancelled_by}}</p>\n        {% if cancellation_reason %}\n        <p>Reason: {{cancellation_reason}}</p>\n        {% endif %}\n    </div>\n    <p>Hi {{user_name}},</p>\n    <p>A booking has been cancelled. The time slot is now available again.</p>\n    <p><a href="{{reschedule_url}}">Reschedule</a> | <a href="{{app_url}}">View all bookings</a></p>\n</body>\n</html>\n            ', "available_variables": ["user_name", "booking_title", "booking_time", "cancelled_by", "cancellation_reason", "reschedule_url", "app_url"]}, "welcome_email": {"name": "Welcome Email", "subject": "Welcome to GraftAI, {{user_name}}!", "html_body": '\n<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>{{subject}}</title>\n    <style>\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }\n        .hero { background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%); padding: 40px; text-align: center; border-radius: 8px; color: white; }\n        .feature { padding: 15px; margin: 10px 0; background: #f9fafb; border-radius: 6px; }\n        .button { display: inline-block; background: white; color: {{primary_color}}; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; }\n    </style>\n</head>\n<body>\n    <div class="hero">\n        <h1>🎉 Welcome to GraftAI!</h1>\n        <p>Smart scheduling powered by AI</p>\n        <a href="{{dashboard_url}}" class="button">Get Started</a>\n    </div>\n    <div style="padding: 30px 0;">\n        <p>Hi {{user_name}},</p>\n        <p>Thank you for joining GraftAI! Here\'s what you can do:</p>\n\n        <div class="feature">\n            <strong>📅 Create Booking Links</strong>\n            <p>Share your availability with a simple link</p>\n        </div>\n        <div class="feature">\n            <strong>🤖 AI Scheduling</strong>\n            <p>Let AI find the best times for your meetings</p>\n        </div>\n        <div class="feature">\n            <strong>🔗 Calendar Sync</strong>\n            <p>Connect Google, Outlook, and Apple calendars</p>\n        </div>\n\n        <p style="text-align: center;">\n            <a href="{{getting_started_url}}" style="color: {{primary_color}};">View Getting Started Guide →</a>\n        </p>\n    </div>\n</body>\n</html>\n            ', "available_variables": ["user_name", "dashboard_url", "getting_started_url", "primary_color", "secondary_color"]}, "payment_received": {"name": "Payment Received", "subject": "Payment received: ${{amount}}", "html_body": '\n<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>{{subject}}</title>\n    <style>\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }\n        .receipt { background: #f0fdf4; border: 1px solid #86efac; padding: 20px; border-radius: 8px; margin: 20px 0; }\n    </style>\n</head>\n<body>\n    <h2>💳 Payment Confirmed</h2>\n    <p>Hi {{user_name}},</p>\n    <p>Thank you for your payment. Here\'s your receipt:</p>\n\n    <div class="receipt">\n        <p><strong>Amount:</strong> ${{amount}} {{currency}}</p>\n        <p><strong>Date:</strong> {{payment_date}}</p>\n        <p><strong>Plan:</strong> {{plan_name}}</p>\n        <p><strong>Transaction ID:</strong> {{transaction_id}}</p>\n    </div>\n\n    <p><a href="{{billing_url}}">View billing history →</a></p>\n</body>\n</html>\n            ', "available_variables": ["user_name", "amount", "currency", "payment_date", "plan_name", "transaction_id", "billing_url"]}}

    def __init__(self, db: AsyncSession):
        """Initialize the email template service.

        Args:
            db: SQLAlchemy async session for database operations
        """
        self.db = db
        # Enable autoescaping for HTML templates to prevent XSS when rendering
        self.jinja_env = Environment(loader=BaseLoader(), autoescape=True)

    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """Sanitize HTML content submitted by users.

        Uses `bleach` to allow a conservative set of tags and attributes suitable
        for HTML email templates. This helps prevent stored XSS and removes
        potentially dangerous content before saving to the database.
        """
        allowed_tags = [
            "a",
            "b",
            "strong",
            "i",
            "em",
            "u",
            "p",
            "br",
            "div",
            "span",
            "ul",
            "ol",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "img",
            "table",
            "thead",
            "tbody",
            "tr",
            "td",
            "th",
        ]
        allowed_attrs = {
            "a": ["href", "title", "rel", "target"],
            "img": ["src", "alt", "title", "width", "height"],
            "div": ["style"],
            "span": ["style"],
            "p": ["style"],
        }
        cleaned = bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        return cleaned

    async def initialize_system_templates(self) -> None:
        """Create default system templates if they don't exist."""
        for slug, template_data in self.DEFAULT_TEMPLATES.items():
            stmt = select(EmailTemplate).where(and_(EmailTemplate.slug == slug, EmailTemplate.is_system))
            existing = (await self.db.execute(stmt)).scalars().first()
            if not existing:
                template = EmailTemplate(name=template_data["name"], slug=slug, description=f"System template for {template_data['name']}", is_system=True, user_id=None, subject=template_data["subject"], html_body=template_data["html_body"], text_body=self._html_to_text(template_data["html_body"]), available_variables=template_data["available_variables"], primary_color="#6366f1")
                self.db.add(template)
        await self.db.commit()

    async def get_template(self, slug: str, user_id: str | None=None, language: str="en") -> EmailTemplate | None:
        """Get a template by slug.

        First tries to find a user-specific template, then falls back to system template.

        Args:
            slug: Template identifier (e.g., "booking_confirmation")
            user_id: Optional user ID for user-specific templates
            language: Language code (default: "en")

        Returns:
            EmailTemplate instance or None
        """
        if user_id:
            stmt = select(EmailTemplate).where(and_(EmailTemplate.slug == slug, EmailTemplate.user_id == user_id, EmailTemplate.language == language, EmailTemplate.is_active))
            template = (await self.db.execute(stmt)).scalars().first()
            if template:
                return template
        stmt = select(EmailTemplate).where(and_(EmailTemplate.slug == slug, EmailTemplate.is_system, EmailTemplate.language == language, EmailTemplate.is_active))
        return (await self.db.execute(stmt)).scalars().first()

    def render_template(self, template: EmailTemplate, variables: dict[str, str]) -> tuple[str, str, str]:
        """Render a template with variables.

        Args:
            template: EmailTemplate instance
            variables: Dictionary of variables for substitution

        Returns:
            Tuple of (subject, html_body, text_body)

        Raises:
            TemplateError: If template rendering fails
        """
        default_vars = {"primary_color": template.primary_color, "secondary_color": "#ec4899", "app_url": "https://graftai.com", "support_url": "https://graftai.com/support", **variables}
        try:
            subject_template = self.jinja_env.from_string(template.subject)
            subject = subject_template.render(**default_vars)
            html_template = self.jinja_env.from_string(template.html_body)
            html_body = html_template.render(**default_vars)
            text_template = self.jinja_env.from_string(template.text_body)
            text_body = text_template.render(**default_vars)
            return (subject, html_body, text_body)
        except TemplateError as e:
            msg = f"Failed to render template {template.slug}: {e}"
            raise TemplateError(msg)

    @staticmethod
    def _html_to_text(html_content: str) -> str:
        """Convert HTML to plain text.

        Simple conversion that removes tags and converts
        common elements to text equivalents.

        Args:
            html_content: HTML string

        Returns:
            Plain text version
        """
        text = re.sub("<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL)
        text = re.sub("<h[1-6][^>]*>", "\n\n", text)
        text = re.sub("</h[1-6]>", "\n", text)
        text = re.sub("<p[^>]*>", "\n", text)
        text = re.sub("</p>", "\n", text)
        text = re.sub("<br[^>]*>", "\n", text)
        text = re.sub("<div[^>]*>", "\n", text)
        text = re.sub("</div>", "\n", text)
        text = re.sub('<a[^>]+href="([^"]*)"[^>]*>([^<]*)</a>', "\\2 (\\1)", text)
        text = re.sub("<[^>]+>", "", text)
        text = html.unescape(text)
        text = re.sub("\\n\\s*\\n", "\n\n", text)
        text = re.sub("^[\\s\\n]+", "", text)
        return text.strip()

    async def send_email(self, to_email: str, subject: str, html_body: str, text_body: str, template_id: str | None=None, user_id: str | None=None, cc_emails: list[str] | None=None, bcc_emails: list[str] | None=None) -> EmailLog:
        """Send an email and log the delivery.

        This is a placeholder implementation. In production, this would
        integrate with an email provider like Resend, SendGrid, or AWS SES.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content
            template_id: Optional template ID for tracking
            user_id: Optional user ID for tracking
            cc_emails: Optional CC recipients
            bcc_emails: Optional BCC recipients

        Returns:
            EmailLog instance
        """
        log = EmailLog(template_id=template_id, user_id=user_id or "system", to_email=to_email, cc_emails=cc_emails, bcc_emails=bcc_emails, subject=subject, status="sent", provider="resend", email_metadata={"html_length": len(html_body), "text_length": len(text_body)})
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        resend_api_key = os.getenv("RESEND_API_KEY")
        resend_error: str | None = None
        if resend_api_key:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {resend_api_key}"}, json={"from": "GraftAI <noreply@graftai.tech>", "to": [to_email] + (cc_emails or []), "bcc": bcc_emails or [], "subject": subject, "html": html_body, "text": text_body})
                    if response.status_code in (200, 201):
                        result = response.json()
                        log.provider_message_id = result.get("id")
                        log.status = "sent"
                    else:
                        log.status = "failed"
                        resend_error = f"Resend API error: {response.status_code}"
                        log.error_message = resend_error
                        logger.error("Failed to send email: %s", response.text)
            except Exception as e:
                log.status = "failed"
                resend_error = str(e)
                log.error_message = resend_error
                logger.exception("Failed to send email: %s", e)
        else:
            log.status = "failed"
            resend_error = "RESEND_API_KEY not configured"
            log.error_message = resend_error
        if log.status != "sent":
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            if smtp_user and smtp_password:
                try:
                    await smtp_send_email(to_email, subject, html_body, text_body)
                    log.provider = "smtp"
                    log.status = "sent"
                    if resend_error:
                        log.error_message = f"Primary provider failed: {resend_error}. Delivered via SMTP fallback."
                except Exception as smtp_exc:
                    log.status = "failed"
                    log.error_message = f"SMTP fallback failed: {smtp_exc}"
                    logger.exception("SMTP fallback failed: %s", smtp_exc)
            elif resend_error:
                logger.warning("Email delivery failed without SMTP fallback: %s", resend_error)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_email_stats(self, user_id: str, days: int=30) -> dict:
        """Get email sending statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            Dictionary with email statistics
        """
        from datetime import timedelta
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = select(EmailLog).where(and_(EmailLog.user_id == user_id, EmailLog.sent_at >= since))
        logs = (await self.db.execute(stmt)).scalars().all()
        stats = {"total": len(logs), "sent": len([log_item for log_item in logs if log_item.status == "sent"]), "delivered": len([log_item for log_item in logs if log_item.status == "delivered"]), "opened": len([log_item for log_item in logs if log_item.opened_at]), "failed": len([log_item for log_item in logs if log_item.status == "failed"]), "open_rate": 0, "period_days": days}
        if stats["delivered"] > 0:
            stats["open_rate"] = round(stats["opened"] / stats["delivered"] * 100, 2)
        return stats
