"""Gmail SMTP email service for GraftAI notifications.

Uses the standard library `smtplib` with TLS, executed in a thread pool via
`asyncio.to_thread` so it never blocks the async event loop.

Required environment variables (set in backend/.env or Render dashboard):
    SMTP_HOST        Gmail SMTP host (default: smtp.gmail.com)
    SMTP_PORT        Gmail SMTP port (default: 587)
    SMTP_USER        Your Gmail address, e.g. noreply@gmail.com
    SMTP_PASSWORD    Gmail App Password (NOT your account password)
                     → Generate at: https://myaccount.google.com/apppasswords
    SMTP_FROM_EMAIL  Display from address (optional, defaults to SMTP_USER)
    SMTP_FROM_NAME   Display name (optional, default: GraftAI)

Gmail setup notes:
    1. Enable 2-Step Verification on the Google account.
    2. Create an App Password (Google Account → Security → App Passwords).
    3. Set SMTP_PASSWORD to that 16-character token.
"""

import os
import asyncio
import smtplib
import ssl
import logging
from email.message import EmailMessage
from pathlib import Path
from typing import Optional, Any

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# ── Environment ──────────────────────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

# ── Jinja2 template environment ───────────────────────────────────────────────
template_dir = (project_root / "templates" / "email").resolve()
if not template_dir.exists():
    logger.warning(f"⚠️ Email template directory not found at {template_dir}.")

jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 HTML email template from backend/templates/email/."""
    if "frontend_url" not in context:
        context["frontend_url"] = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    template = jinja_env.get_template(template_name)
    return template.render(**context)


# ── Config helpers ────────────────────────────────────────────────────────────

def _get_smtp_config() -> dict:
    """Read SMTP config from environment variables."""
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL") or os.getenv("SMTP_USER") or "no-reply@gmail.com",
        "from_name": os.getenv("SMTP_FROM_NAME", "GraftAI"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
    }


def _log_smtp_config_once() -> None:
    """Log the effective SMTP config at startup — helps catch misconfigs early."""
    cfg = _get_smtp_config()
    if not cfg["user"] or not cfg["password"]:
        logger.warning(
            "⚠️ [EMAIL] SMTP_USER or SMTP_PASSWORD is not set. "
            "Emails will fail. Set SMTP_USER to your Gmail address and "
            "SMTP_PASSWORD to a Gmail App Password."
        )
    else:
        logger.info(
            f"✅ [EMAIL] Gmail SMTP configured — "
            f"from: {cfg['from_email']} via {cfg['host']}:{cfg['port']}"
        )


_log_smtp_config_once()


# ── Core send helpers ─────────────────────────────────────────────────────────

def _build_message(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> EmailMessage:
    cfg = _get_smtp_config()
    msg = EmailMessage()
    msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    # Set plain-text first, then add HTML as alternative
    msg.set_content(text_body or "")
    msg.add_alternative(html_body, subtype="html")
    return msg


import resend

def _send_email_sync(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    """Validate inputs then build and dispatch the email using Resend (if configured) or SMTP."""
    if not to_email or not isinstance(to_email, str) or not to_email.strip():
        raise ValueError("Recipient email address is required")
        
    cfg = _get_smtp_config()
    
    # Primary/Fallback: Try Resend first if API key is present
    resend_api_key = os.getenv("RESEND_API_KEY")
    if resend_api_key:
        try:
            resend.api_key = resend_api_key
            response = resend.Emails.send({
                "from": f"{cfg['from_name']} <{cfg['from_email']}>",
                "to": to_email,
                "subject": subject,
                "html": html_body,
                "text": text_body or ""
            })
            logger.info(f"📧 Email sent via Resend → {to_email} | ID: {response.get('id')}")
            return
        except Exception as e:
            logger.warning(f"⚠️ [RESEND] Failed to send via Resend, falling back to SMTP: {e}")
            # Fall through to SMTP

    msg = _build_message(to_email, subject, html_body, text_body)

    host, port = cfg["host"], cfg["port"]
    timeout = 15  # seconds

    # Attempt primary SMTP port
    try:
        if cfg["use_tls"]:
            with smtplib.SMTP(host, port, timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(host, port, timeout=timeout) as server:
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
                server.send_message(msg)

        logger.info(f"📧 Email sent via SMTP → {msg['To']} | port: {port}")

    except (OSError, smtplib.SMTPException) as e:
        # Fallback to port 465 (SMTP_SSL) if port 587 / STARTTLS is blocked
        if port != 465:
            logger.warning(f"⚠️ [SMTP] Primary port {port} failed ({e}). Falling back to port 465 (SSL)...")
            try:
                with smtplib.SMTP_SSL(host, 465, timeout=timeout) as server:
                    if cfg["user"] and cfg["password"]:
                        server.login(cfg["user"], cfg["password"])
                    server.send_message(msg)
                logger.info(f"📧 Email sent via SMTP (Fallback Port 465) → {msg['To']}")
                return
            except Exception as fallback_e:
                logger.error(f"❌ [SMTP] Fallback to port 465 also failed: {fallback_e}")
                raise fallback_e
        else:
            logger.error(f"❌ [SMTP] Failed to send to {msg['To']}: {e}")
            raise e


# ── Public async interface ────────────────────────────────────────────────────

async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    """
    Send an email asynchronously via Gmail SMTP.
    Runs the blocking smtplib call in a thread pool to avoid blocking the
    async event loop.
    """
    await asyncio.to_thread(_send_email_sync, to_email, subject, html_body, text_body)


# ── Diagnostics ───────────────────────────────────────────────────────────────

def verify_smtp_config() -> dict[str, Any]:
    """
    Test SMTP connectivity and authentication — used by the admin diagnostic API.
    Returns a dict with 'status', 'message', and 'config_preview'.
    """
    cfg = _get_smtp_config()
    host, port = cfg["host"], cfg["port"]

    try:
        if cfg["use_tls"]:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
        else:
            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])

        return {
            "status": "success",
            "message": f"Connected to {host}:{port} and authenticated as {cfg['user']}",
            "config_preview": {
                "host": host,
                "port": port,
                "user": cfg["user"],
                "from_email": cfg["from_email"],
                "from_name": cfg["from_name"],
                "use_tls": cfg["use_tls"],
            },
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "error_type": "SMTPAuthenticationError",
            "message": f"Authentication failed for {cfg['user']}",
            "hint": (
                "Make sure SMTP_PASSWORD is a Gmail App Password (not your account password). "
                "Generate one at https://myaccount.google.com/apppasswords"
            ),
        }
    except Exception as e:
        msg = str(e)
        hint = "Check SMTP_HOST, SMTP_PORT, and firewall settings."
        if "unreachable" in msg.lower() or "refused" in msg.lower():
            hint = (
                "Outbound SMTP appears blocked. "
                "On Render, ensure outbound port 587 is not restricted."
            )
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": msg,
            "hint": hint,
        }


__all__ = ["send_email", "render_template", "verify_smtp_config"]
