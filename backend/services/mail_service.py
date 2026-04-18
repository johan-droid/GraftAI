import os
import asyncio
import smtplib
import ssl
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


def _get_smtp_config():
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "pass": os.getenv("SMTP_PASSWORD", ""),
        "from": os.getenv("SMTP_FROM_EMAIL")
        or os.getenv("SMTP_USER", "no-reply@graftai.tech"),
    }


def _send_sync(
    to_email: str, subject: str, html_content: str, text_body: str | None = None
):
    cfg = _get_smtp_config()
    if not cfg["user"] or not cfg["pass"]:
        logger.error("SMTP credentials missing.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from"]
    msg["To"] = to_email
    msg.set_content(
        text_body or "Please use an HTML-capable mail client to view this message."
    )
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(cfg["user"], cfg["pass"])
            server.send_message(msg)
            logger.info(f"📧 Sent email to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")


async def send_email(
    to_email: str, subject: str, html_body: str, text_body: str = None
):
    """Async wrapper for the blocking SMTP call."""
    await asyncio.to_thread(_send_sync, to_email, subject, html_body, text_body)


from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

# Setup Jinja2
project_root = Path(__file__).resolve().parents[1]
template_dir = (project_root / "templates" / "email").resolve()
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str, context: dict) -> str:
    """Render a Jinja2 HTML email template from backend/templates/email/."""
    if "frontend_url" not in context:
        context["frontend_url"] = os.getenv(
            "FRONTEND_BASE_URL", "http://localhost:3000"
        )
    try:
        template = jinja_env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Template rendering failed for {template_name}: {e}")
        return f"<html><body>{str(context)}</body></html>"
