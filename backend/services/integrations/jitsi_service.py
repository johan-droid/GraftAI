"""Lightweight Jitsi meeting helper (public meet.jit.si and optional self-host JWT support).

This module provides a minimal interface for creating Jitsi join URLs.
For public usage (meet.jit.si) we simply generate a deterministic room name.
For self-hosted deployments requiring JWT, provide `jwt_secret` in config and
the code will attach a placeholder token generation hook (caller must implement
proper JWT claims according to their Jitsi installation).
"""
from datetime import datetime, timezone
import secrets
from typing import Optional, Dict


class JitsiService:
    def __init__(self, db=None):
        # db is optional; kept for parity with other services
        self.db = db

    async def create_meeting(
        self,
        topic: str,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 30,
        booking_id: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> Dict:
        """Create a lightweight Jitsi meeting descriptor.

        Returns a dict with `join_url`, `room_name`, and `metadata`.
        This does not contact an external API when using meet.jit.si.
        """
        # Room name: prefer booking_id for traceability, else random
        base = (booking_id or secrets.token_urlsafe(8)).replace("/", "-")
        room_name = f"graftai-{base}"

        # If the caller provided a domain (self-hosted), use it; otherwise use public
        domain = "meet.jit.si"
        if config and config.get("domain"):
            domain = config.get("domain")

        join_url = f"https://{domain}/{room_name}"

        metadata = {
            "provider": "jitsi",
            "room_name": room_name,
            "domain": domain,
            "topic": topic,
            "start_time": start_time.isoformat() if start_time else None,
            "duration_minutes": duration_minutes,
        }

        # If self-hosted JWT secret present, add placeholder token (implementation-specific)
        if config and config.get("jwt_secret"):
            # Real JWT creation should be done following Jitsi's expected claims.
            metadata["jwt_hint"] = "self-hosted-jwt-configured"

        return {"join_url": join_url, "host_url": None, "password": None, "metadata": metadata}
