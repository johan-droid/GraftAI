"""Webhook service for third-party integrations (Zapier, Slack, Teams)."""

import json
import hmac
import hashlib
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import httpx
from enum import Enum


class WebhookEventType(str, Enum):
    """Types of events that can trigger webhooks."""
    BOOKING_CREATED = "booking.created"
    BOOKING_UPDATED = "booking.updated"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_COMPLETED = "booking.completed"
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    TEAM_MEMBER_JOINED = "team.member_joined"
    TEAM_MEMBER_LEFT = "team.member_left"


class WebhookProvider(str, Enum):
    """Supported webhook providers."""
    ZAPIER = "zapier"
    SLACK = "slack"
    TEAMS = "teams"
    CUSTOM = "custom"


class WebhookPayload:
    """Builder for webhook payloads."""
    
    def __init__(self, event_type: WebhookEventType, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def build(self) -> Dict[str, Any]:
        return {
            "event": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data
        }


class WebhookService:
    """Service for sending webhooks to third-party integrations."""
    
    def __init__(self, signing_secret: Optional[str] = None):
        self.signing_secret = signing_secret
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for webhook payload."""
        if not self.signing_secret:
            return ""
        
        signature = hmac.new(
            self.signing_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        provider: WebhookProvider = WebhookProvider.CUSTOM,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send a webhook to a URL."""
        
        # Build request headers
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "GraftAI-Webhook/1.0",
            "X-GraftAI-Event": payload.get("event", "unknown"),
            "X-GraftAI-Timestamp": payload.get("timestamp", ""),
        }
        
        # Add provider-specific headers
        if provider == WebhookProvider.SLACK:
            request_headers["Content-Type"] = "application/json"
        
        # Generate signature
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = self._generate_signature(payload_str)
        if signature:
            request_headers["X-GraftAI-Signature"] = signature
        
        # Merge custom headers
        if headers:
            request_headers.update(headers)
        
        try:
            response = await self.client.post(
                url,
                content=payload_str,
                headers=request_headers
            )
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response_body": response.text if response.status_code >= 400 else None
            }
        except httpx.TimeoutException:
            return {"success": False, "error": "Timeout", "status_code": None}
        except httpx.RequestError as e:
            return {"success": False, "error": str(e), "status_code": None}
    
    async def send_batch(
        self,
        webhooks: List[Dict[str, Any]],
        payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Send webhooks to multiple endpoints concurrently."""
        tasks = [
            self.send_webhook(
                url=wh["url"],
                payload=payload,
                provider=WebhookProvider(wh.get("provider", "custom")),
                headers=wh.get("headers")
            )
            for wh in webhooks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            {"url": webhooks[i]["url"], **(result if isinstance(result, dict) else {"error": str(result)})}
            for i, result in enumerate(results)
        ]
    
    def build_booking_payload(self, booking: Any, event_type: WebhookEventType) -> Dict[str, Any]:
        """Build payload for booking events."""
        return WebhookPayload(
            event_type=event_type,
            data={
                "booking_id": getattr(booking, 'id', None),
                "title": getattr(booking, 'title', None),
                "description": getattr(booking, 'description', None),
                "start_time": getattr(booking, 'start_time', None),
                "end_time": getattr(booking, 'end_time', None),
                "status": getattr(booking, 'status', None),
                "attendee_name": getattr(booking, 'attendee_name', None),
                "attendee_email": getattr(booking, 'attendee_email', None),
                "location": getattr(booking, 'location', None),
                "meeting_link": getattr(booking, 'meeting_link', None),
                "confirmation_code": getattr(booking, 'confirmation_code', None),
            }
        ).build()
    
    def build_user_payload(self, user: Any, event_type: WebhookEventType) -> Dict[str, Any]:
        """Build payload for user events."""
        return WebhookPayload(
            event_type=event_type,
            data={
                "user_id": getattr(user, 'id', None),
                "email": getattr(user, 'email', None),
                "full_name": getattr(user, 'full_name', None),
                "tier": getattr(user, 'tier', None),
                "timezone": getattr(user, 'timezone', None),
            }
        ).build()
    
    def build_payment_payload(
        self,
        user_id: str,
        amount: float,
        currency: str,
        status: str,
        event_type: WebhookEventType
    ) -> Dict[str, Any]:
        """Build payload for payment events."""
        return WebhookPayload(
            event_type=event_type,
            data={
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ).build()
    
    def build_team_payload(
        self,
        team: Any,
        user: Any,
        event_type: WebhookEventType
    ) -> Dict[str, Any]:
        """Build payload for team events."""
        return WebhookPayload(
            event_type=event_type,
            data={
                "team_id": getattr(team, 'id', None),
                "team_name": getattr(team, 'name', None),
                "user_id": getattr(user, 'id', None),
                "user_email": getattr(user, 'email', None),
                "user_name": getattr(user, 'full_name', None),
            }
        ).build()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Specific provider formatters

class SlackWebhookFormatter:
    """Format webhooks for Slack compatibility."""
    
    @staticmethod
    def format_booking(booking: Any, event_type: WebhookEventType) -> Dict[str, Any]:
        """Format booking event for Slack."""
        action = event_type.value.split('.')[-1].upper()
        color = {
            "created": "#36a64f",
            "updated": "#f2c744",
            "cancelled": "#ff0000",
            "completed": "#36a64f"
        }.get(action.lower(), "#808080")
        
        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"Booking {action}: {booking.title}",
                    "fields": [
                        {"title": "Attendee", "value": booking.attendee_name, "short": True},
                        {"title": "Email", "value": booking.attendee_email, "short": True},
                        {"title": "Time", "value": str(booking.start_time), "short": True},
                        {"title": "Status", "value": booking.status, "short": True},
                    ],
                    "footer": "GraftAI",
                    "ts": int(datetime.now(timezone.utc).timestamp())
                }
            ]
        }


class TeamsWebhookFormatter:
    """Format webhooks for Microsoft Teams compatibility."""
    
    @staticmethod
    def format_booking(booking: Any, event_type: WebhookEventType) -> Dict[str, Any]:
        """Format booking event for Teams."""
        action = event_type.value.split('.')[-1].upper()
        
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": f"Booking {action}",
            "sections": [
                {
                    "activityTitle": f"Booking {action}: {booking.title}",
                    "facts": [
                        {"name": "Attendee:", "value": booking.attendee_name},
                        {"name": "Email:", "value": booking.attendee_email},
                        {"name": "Time:", "value": str(booking.start_time)},
                        {"name": "Status:", "value": booking.status},
                    ]
                }
            ]
        }
