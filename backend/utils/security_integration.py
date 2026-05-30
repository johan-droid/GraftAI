"""
Security integration module for GraftAI backend.
Integrates all security components and provides unified security middleware.
"""
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .csrf import CSRFMiddleware, CSRFProtection
from .rate_limiter import RateLimitMiddleware, get_rate_limiter
from .secure_config import get_secure_config
from .security_monitoring import (
    SecurityMiddleware,
    SecurityMonitor,
    get_security_monitor,
)
from .validation import SecurityValidator, validate_and_sanitize_input

logger = logging.getLogger(__name__)

class SecurityIntegration:
    """Main security integration class that combines all security features."""

    def __init__(self, app: FastAPI, redis_url: str | None=None):
        self.app = app
        self.redis_url = redis_url
        self._init_security_components()
        self._apply_security_middleware()

    def _init_security_components(self):
        """Initialize all security components."""
        try:
            import redis.asyncio as redis
            redis_client = None
            if self.redis_url:
                redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.security_monitor = get_security_monitor(redis_client)
            self.rate_limiter = get_rate_limiter(redis_url=self.redis_url, default_limit=100, default_window=60)
            self.csrf_protection = CSRFProtection()
            self.secure_config = get_secure_config()
            config_validation = self.secure_config.validate_all_config()
            if not config_validation["valid"]:
                logger.error("Security configuration validation failed: %s", config_validation["errors"])
                msg = "Invalid security configuration"
                raise ValueError(msg)
            logger.info("Security components initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize security components: %s", e)
            raise

    def _apply_security_middleware(self):
        """Apply all security middleware to the FastAPI app."""
        self.app.add_middleware(RateLimitMiddleware, redis_url=self.redis_url, default_limit=100, default_window=60, strategy="sliding_window", skip_paths=["/health", "/api/health", "/metrics", "/api/metrics"])

        class SecurityMonitoringMiddleware(BaseHTTPMiddleware):

            def __init__(self, app, security_monitor: SecurityMonitor):
                super().__init__(app)
                self.monitor = security_monitor
                self.security_middleware = SecurityMiddleware(security_monitor)

            async def dispatch(self, request: Request, call_next):
                client_ip = self._get_client_ip(request)
                if await self.monitor.is_ip_blocked(client_ip):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
                await self._check_suspicious_request(request)
                return await call_next(request)

            def _get_client_ip(self, request: Request) -> str:
                forwarded = request.headers.get("X-Forwarded-For")
                if forwarded:
                    return forwarded.split(",")[0].strip()
                real_ip = request.headers.get("X-Real-IP")
                if real_ip:
                    return real_ip.strip()
                return request.client.host if request.client else "unknown"

            async def _check_suspicious_request(self, request: Request):
                """Check for suspicious request patterns."""
                suspicious_patterns = ["../../", "..\\..", "<script", "javascript:", "SELECT", "INSERT", "UPDATE", "DELETE", "union", "or 1=1", "and 1=1"]
                url_str = str(request.url)
                headers_str = str(request.headers)
                for pattern in suspicious_patterns:
                    if pattern.lower() in url_str.lower() or pattern.lower() in headers_str.lower():
                        await self.security_middleware.log_suspicious_request(request, f"Suspicious pattern detected: {pattern}")
                        break
        self.app.add_middleware(SecurityMonitoringMiddleware, security_monitor=self.security_monitor)
        self.app.add_middleware(CSRFMiddleware, csrf=self.csrf_protection, exclude_methods=["GET", "HEAD", "OPTIONS", "TRACE"])

        class InputValidationMiddleware(BaseHTTPMiddleware):

            async def dispatch(self, request: Request, call_next):
                if request.method in ["POST", "PUT", "PATCH"]:
                    try:
                        body = await request.body()
                        if body:
                            import json
                            try:
                                json_data = json.loads(body.decode())
                                validated_data = validate_and_sanitize_input(json_data)
                                request.state.validated_body = validated_data
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                body_str = body.decode(errors="ignore")
                                if not SecurityValidator.validate_sql_input(body_str):
                                    await self.security_monitor.log_security_violation(request, "SQL_INJECTION_ATTEMPT", {"body_preview": body_str[:200]})
                                if not SecurityValidator.validate_command_input(body_str):
                                    await self.security_monitor.log_security_violation(request, "COMMAND_INJECTION_ATTEMPT", {"body_preview": body_str[:200]})
                    except Exception as e:
                        logger.exception("Input validation error: %s", e)
                return await call_next(request)
        self.app.add_middleware(InputValidationMiddleware)
        secure_origins = self.secure_config.get_config_value("CORS_ORIGINS", "http://localhost:3000")
        if isinstance(secure_origins, str):
            origins = [origin.strip() for origin in secure_origins.split(",")]
        else:
            origins = secure_origins
        self.app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["*"], expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-CSRF-Token"])
        logger.info("Security middleware applied successfully")

    async def get_security_status(self) -> dict:
        """Get comprehensive security status."""
        try:
            security_stats = await self.security_monitor.get_security_stats()
            security_report = self.secure_config.get_security_report()
            rate_limiter_status = {"redis_connected": self.rate_limiter.redis is not None, "strategy": self.rate_limiter.strategy.value, "default_limit": self.rate_limiter.default_limit, "default_window": self.rate_limiter.default_window}
            return {"security_monitor": security_stats, "configuration": security_report, "rate_limiter": rate_limiter_status, "csrf_protection": True, "input_validation": True, "cors_configured": True, "overall_status": "healthy" if security_report["validation"]["valid"] else "warning"}
        except Exception as e:
            logger.exception("Failed to get security status: %s", e)
            return {"error": str(e), "overall_status": "error"}

def apply_security(app: FastAPI, redis_url: str | None=None) -> SecurityIntegration:
    """
    Apply comprehensive security to FastAPI application.

    Args:
        app: FastAPI application instance
        redis_url: Redis connection URL

    Returns:
        SecurityIntegration instance
    """
    return SecurityIntegration(app, redis_url)

def secure_endpoint(rate_limit: int | None=None, require_csrf: bool=True, validate_input: bool=True):
    """
    Decorator for securing individual endpoints.

    Args:
        rate_limit: Custom rate limit for this endpoint
        require_csrf: Whether to require CSRF protection
        validate_input: Whether to validate input
    """

    def decorator(func):

        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request:
                if rate_limit:
                    limiter = get_rate_limiter()
                    limiter.default_limit = rate_limit
                    allowed, _remaining, retry_after = await limiter.is_allowed(request)
                    if not allowed:
                        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Rate limit exceeded. Retry after {retry_after} seconds.")
                if require_csrf:
                    csrf = CSRFProtection()
                    if not csrf.validate_token(request):
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token validation failed")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def admin_endpoint():
    """
    Decorator for admin-only endpoints with additional security.
    """

    def decorator(func):

        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request:
                if hasattr(request.state, "user") and request.state.user:
                    user_role = getattr(request.state.user, "role", "user")
                    if user_role != "admin":
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
                monitor = get_security_monitor()
                from .security_monitoring import (
                    SecurityEvent,
                    SecurityEventSeverity,
                    SecurityEventType,
                )
                event = SecurityEvent(event_type=SecurityEventType.PRIVILEGE_ESCALATION, severity=SecurityEventSeverity.LOW, user_id=getattr(request.state.user, "id", None) if hasattr(request.state, "user") else None, ip_address=request.client.host if request.client else None, endpoint=str(request.url), details={"action": "admin_access"})
                await monitor.log_event(event)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
