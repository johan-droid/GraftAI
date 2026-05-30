"""
CSRF protection utilities for GraftAI backend.
Implements double-submit cookie pattern for CSRF protection.
"""
import logging
import secrets

from fastapi import HTTPException, Request, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class CSRFProtection:
    """CSRF protection using double-submit cookie pattern."""

    def __init__(self, cookie_name: str="csrf_token", header_name: str="X-CSRF-Token"):
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
        response.set_cookie(key=self.cookie_name, value=token, max_age=3600, httponly=True, samesite="strict", secure=True)

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for FastAPI."""

    def __init__(self, app, csrf: CSRFProtection | None=None, exclude_methods: list | None=None):
        super().__init__(app)
        self.csrf = csrf or CSRFProtection()
        self.exclude_methods = exclude_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]

    async def dispatch(self, request: Request, call_next):
        if request.method in self.exclude_methods:
            return await call_next(request)
        if request.url.path.startswith("/api/v1/auth/") or request.url.path.startswith("/api/v1/webhooks/") or request.headers.get("Authorization"):
            return await call_next(request)
        if not self.csrf.validate_token(request):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token validation failed")
        response = await call_next(request)
        if not request.cookies.get(self.csrf.cookie_name):
            token = self.csrf.generate_token()
            self.csrf.set_cookie(response, token)
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
