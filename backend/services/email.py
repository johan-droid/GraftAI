"""Email sending helper using Gmail/SMTP for notifications.

Provides an async-friendly `send_email` wrapper that uses the standard
library `smtplib` executed in a thread to avoid adding extra runtime
dependencies.

Environment variables used (add to backend/.env or .env.example):
- SMTP_HOST (e.g. smtp.gmail.com)
- SMTP_PORT (e.g. 587)
- SMTP_USER (SMTP username / Gmail address)
- SMTP_PASSWORD (SMTP app password or account password)
- SMTP_FROM_EMAIL (optional override for From header)
- SMTP_FROM_NAME (optional display name)
- SMTP_USE_TLS (true/false, default true)
- EMAIL_PROVIDER (smtp/sendgrid, default is automatically sendgrid when SENDGRID_API_KEY is set)
- SENDGRID_API_KEY (required when EMAIL_PROVIDER=sendgrid)
- SENDGRID_ALLOW_SMTP_FALLBACK (true/false, default false)
"""

import os
import asyncio
import smtplib
import ssl
import logging
from email.message import EmailMessage
from pathlib import Path
from typing import Optional, Any
import httpx
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Initialize logger
logger = logging.getLogger(__name__)


class SendGridDeliveryError(RuntimeError):
    """Raised when SendGrid rejects a delivery request."""

    def __init__(self, status_code: int, response_text: str):
        super().__init__(f"SendGrid API error {status_code}: {response_text}")
        self.status_code = status_code
        self.response_text = response_text

# Ensure .env from project root is loaded (backend/.env)

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / '.env')

# Initialize Jinja2 Environment
# Hardened: Use absolute directory resolution for production stability
template_dir = (project_root / "templates" / "email").resolve()
if not template_dir.exists():
    logger.warning(f"⚠️ Email template directory not found at {template_dir}. Sending will fail.")

jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 email template found in backend/templates/email/."""
    # Ensure frontend_url is available to all templates for logo/dashboard links
    if "frontend_url" not in context:
        context["frontend_url"] = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def _get_smtp_config() -> dict:
    configured_provider = os.getenv("EMAIL_PROVIDER")
    if configured_provider:
        provider = configured_provider.lower()
    else:
        provider = "sendgrid" if os.getenv("SENDGRID_API_KEY") else "smtp"

    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", "no-reply@example.com")),
        "from_name": os.getenv("SMTP_FROM_NAME", "GraftAI"),
        "sendgrid_from_email": os.getenv("SENDGRID_FROM_EMAIL"),
        "sendgrid_from_name": os.getenv("SENDGRID_FROM_NAME", os.getenv("SMTP_FROM_NAME", "GraftAI")),
        "sendgrid_allow_smtp_fallback": os.getenv("SENDGRID_ALLOW_SMTP_FALLBACK", "false").lower() in ("1", "true", "yes"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
        "provider": provider,
    }


def _build_message(
    to_email: str, subject: str, html_body: str, text_body: Optional[str] = None
) -> EmailMessage:
    msg = EmailMessage()
    cfg = _get_smtp_config()

    # Gmail requires the from address to match authenticated user or be authorized.
    # Use SMTP_USER when provided for compatibility with many providers.
    from_email = cfg.get("user") or cfg.get("from_email") or "no-reply@example.com"
    cfg["from_email"] = from_email

    from_header = f"{cfg['from_name']} <{from_email}>"
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Subject"] = subject
    if text_body:
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
    else:
        msg.set_content("", subtype="plain")
        msg.add_alternative(html_body, subtype="html")

    return msg


def _send_via_smtp(msg: EmailMessage) -> None:
    cfg = _get_smtp_config()
    try:
        timeout = 15 # 15 seconds for Render network constraints
        if cfg["use_tls"]:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=timeout) as server:
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        logger.error(f"❌ [SMTP ERROR] Failed to connect to {cfg['host']}:{cfg['port']} - {type(e).__name__}: {e}")
        # Re-raise so the background task knows it failed
        raise


def _send_via_sendgrid(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str],
    from_email: str,
    from_name: str,
) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY is required for SendGrid provider")

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": from_name},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body or ""},
            {"type": "text/html", "value": html_body},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = httpx.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers, timeout=10)
    if response.status_code not in (200, 202):
        raise SendGridDeliveryError(response.status_code, response.text)


def _send_email_provider(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    if not to_email or not isinstance(to_email, str) or not to_email.strip():
        raise ValueError("Recipient email address is required")
    cfg = _get_smtp_config()
    provider = cfg.get("provider", "smtp")
    from_email = cfg.get("from_email") or cfg.get("user") or "no-reply@example.com"
    from_name = cfg.get("from_name", "GraftAI")
    allow_smtp_fallback = cfg.get("sendgrid_allow_smtp_fallback", False)

    if provider == "sendgrid":
        sendgrid_from_email = cfg.get("sendgrid_from_email") or from_email
        sendgrid_from_name = cfg.get("sendgrid_from_name") or from_name

        try:
            _send_via_sendgrid(to_email, subject, html_body, text_body, sendgrid_from_email, sendgrid_from_name)
            return
        except SendGridDeliveryError as e:
            # 4xx are generally configuration/content issues; SMTP fallback won't fix those.
            if 400 <= e.status_code < 500:
                logger.error(f"SendGrid delivery rejected ({e.status_code}); skipping SMTP fallback: {e.response_text}")
                raise

            if not allow_smtp_fallback:
                logger.error(f"SendGrid delivery failed ({e.status_code}) and SMTP fallback is disabled")
                raise

            logger.warning(f"SendGrid delivery failed ({e.status_code}), falling back to SMTP")
        except Exception as e:
            if not allow_smtp_fallback:
                logger.error(f"SendGrid delivery failed and SMTP fallback is disabled: {e}")
                raise
            logger.warning(f"SendGrid delivery failed, falling back to SMTP: {e}")

    # Default: SMTP (or fallback path)
    msg = _build_message(to_email, subject, html_body, text_body)
    _send_via_smtp(msg)


async def send_email(
    to_email: str, subject: str, html_body: str, text_body: Optional[str] = None
) -> None:
    """Send an email asynchronously with provider fallback."""
    await asyncio.to_thread(_send_email_provider, to_email, subject, html_body, text_body)


def verify_smtp_config() -> dict[str, Any]:
    """
    Diagnostic tool to verify SMTP connectivity and credentials.
    Returns a dict with 'status', 'error', and 'details'.
    """
    cfg = _get_smtp_config()
    try:
        timeout = 10
        if cfg["use_tls"]:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
        else:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=timeout) as server:
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
        
        return {
            "status": "success",
            "message": f"Successfully connected to {cfg['host']}:{cfg['port']}",
            "config_preview": {
                "host": cfg["host"],
                "port": cfg["port"],
                "user": cfg["user"],
                "use_tls": cfg["use_tls"]
            }
        }
    except Exception as e:
        message = str(e)
        hint = "Check SMTP_USER and SMTP_PASSWORD. For Gmail, use an App Password." if "Authentication" in message or "login" in message.lower() else "Check host/port and firewall settings."
        if "Network is unreachable" in message or "network is unreachable" in message.lower():
            hint = (
                "Outbound SMTP appears blocked. On Render, direct SMTP may be restricted. "
                "Use EMAIL_PROVIDER=sendgrid with SENDGRID_API_KEY or another HTTP-based email service."
            )
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": message,
            "hint": hint,
        }


__all__ = ["send_email", "verify_smtp_config"]
