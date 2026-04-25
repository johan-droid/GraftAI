"""
Security middleware for GraftAI backend.
Provides security headers, request validation, and input sanitization.
"""

import re
from typing import Optional, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
import bleach
import time
import logging


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all HTTP responses.
    Protects against XSS, clickjacking, MIME sniffing, and other common attacks.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )

        # Strict Transport Security (HTTPS only)
        # Only in production
        import os

        if os.getenv("ENV", "development").lower() == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate and sanitize incoming requests.
    Prevents injection attacks and ensures data integrity.
    """

    # Maximum request size (10MB)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    # Allowed content types
    ALLOWED_CONTENT_TYPES = {
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain",
    }

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
        r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
        r"((\%27)|(\'))union",
        r"exec(\s|\+)+(s|x)p\w+",
        r"UNION\s+SELECT",
        r"INSERT\s+INTO",
        r"DELETE\s+FROM",
        r"DROP\s+TABLE",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>[\s\S]*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.MAX_CONTENT_LENGTH:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request too large. Maximum size: {self.MAX_CONTENT_LENGTH} bytes",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Length header",
                )

        # Validate content type
        content_type = request.headers.get("content-type", "").lower()
        if content_type:
            # Extract main content type (ignore charset)
            main_type = content_type.split(";")[0].strip()
            if main_type and main_type not in self.ALLOWED_CONTENT_TYPES:
                if not any(
                    ct in main_type for ct in ["json", "form-data", "urlencoded"]
                ):
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Content-Type '{content_type}' not supported",
                    )

        # Continue processing
        response = await call_next(request)
        return response

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string value to prevent XSS."""
        if not isinstance(value, str):
            return value

        # Remove HTML tags
        cleaned = bleach.clean(value, tags=[], strip=True)

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                # Remove potentially dangerous content
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        return cleaned

    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check if value contains SQL injection patterns."""
        if not isinstance(value, str):
            return False

        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False


class CORSHardeningMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with stricter security.
    Prevents unauthorized cross-origin requests.
    """

    def __init__(self, app, allowed_origins: Optional[list] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []

        # In production, validate against whitelist
        import os

        env = os.getenv("ENV", "development").lower()
        if env == "production":
            cors_origins = os.getenv("CORS_ORIGINS", "")
            self.allowed_origins = [
                origin.strip() for origin in cors_origins.split(",") if origin.strip()
            ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")

        # Check if origin is allowed
        if origin and self.allowed_origins:
            if origin not in self.allowed_origins:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed"
                )

        response = await call_next(request)

        # Add CORS headers only for allowed origins
        if origin and (not self.allowed_origins or origin in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "86400"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests for security audit trail.
    Captures request metadata without sensitive data.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import time
        from backend.utils.logger import get_logger

        logger = get_logger(__name__)
        start_time = time.time()

        # Log request
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")

        logger.info(
            f"Request started: {method} {path} | IP: {client_ip} | UA: {user_agent}"
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {method} {path} | "
                f"Status: {response.status_code} | Duration: {duration:.3f}s"
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {method} {path} | "
                f"Error: {str(e)} | Duration: {duration:.3f}s",
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(e),
                    "code": "middleware_error",
                    "path": path
                }
            )


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Validate that requests come from trusted hosts.
    Prevents DNS rebinding and host header attacks.
    """

    def __init__(self, app, allowed_hosts: Optional[list] = None):
        super().__init__(app)
        import os

        # Get allowed hosts from environment
        trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
        self.allowed_hosts = allowed_hosts or [
            host.strip() for host in trusted_hosts.split(",") if host.strip()
        ]

        # Support wildcards
        self.allowed_patterns = []
        for host in self.allowed_hosts:
            if host.startswith("*."):
                # Convert *.example.com to regex pattern
                pattern = host.replace("*.", "^.+\\.")
                self.allowed_patterns.append(re.compile(pattern + "$"))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        host = request.headers.get("host", "").split(":")[0]  # Remove port

        # Check if host is allowed
        is_allowed = False

        # Exact match
        if host in self.allowed_hosts:
            is_allowed = True

        # Pattern match
        for pattern in self.allowed_patterns:
            if pattern.match(host):
                is_allowed = True
                break

        # localhost is always allowed in development
        import os

        if os.getenv("ENV", "development").lower() == "development":
            if host in ["localhost", "127.0.0.1"]:
                is_allowed = True

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Host header"
            )

        return await call_next(request)


def get_security_middleware() -> list:
    """
    Get list of security middleware to add to FastAPI app.
    Order matters - process in reverse order (last added runs first).
    """
    return [
        Middleware(SecurityHeadersMiddleware),
        Middleware(InputValidationMiddleware),
        Middleware(RequestLoggingMiddleware),
        Middleware(CORSHardeningMiddleware),
        Middleware(TrustedHostMiddleware),
    ]
