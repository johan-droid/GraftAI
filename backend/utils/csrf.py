"""
CSRF protection utilities for GraftAI backend.
Implements double-submit cookie pattern for CSRF protection.
"""

import secrets
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF protection using double-submit cookie pattern."""
    
    def __init__(self, cookie_name: str = "csrf_token", header_name: str = "X-CSRF-Token"):
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
        # Get token from header
        header_token = request.headers.get(self.header_name)
        if not header_token:
            logger.warning("CSRF token missing from header")
            return False
        
        # Get token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            logger.warning("CSRF token missing from cookie")
            return False
        
        # Compare tokens
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
            max_age=3600,  # 1 hour
            httponly=True,
            samesite="strict",
            secure=True,  # Only in production
        )


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for FastAPI."""
    
    def __init__(self, app, csrf: Optional[CSRFProtection] = None, exclude_methods: Optional[list] = None):
        super().__init__(app)
        self.csrf = csrf or CSRFProtection()
        self.exclude_methods = exclude_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods
        if request.method in self.exclude_methods:
            response = await call_next(request)
            return response
        
        # Skip CSRF for API endpoints that use JWT auth
        if request.url.path.startswith("/api/v1/auth/") or \
           request.url.path.startswith("/api/v1/webhooks/") or \
           request.headers.get("Authorization"):
            response = await call_next(request)
            return response
        
        # Validate CSRF token
        if not self.csrf.validate_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token validation failed"
            )
        
        # Process request
        response = await call_next(request)
        
        # Set new CSRF token if needed
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
