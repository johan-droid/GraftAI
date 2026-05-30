"""
Security middleware for GraftAI backend.
Provides security headers, request validation, and input sanitization.
"""
import re
import time
from collections.abc import Callable
from typing import ClassVar

import os

import bleach
from fastapi import HTTPException, Request, Response, status
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all HTTP responses.
    Protects against XSS, clickjacking, MIME sniffing, and other common attacks.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()"
        if os.getenv("ENV", "development").lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate and sanitize incoming requests.
    Prevents injection attacks and ensures data integrity.
    """
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_CONTENT_TYPES: ClassVar[set[str]] = {"application/json", "application/x-www-form-urlencoded", "multipart/form-data", "text/plain"}
    SQL_INJECTION_PATTERNS: ClassVar[list[str]] = ["(\\%27)|(\\')|(\\-\\-)|(\\%23)|(#)", "((\\%3D)|(=))[^\\n]*((\\%27)|(\\')|(\\-\\-)|(\\%3B)|(;))", "\\w*((\\%27)|(\\'))((\\%6F)|o|(\\%4F))((\\%72)|r|(\\%52))", "((\\%27)|(\\'))union", "exec(\\s|\\+)+(s|x)p\\w+", "UNION\\s+SELECT", "INSERT\\s+INTO", "DELETE\\s+FROM", "DROP\\s+TABLE"]
    XSS_PATTERNS: ClassVar[list[str]] = ["<script[^>]*>[\\s\\S]*?</script>", "javascript:", "on\\w+\\s*=", "<iframe", "<object", "<embed"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.MAX_CONTENT_LENGTH:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Request too large. Maximum size: {self.MAX_CONTENT_LENGTH} bytes")
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Content-Length header") from exc
        content_type = request.headers.get("content-type", "").lower()
        if content_type:
            main_type = content_type.split(";")[0].strip()
            if main_type and main_type not in self.ALLOWED_CONTENT_TYPES:
                if not any(ct in main_type for ct in ["json", "form-data", "urlencoded"]):
                    raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Content-Type '{content_type}' not supported")
        return await call_next(request)

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string value to prevent XSS."""
        if not isinstance(value, str):
            return value
        cleaned = bleach.clean(value, tags=[], strip=True)
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
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

    def __init__(self, app, allowed_origins: list | None=None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []
        env = os.getenv("ENV", "development").lower()
        if env == "production":
            cors_origins = os.getenv("CORS_ORIGINS", "")
            self.allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        if origin and self.allowed_origins:
            if origin not in self.allowed_origins:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed")
        response = await call_next(request)
        if origin and (not self.allowed_origins or origin in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "86400"
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests for security audit trail.
    Captures request metadata without sensitive data.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from backend.utils.logger import get_logger
        logger = get_logger(__name__)
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")
        logger.info("Request started: %s %s | IP: %s | UA: %s", method, path, client_ip, user_agent)
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            logger.info("Request completed: %s %s | Status: %s | Duration: %ss", method, path, response.status_code, duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Request failed: %s %s | Error: %s | Duration: %ss", method, path, e, duration, exc_info=True)
            return JSONResponse(status_code=500, content={"error": "Internal Server Error", "message": str(e), "code": "middleware_error", "path": path})

class TrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Validate that requests come from trusted hosts.
    Prevents DNS rebinding and host header attacks.
    """

    def __init__(self, app, allowed_hosts: list | None=None):
        super().__init__(app)
        trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
        self.allowed_hosts = allowed_hosts or [host.strip() for host in trusted_hosts.split(",") if host.strip()]
        self.allowed_patterns = []
        for host in self.allowed_hosts:
            if host.startswith("*."):
                pattern = host.replace("*.", "^.+\\.")
                self.allowed_patterns.append(re.compile(pattern + "$"))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        host = request.headers.get("host", "").split(":")[0]
        is_allowed = False
        if host in self.allowed_hosts:
            is_allowed = True
        for pattern in self.allowed_patterns:
            if pattern.match(host):
                is_allowed = True
                break
        if os.getenv("ENV", "development").lower() == "development":
            if host in ["localhost", "127.0.0.1"]:
                is_allowed = True
        if not is_allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Host header")
        return await call_next(request)

def get_security_middleware() -> list:
    """
    Get list of security middleware to add to FastAPI app.
    Order matters - process in reverse order (last added runs first).
    """
    return [Middleware(SecurityHeadersMiddleware), Middleware(InputValidationMiddleware), Middleware(RequestLoggingMiddleware), Middleware(CORSHardeningMiddleware), Middleware(TrustedHostMiddleware)]
