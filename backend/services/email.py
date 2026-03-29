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
"""

from __future__ import annotations

import os
import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

# Ensure .env from project root is loaded (backend/.env)
project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / '.env', override=True)


def _get_smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", "no-reply@example.com")),
        "from_name": os.getenv("SMTP_FROM_NAME", "GraftAI"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
        "provider": os.getenv("EMAIL_PROVIDER", "smtp").lower(),
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

    if cfg["use_tls"]:
        with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            if cfg["user"] and cfg["password"]:
                server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
    else:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as server:
            if cfg["user"] and cfg["password"]:
                server.login(cfg["user"], cfg["password"])
            server.send_message(msg)


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
        raise RuntimeError(
            f"SendGrid API error {response.status_code}: {response.text}"
        )


def _send_email_provider(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    cfg = _get_smtp_config()
    provider = cfg.get("provider", "smtp")
    from_email = cfg.get("from_email")
    from_name = cfg.get("from_name")

    if provider == "sendgrid":
        try:
            _send_via_sendgrid(to_email, subject, html_body, text_body, from_email, from_name)
            return
        except Exception as e:
            # fallback to SMTP if sendgrid fails
            print(f"SendGrid delivery failed, falling back to SMTP: {e}")

    # Default: SMTP (or fallback path)
    msg = _build_message(to_email, subject, html_body, text_body)
    _send_via_smtp(msg)


async def send_email(
    to_email: str, subject: str, html_body: str, text_body: Optional[str] = None
) -> None:
    """Send an email asynchronously with provider fallback."""
    await asyncio.to_thread(_send_email_provider, to_email, subject, html_body, text_body)


__all__ = ["send_email"]
