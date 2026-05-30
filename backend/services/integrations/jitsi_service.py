"""Lightweight Jitsi meeting helper (public meet.jit.si and optional self-host JWT support).

This module provides a minimal interface for creating Jitsi join URLs.
For public usage (meet.jit.si) we simply generate a deterministic room name.
For self-hosted deployments requiring JWT, provide `jwt_secret` in config and
the code will attach a placeholder token generation hook (caller must implement
proper JWT claims according to their Jitsi installation).
"""
import secrets
from datetime import datetime


class JitsiService:

    def __init__(self, db=None):
        self.db = db

    async def create_meeting(self, topic: str, start_time: datetime | None=None, duration_minutes: int=30, booking_id: str | None=None, config: dict | None=None) -> dict:
        """Create a lightweight Jitsi meeting descriptor.

        Returns a dict with `join_url`, `room_name`, and `metadata`.
        This does not contact an external API when using meet.jit.si.
        """
        base = (booking_id or secrets.token_urlsafe(8)).replace("/", "-")
        room_name = f"graftai-{base}"
        domain = "meet.jit.si"
        if config and config.get("domain"):
            domain = config.get("domain")
        join_url = f"https://{domain}/{room_name}"
        metadata = {"provider": "jitsi", "room_name": room_name, "domain": domain, "topic": topic, "start_time": start_time.isoformat() if start_time else None, "duration_minutes": duration_minutes}
        if config and config.get("jwt_secret"):
            metadata["jwt_hint"] = "self-hosted-jwt-configured"
        return {"join_url": join_url, "host_url": None, "password": None, "metadata": metadata}
