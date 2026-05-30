"""Wrapper for unified.to shortlink API with a safe fallback.

This module attempts to create a shortlink via unified.to API if an API key
is configured. If the external API is unavailable or not configured, it will
return a simple internally-constructed fallback URL (non-persistent) so callers
can proceed in dev environments. For production, you should store the
unified.to API key in secrets and handle persistence/analytics via the provider.
"""
import logging
import secrets

import httpx

logger = logging.getLogger(__name__)

class UnifiedService:
    API_ENDPOINT = "https://api.unified.to/v1/links"

    def __init__(self, api_key: str | None=None):
        self.api_key = api_key

    async def create_shortlink(self, target_url: str, title: str | None=None) -> dict:
        """Create a shortlink for the given target URL.

        Returns a dict: {"short_url": str, "id": str, "external": bool}
        """
        if not self.api_key:
            fallback_id = secrets.token_urlsafe(6)
            short = f"/s/{fallback_id}"
            logger.info("unified.to API key not configured, returning fallback shortlink")
            return {"short_url": short, "id": fallback_id, "external": False}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"target": target_url}
        if title:
            payload["title"] = title
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.API_ENDPOINT, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return {"short_url": data.get("short_url") or data.get("url"), "id": data.get("id"), "external": True}
        except Exception as exc:
            logger.warning("unified.to request failed: %s", exc)
            fallback_id = secrets.token_urlsafe(6)
            short = f"/s/{fallback_id}"
            return {"short_url": short, "id": fallback_id, "external": False}
