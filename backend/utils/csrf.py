"""
CSRF protection utilities for GraftAI backend.

Auth cookies are SameSite=None (the frontend and API are served from different
sites), so browsers attach them to cross-site requests. Origin/Referer is the
only value an attacker's page cannot forge, so the middleware requires it to
match a trusted origin for every state-changing request.
"""

import logging
import re
import secrets
from urllib.parse import urlsplit

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF protection using double-submit cookie pattern."""

    def __init__(
        self, cookie_name: str = "csrf_token", header_name: str = "X-CSRF-Token"
    ):
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.token_length = 32

    def generate_token(self) -> str:
        """Generate a secure CSRF token."""
        return secrets.token_urlsafe(self.token_length)

    def validate_token(self, request: Request) -> bool:
        """
        Validate CSRF token from request.

        Args:
            request: FastAPI request object

        Returns:
            bool: True if token is valid, False otherwise
        """
        header_token = request.headers.get(self.header_name)
        if not header_token:
            logger.warning("CSRF token missing from header")
            return False
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            logger.warning("CSRF token missing from cookie")
            return False
        is_valid = secrets.compare_digest(header_token, cookie_token)
        if not is_valid:
            logger.warning("CSRF token mismatch")
        return is_valid

    def set_cookie(self, response: Response, token: str) -> None:
        """
        Set CSRF token in cookie.

        Args:
            response: FastAPI response object
            token: CSRF token to set
        """
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=3600,
            httponly=True,
            samesite="strict",
            secure=True,
        )


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject state-changing requests whose Origin/Referer is not a trusted origin."""

    def __init__(
        self,
        app,
        csrf: CSRFProtection | None = None,
        exclude_methods: list | None = None,
        allowed_origins: list | None = None,
        allowed_origin_regex: str | None = None,
        exempt_paths: tuple = (),
    ):
        super().__init__(app)
        self.csrf = csrf or CSRFProtection()
        self.exclude_methods = exclude_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]
        self.allowed_origins = {
            origin.rstrip("/") for origin in (allowed_origins or [])
        }
        self.allowed_origin_regex = (
            re.compile(allowed_origin_regex) if allowed_origin_regex else None
        )
        self.exempt_paths = exempt_paths

    def _is_trusted(self, origin: str) -> bool:
        candidate = origin.rstrip("/")
        if candidate in self.allowed_origins:
            return True
        return bool(
            self.allowed_origin_regex and self.allowed_origin_regex.match(candidate)
        )

    def _request_origin(self, request: Request) -> str | None:
        origin = request.headers.get("origin")
        if origin:
            return origin
        referer = request.headers.get("referer")
        if not referer:
            return None
        parsed = urlsplit(referer)
        return (
            f"{parsed.scheme}://{parsed.netloc}"
            if parsed.scheme and parsed.netloc
            else None
        )

    async def dispatch(self, request: Request, call_next):
        if request.method in self.exclude_methods or request.url.path.startswith(
            self.exempt_paths
        ):
            return await call_next(request)
        origin = self._request_origin(request)
        if origin is None:
            # Not a browser request (server-to-server, CLI, mobile) — there is no
            # ambient credential riding along, so there is nothing for CSRF to abuse.
            return await call_next(request)
        if not self._is_trusted(origin):
            logger.warning(
                "CSRF rejected: untrusted origin %s for %s", origin, request.url.path
            )
            return JSONResponse(
                {"detail": "CSRF origin not allowed."},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        response = await call_next(request)
        if not request.cookies.get(self.csrf.cookie_name):
            self.csrf.set_cookie(response, self.csrf.generate_token())
        return response


def get_csrf_token(request: Request) -> str:
    """
    Get CSRF token from request cookies.

    Args:
        request: FastAPI request object

    Returns:
        str: CSRF token or empty string if not found
    """
    csrf = CSRFProtection()
    return request.cookies.get(csrf.cookie_name, "")


def generate_csrf_token() -> str:
    """
    Generate a new CSRF token.

    Returns:
        str: New CSRF token
    """
    csrf = CSRFProtection()
    return csrf.generate_token()
