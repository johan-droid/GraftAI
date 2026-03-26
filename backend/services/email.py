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
from typing import Optional


def _get_smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", "no-reply@example.com")),
        "from_name": os.getenv("SMTP_FROM_NAME", "GraftAI"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
    }


def _build_message(
    to_email: str, subject: str, html_body: str, text_body: Optional[str] = None
) -> EmailMessage:
    msg = EmailMessage()
    cfg = _get_smtp_config()
    from_header = f"{cfg['from_name']} <{cfg['from_email']}>"
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Subject"] = subject
    if text_body:
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
    else:
        # Use HTML as both for clients that support it and fallback
        msg.set_content("", subtype="plain")
        msg.add_alternative(html_body, subtype="html")

    return msg


def _send_via_smtp(msg: EmailMessage) -> None:
    cfg = _get_smtp_config()

    if cfg["use_tls"]:
        # Start TLS connection
        with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            if cfg["user"] and cfg["password"]:
                server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
    else:
        # SSL direct
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as server:
            if cfg["user"] and cfg["password"]:
                server.login(cfg["user"], cfg["password"])
            server.send_message(msg)


async def send_email(
    to_email: str, subject: str, html_body: str, text_body: Optional[str] = None
) -> None:
    """Send an email asynchronously.

    This function delegates the blocking SMTP interaction to a thread
    using `asyncio.to_thread` to avoid adding a dependency on an async
    SMTP library.
    """
    msg = _build_message(to_email, subject, html_body, text_body)
    await asyncio.to_thread(_send_via_smtp, msg)


__all__ = ["send_email"]
