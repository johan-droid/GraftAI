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

import re
import html
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timezone
from jinja2 import Environment, BaseLoader, TemplateError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.email_template import EmailTemplate, EmailLog
from backend.models.tables import UserTable


class EmailTemplateService:
    """Service for managing and rendering email templates."""
    
    # Default system templates
    DEFAULT_TEMPLATES = {
        "booking_confirmation": {
            "name": "Booking Confirmation",
            "subject": "Your booking is confirmed: {{booking_title}}",
            "html_body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject}}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .header h1 { color: white; margin: 0; font-size: 24px; }
        .content { background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }
        .booking-details { background: #f9fafb; padding: 20px; border-radius: 6px; margin: 20px 0; }
        .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }
        .detail-row:last-child { border-bottom: none; }
        .button { display: inline-block; background: {{primary_color}}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }
        .footer { text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>✓ Booking Confirmed</h1>
    </div>
    <div class="content">
        <p>Hi {{user_name}},</p>
        <p>Your booking has been confirmed. Here are the details:</p>
        
        <div class="booking-details">
            <div class="detail-row">
                <strong>Event:</strong>
                <span>{{booking_title}}</span>
            </div>
            <div class="detail-row">
                <strong>Date & Time:</strong>
                <span>{{booking_time}}</span>
            </div>
            <div class="detail-row">
                <strong>Duration:</strong>
                <span>{{booking_duration}} minutes</span>
            </div>
            <div class="detail-row">
                <strong>Location:</strong>
                <span>{{booking_location}}</span>
            </div>
            <div class="detail-row">
                <strong>Attendee:</strong>
                <span>{{attendee_name}} ({{attendee_email}})</span>
            </div>
        </div>
        
        <p style="text-align: center;">
            <a href="{{calendar_link}}" class="button">Add to Calendar</a>
        </p>
        
        <div class="footer">
            <p>Powered by GraftAI · <a href="{{app_url}}">Manage your bookings</a></p>
            <p>If you didn't make this booking, please <a href="{{support_url}}">contact support</a>.</p>
        </div>
    </div>
</body>
</html>
            """,
            "available_variables": [
                "user_name", "booking_title", "booking_time", "booking_duration",
                "booking_location", "attendee_name", "attendee_email",
                "calendar_link", "app_url", "support_url", "primary_color", "secondary_color"
            ]
        },
        "booking_reminder": {
            "name": "Booking Reminder",
            "subject": "Reminder: {{booking_title}} in {{time_until}}",
            "html_body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .reminder-box { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; border-radius: 4px; }
        .button { display: inline-block; background: {{primary_color}}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }
    </style>
</head>
<body>
    <h2>⏰ Upcoming Booking Reminder</h2>
    <div class="reminder-box">
        <p><strong>{{booking_title}}</strong></p>
        <p>Starting in {{time_until}} at {{booking_time}}</p>
    </div>
    <p>Hi {{user_name}},</p>
    <p>This is a friendly reminder about your upcoming booking.</p>
    <p style="text-align: center;">
        <a href="{{meeting_link}}" class="button">Join Meeting</a>
    </p>
</body>
</html>
            """,
            "available_variables": [
                "user_name", "booking_title", "booking_time", "time_until",
                "meeting_link", "primary_color"
            ]
        },
        "booking_cancelled": {
            "name": "Booking Cancelled",
            "subject": "Booking cancelled: {{booking_title}}",
            "html_body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .cancelled-box { background: #fee2e2; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <h2>❌ Booking Cancelled</h2>
    <div class="cancelled-box">
        <p><strong>{{booking_title}}</strong></p>
        <p>Scheduled for: {{booking_time}}</p>
        <p>Cancelled by: {{cancelled_by}}</p>
        {% if cancellation_reason %}
        <p>Reason: {{cancellation_reason}}</p>
        {% endif %}
    </div>
    <p>Hi {{user_name}},</p>
    <p>A booking has been cancelled. The time slot is now available again.</p>
    <p><a href="{{reschedule_url}}">Reschedule</a> | <a href="{{app_url}}">View all bookings</a></p>
</body>
</html>
            """,
            "available_variables": [
                "user_name", "booking_title", "booking_time", "cancelled_by",
                "cancellation_reason", "reschedule_url", "app_url"
            ]
        },
        "welcome_email": {
            "name": "Welcome Email",
            "subject": "Welcome to GraftAI, {{user_name}}!",
            "html_body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .hero { background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%); padding: 40px; text-align: center; border-radius: 8px; color: white; }
        .feature { padding: 15px; margin: 10px 0; background: #f9fafb; border-radius: 6px; }
        .button { display: inline-block; background: white; color: {{primary_color}}; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="hero">
        <h1>🎉 Welcome to GraftAI!</h1>
        <p>Smart scheduling powered by AI</p>
        <a href="{{dashboard_url}}" class="button">Get Started</a>
    </div>
    <div style="padding: 30px 0;">
        <p>Hi {{user_name}},</p>
        <p>Thank you for joining GraftAI! Here's what you can do:</p>
        
        <div class="feature">
            <strong>📅 Create Booking Links</strong>
            <p>Share your availability with a simple link</p>
        </div>
        <div class="feature">
            <strong>🤖 AI Scheduling</strong>
            <p>Let AI find the best times for your meetings</p>
        </div>
        <div class="feature">
            <strong>🔗 Calendar Sync</strong>
            <p>Connect Google, Outlook, and Apple calendars</p>
        </div>
        
        <p style="text-align: center;">
            <a href="{{getting_started_url}}" style="color: {{primary_color}};">View Getting Started Guide →</a>
        </p>
    </div>
</body>
</html>
            """,
            "available_variables": [
                "user_name", "dashboard_url", "getting_started_url",
                "primary_color", "secondary_color"
            ]
        },
        "payment_received": {
            "name": "Payment Received",
            "subject": "Payment received: ${{amount}}",
            "html_body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .receipt { background: #f0fdf4; border: 1px solid #86efac; padding: 20px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <h2>💳 Payment Confirmed</h2>
    <p>Hi {{user_name}},</p>
    <p>Thank you for your payment. Here's your receipt:</p>
    
    <div class="receipt">
        <p><strong>Amount:</strong> ${{amount}} {{currency}}</p>
        <p><strong>Date:</strong> {{payment_date}}</p>
        <p><strong>Plan:</strong> {{plan_name}}</p>
        <p><strong>Transaction ID:</strong> {{transaction_id}}</p>
    </div>
    
    <p><a href="{{billing_url}}">View billing history →</a></p>
</body>
</html>
            """,
            "available_variables": [
                "user_name", "amount", "currency", "payment_date",
                "plan_name", "transaction_id", "billing_url"
            ]
        }
    }
    
    def __init__(self, db: AsyncSession):
        """Initialize the email template service.
        
        Args:
            db: SQLAlchemy async session for database operations
        """
        self.db = db
        self.jinja_env = Environment(loader=BaseLoader())
    
    async def initialize_system_templates(self) -> None:
        """Create default system templates if they don't exist."""
        for slug, template_data in self.DEFAULT_TEMPLATES.items():
            # Check if template exists
            stmt = select(EmailTemplate).where(
                and_(
                    EmailTemplate.slug == slug,
                    EmailTemplate.is_system == True
                )
            )
            existing = (await self.db.execute(stmt)).scalars().first()
            
            if not existing:
                template = EmailTemplate(
                    name=template_data["name"],
                    slug=slug,
                    description=f"System template for {template_data['name']}",
                    is_system=True,
                    user_id=None,
                    subject=template_data["subject"],
                    html_body=template_data["html_body"],
                    text_body=self._html_to_text(template_data["html_body"]),
                    available_variables=template_data["available_variables"],
                    primary_color="#6366f1"
                )
                self.db.add(template)
        
        await self.db.commit()
    
    async def get_template(
        self,
        slug: str,
        user_id: Optional[str] = None,
        language: str = "en"
    ) -> Optional[EmailTemplate]:
        """Get a template by slug.
        
        First tries to find a user-specific template, then falls back to system template.
        
        Args:
            slug: Template identifier (e.g., "booking_confirmation")
            user_id: Optional user ID for user-specific templates
            language: Language code (default: "en")
        
        Returns:
            EmailTemplate instance or None
        """
        # Try user-specific template first
        if user_id:
            stmt = select(EmailTemplate).where(
                and_(
                    EmailTemplate.slug == slug,
                    EmailTemplate.user_id == user_id,
                    EmailTemplate.language == language,
                    EmailTemplate.is_active == True
                )
            )
            template = (await self.db.execute(stmt)).scalars().first()
            if template:
                return template
        
        # Fall back to system template
        stmt = select(EmailTemplate).where(
            and_(
                EmailTemplate.slug == slug,
                EmailTemplate.is_system == True,
                EmailTemplate.language == language,
                EmailTemplate.is_active == True
            )
        )
        return (await self.db.execute(stmt)).scalars().first()
    
    def render_template(
        self,
        template: EmailTemplate,
        variables: Dict[str, str]
    ) -> Tuple[str, str, str]:
        """Render a template with variables.
        
        Args:
            template: EmailTemplate instance
            variables: Dictionary of variables for substitution
        
        Returns:
            Tuple of (subject, html_body, text_body)
        
        Raises:
            TemplateError: If template rendering fails
        """
        # Add default variables
        default_vars = {
            "primary_color": template.primary_color,
            "secondary_color": "#ec4899",  # Default secondary
            "app_url": "https://graftai.com",
            "support_url": "https://graftai.com/support",
            **variables
        }
        
        try:
            # Render subject
            subject_template = self.jinja_env.from_string(template.subject)
            subject = subject_template.render(**default_vars)
            
            # Render HTML
            html_template = self.jinja_env.from_string(template.html_body)
            html_body = html_template.render(**default_vars)
            
            # Render text (use stored text body as base)
            text_template = self.jinja_env.from_string(template.text_body)
            text_body = text_template.render(**default_vars)
            
            return subject, html_body, text_body
            
        except TemplateError as e:
            raise TemplateError(f"Failed to render template {template.slug}: {e}")
    
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
        # Remove style tags and content
        text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Replace common tags with text equivalents
        text = re.sub(r'<h[1-6][^>]*>', '\n\n', text)
        text = re.sub(r'</h[1-6]>', '\n', text)
        text = re.sub(r'<p[^>]*>', '\n', text)
        text = re.sub(r'</p>', '\n', text)
        text = re.sub(r'<br[^>]*>', '\n', text)
        text = re.sub(r'<div[^>]*>', '\n', text)
        text = re.sub(r'</div>', '\n', text)
        
        # Replace links
        text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>([^<]*)</a>', r'\2 (\1)', text)
        
        # Remove remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'^[\s\n]+', '', text)
        
        return text.strip()
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        template_id: Optional[str] = None,
        user_id: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> EmailLog:
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
        # Create log entry
        log = EmailLog(
            template_id=template_id,
            user_id=user_id or "system",
            to_email=to_email,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            subject=subject,
            status="sent",
            provider="resend",
            metadata={
                "html_length": len(html_body),
                "text_length": len(text_body)
            }
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        # Send email via Resend if configured
        import os
        resend_api_key = os.getenv("RESEND_API_KEY")
        if resend_api_key:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {resend_api_key}"},
                        json={
                            "from": "GraftAI <noreply@graftai.tech>",
                            "to": [to_email] + (cc_emails or []),
                            "bcc": bcc_emails or [],
                            "subject": subject,
                            "html": html_body,
                            "text": text_body
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        log.provider_message_id = result.get("id")
                        log.status = "sent"
                    else:
                        log.status = "failed"
                        log.error_message = f"Resend API error: {response.status_code}"
                        logger.error(f"Failed to send email: {response.text}")
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
                logger.error(f"Failed to send email: {e}")
        else:
            logger.warning("RESEND_API_KEY not configured - email logged but not sent")
        
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_email_stats(self, user_id: str, days: int = 30) -> Dict:
        """Get email sending statistics for a user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            Dictionary with email statistics
        """
        from datetime import timedelta
        
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        stmt = select(EmailLog).where(
            and_(
                EmailLog.user_id == user_id,
                EmailLog.sent_at >= since
            )
        )
        logs = (await self.db.execute(stmt)).scalars().all()
        
        stats = {
            "total": len(logs),
            "sent": len([l for l in logs if l.status == "sent"]),
            "delivered": len([l for l in logs if l.status == "delivered"]),
            "opened": len([l for l in logs if l.opened_at]),
            "failed": len([l for l in logs if l.status == "failed"]),
            "open_rate": 0,
            "period_days": days
        }
        
        if stats["delivered"] > 0:
            stats["open_rate"] = round((stats["opened"] / stats["delivered"]) * 100, 2)
        
        return stats
