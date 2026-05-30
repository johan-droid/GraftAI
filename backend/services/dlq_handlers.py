"""
Dead Letter Queue Handlers Registration.
Registers all action handlers for DLQ retry processing.
"""
import asyncio
from typing import Any

from backend.utils.circuit_breaker import (
    GOOGLE_CALENDAR_BREAKER,
    SENDGRID_BREAKER,
    SLACK_BREAKER,
    TWILIO_BREAKER,
)
from backend.utils.dead_letter_queue import get_dlq
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def _mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "<unknown>"
    local, domain = email.split("@", 1)
    local = "**" if len(local) <= 2 else local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{local}@{domain}"

def _mask_phone(phone: str) -> str:
    if not phone:
        return "<unknown>"
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) <= 4:
        return "****"
    return f"****{digits[-4:]}"

def _validate_webhook_url(url: str, allow_localhost: bool=False) -> bool:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "http"}:
            return False
        if not parsed.netloc:
            return False
        host = parsed.hostname or ""
        if parsed.scheme == "http" and (not allow_localhost):
            return False
        if allow_localhost and host in {"localhost", "127.0.0.1", "::1"}:
            return True
        return bool(host)
    except Exception:
        return False

def _validate_teams_webhook_url(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return False
        host = parsed.hostname or ""
        return host.endswith(("office.com", "microsoft.com"))
    except Exception:
        return False
try:
    from backend.ai.tools.communication_tools_real import (
        post_to_slack as real_send_slack,
    )
    from backend.ai.tools.communication_tools_real import send_email as real_send_email
    from backend.ai.tools.communication_tools_real import send_sms as real_send_sms
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    logger.warning("Communication tools not available, DLQ handlers will use mock implementations")

async def handle_send_email(payload: dict[str, Any]) -> dict[str, Any]:
    """
    DLQ handler for sending emails.

    Args:
        payload: Email payload with 'to', 'subject', 'body', 'html'

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    try:
        to = payload.get("to")
        subject = payload.get("subject")
        body = payload.get("body") or payload.get("html")
        cc = payload.get("cc")
        bcc = payload.get("bcc")
        template = payload.get("template")
        template_context = payload.get("template_context")
        from_address = payload.get("from_address")
        attachments = payload.get("attachments")
        if not all([to, subject, body]):
            return {"success": False, "error": "Missing required fields: to, subject, body/html"}
        if TOOLS_AVAILABLE:

            @SENDGRID_BREAKER
            async def _send():
                return await real_send_email(to=to, subject=subject, body=body, cc=cc, bcc=bcc, template=template, template_context=template_context, from_address=from_address, attachments=attachments)
            result = await _send()
            return {"success": bool(result.get("success")), "message_id": result.get("email_id"), "result": result}
        logger.info("[DLQ MOCK] Would send email to %s: subject=%s", _mask_email(to), subject)
        await asyncio.sleep(0.1)
        return {"success": True, "mock": True}
    except Exception as e:
        logger.exception("[DLQ] Email handler failed: %s", e)
        return {"success": False, "error": str(e)}

async def handle_send_sms(payload: dict[str, Any]) -> dict[str, Any]:
    """
    DLQ handler for sending SMS.

    Args:
        payload: SMS payload with 'to', 'body'

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    try:
        to = payload.get("to")
        body = payload.get("body")
        from_number = payload.get("from_number")
        media_urls = payload.get("media_urls")
        if not all([to, body]):
            return {"success": False, "error": "Missing required fields: to, body"}
        if TOOLS_AVAILABLE:

            @TWILIO_BREAKER
            async def _send():
                return await real_send_sms(to=to, message=body, from_number=from_number, media_urls=media_urls)
            result = await _send()
            return {"success": bool(result.get("success")), "message_sid": result.get("sms_id"), "result": result}
        logger.info("[DLQ MOCK] Would send SMS to %s: %s", _mask_phone(to), (body or "")[:50])
        await asyncio.sleep(0.1)
        return {"success": True, "mock": True}
    except Exception as e:
        logger.exception("[DLQ] SMS handler failed: %s", e)
        return {"success": False, "error": str(e)}

async def handle_slack_notification(payload: dict[str, Any]) -> dict[str, Any]:
    """
    DLQ handler for Slack notifications.

    Args:
        payload: Slack payload with 'channel', 'message', 'blocks'

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    try:
        channel = payload.get("channel")
        message = payload.get("message")
        blocks = payload.get("blocks")
        if not channel:
            return {"success": False, "error": "Missing required field: channel"}
        if TOOLS_AVAILABLE:

            @SLACK_BREAKER
            async def _send():
                return await real_send_slack(channel=channel, text=message, blocks=blocks)
            result = await _send()
            return {"success": True, "ts": result.get("ts")}
        logger.info("[DLQ MOCK] Would send Slack to %s: %s", channel, message)
        await asyncio.sleep(0.1)
        return {"success": True, "mock": True}
    except Exception as e:
        logger.exception("[DLQ] Slack handler failed: %s", e)
        return {"success": False, "error": str(e)}

async def handle_webhook_delivery(payload: dict[str, Any]) -> dict[str, Any]:
    """
    DLQ handler for webhook delivery.

    Args:
        payload: Webhook payload with 'url', 'method', 'headers', 'body'

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    try:
        import aiohttp
        url = payload.get("url")
        method = payload.get("method", "POST")
        headers = payload.get("headers", {})
        body = payload.get("body")
        if not url:
            return {"success": False, "error": "Missing required field: url"}
        if not _validate_webhook_url(url, allow_localhost=True):
            return {"success": False, "error": "Invalid webhook URL. Only https URLs or localhost are allowed."}
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method=method, url=url, headers=headers, json=body if isinstance(body, dict) else None, data=body if isinstance(body, str) else None) as response:
                if response.status < 400:
                    return {"success": True, "status_code": response.status}
                return {"success": False, "error": f"HTTP {response.status}", "status_code": response.status}
    except Exception as e:
        logger.exception("[DLQ] Webhook handler failed: %s", e)
        return {"success": False, "error": str(e)}

async def handle_calendar_sync(payload: dict[str, Any]) -> dict[str, Any]:
    """
    DLQ handler for calendar synchronization.

    Args:
        payload: Calendar payload with 'event_id', 'action', 'details'

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    try:
        action = payload.get("action")
        event_id = payload.get("event_id")
        calendar_id = payload.get("calendar_id", "primary")
        if not action or (action != "create" and (not event_id)):
            return {"success": False, "error": "Missing required fields: action and event_id for update/delete"}
        if TOOLS_AVAILABLE:

            @GOOGLE_CALENDAR_BREAKER
            async def _sync():
                from backend.ai.tools.scheduling_tools_real import sync_calendar_event
                return await sync_calendar_event(action=action, event_id=event_id, calendar_id=calendar_id, details=payload.get("details", {}))
            result = await _sync()
            success = bool(result.get("success"))
            response = {"success": success, "result": result}
            if result.get("event_id"):
                response["calendar_event_id"] = result.get("event_id")
            if not success:
                response["error"] = result.get("error")
            return response
        logger.info("[DLQ MOCK] Would sync calendar: %s %s", action, event_id)
        await asyncio.sleep(0.1)
        return {"success": True, "mock": True}
    except Exception as e:
        logger.exception("[DLQ] Calendar handler failed: %s", e)
        return {"success": False, "error": str(e)}

async def handle_teams_notification(payload: dict[str, Any]) -> dict[str, Any]:
    """
    DLQ handler for Microsoft Teams notifications.

    Args:
        payload: Teams payload with 'webhook_url', 'title', 'text', 'sections'

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    try:
        import aiohttp
        webhook_url = payload.get("webhook_url")
        title = payload.get("title", "GraftAI Notification")
        text = payload.get("text", "")
        if not webhook_url:
            return {"success": False, "error": "Missing required field: webhook_url"}
        if not _validate_teams_webhook_url(webhook_url):
            return {"success": False, "error": "Invalid Microsoft Teams webhook URL"}
        from urllib.parse import urlparse
        parsed_url = urlparse(webhook_url)
        logger.info("[DLQ] Teams webhook host validated: %s", parsed_url.hostname)
        message_card = {"@type": "MessageCard", "@context": "https://schema.org/extensions", "themeColor": "0078D7", "summary": title, "sections": [{"activityTitle": title, "activitySubtitle": "GraftAI", "text": text}]}
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(webhook_url, json=message_card, headers={"Content-Type": "application/json"}) as response:
                if response.status < 400:
                    return {"success": True}
                return {"success": False, "error": f"HTTP {response.status}"}
    except Exception as e:
        logger.exception("[DLQ] Teams handler failed: %s", e)
        return {"success": False, "error": str(e)}

def register_dlq_handlers():
    """
    Register all DLQ handlers.
    Call this function during application startup.
    """
    dlq = get_dlq()
    handlers = {"send_email": handle_send_email, "send_sms": handle_send_sms, "slack_notification": handle_slack_notification, "webhook_delivery": handle_webhook_delivery, "calendar_sync": handle_calendar_sync, "teams_notification": handle_teams_notification}
    for action_type, handler in handlers.items():
        dlq.register_handler(action_type, handler)
        logger.info("[DLQ] Registered handler for action: %s", action_type)
    logger.info("[DLQ] Total handlers registered: %s", len(handlers))
    return len(handlers)

async def process_dlq_batch(limit: int=50) -> dict[str, int]:
    """
    Process a batch of DLQ items.

    Args:
        limit: Maximum number of items to process

    Returns:
        Statistics dict with counts
    """
    dlq = get_dlq()
    stats = await dlq.process_queue(limit=limit)
    logger.info("[DLQ] Batch processed: %s items, %s succeeded, %s failed, %s errors", stats["processed"], stats["succeeded"], stats["failed"], stats["errors"])
    return stats
__all__ = ["handle_calendar_sync", "handle_send_email", "handle_send_sms", "handle_slack_notification", "handle_teams_notification", "handle_webhook_delivery", "process_dlq_batch", "register_dlq_handlers"]
