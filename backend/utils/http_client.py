"""Shared httpx AsyncClient helper and lightweight proxy.

Provides a single long-lived AsyncClient to reuse connections and a
ClientProxy that exposes `get/post/patch/delete` helpers while
preserving a context-manager interface (no-op for the shared client).
"""
import logging
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

_client: Optional[httpx.AsyncClient] = None


def _default_timeout() -> httpx.Timeout:
    return httpx.Timeout(10.0, connect=5.0)


def _default_limits() -> httpx.Limits:
    return httpx.Limits(max_keepalive_connections=20, max_connections=100)


async def get_client() -> httpx.AsyncClient:
    """Return a shared AsyncClient instance (create lazily)."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=_default_timeout(), limits=_default_limits())
        logger.info("Initialized shared httpx.AsyncClient singleton")
    return _client


class ClientProxy:
    """Lightweight proxy that uses the shared AsyncClient for requests.

    Keeps a small per-service config (base_url + headers). It implements
    ``get/post/patch/delete`` and an async context manager so existing
    code using ``async with`` keeps working (no-op exit).
    """

    def __init__(self, base_url: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.headers = headers or {}

    async def request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> httpx.Response:
        client = await get_client()
        merged = dict(self.headers)
        if headers:
            merged.update(headers)

        # Respect absolute urls; otherwise join with base_url if provided
        if self.base_url and not url.startswith("http://") and not url.startswith("https://"):
            target = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        else:
            target = url

        return await client.request(method, target, headers=merged, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", url, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Intentionally do not close the shared AsyncClient here
        return False


async def aclose() -> None:
    """Close the shared AsyncClient. Useful for graceful shutdown in tests.

    Note: calling this during runtime will force recreation of the client on
    the next request via ``get_client()``.
    """
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception as e:
            logger.warning("Error closing shared http client: %s", e)
        _client = None
