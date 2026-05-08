"""
Security integration module for GraftAI backend.
Integrates all security components and provides unified security middleware.
"""

import logging
from typing import Optional, List
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .rate_limiter import RateLimitMiddleware, get_rate_limiter
from .csrf import CSRFMiddleware, CSRFProtection
from .security_monitoring import SecurityMonitor, SecurityMiddleware, get_security_monitor
from .secure_config import get_secure_config
from .validation import validate_and_sanitize_input, SecurityValidator

logger = logging.getLogger(__name__)


class SecurityIntegration:
    """Main security integration class that combines all security features."""
    
    def __init__(self, app: FastAPI, redis_url: Optional[str] = None):
        self.app = app
        self.redis_url = redis_url
        
        # Initialize security components
        self._init_security_components()
        
        # Apply security middleware
        self._apply_security_middleware()
    
    def _init_security_components(self):
        """Initialize all security components."""
        try:
            # Initialize Redis client
            import redis.asyncio as redis
            redis_client = None
            if self.redis_url:
                redis_client = redis.from_url(self.redis_url, decode_responses=True)
            
            # Initialize security monitor
            self.security_monitor = get_security_monitor(redis_client)
            
            # Initialize rate limiter
            self.rate_limiter = get_rate_limiter(
                redis_url=self.redis_url,
                default_limit=100,
                default_window=60
            )
            
            # Initialize CSRF protection
            self.csrf_protection = CSRFProtection()
            
            # Initialize secure config
            self.secure_config = get_secure_config()
            
            # Validate configuration
            config_validation = self.secure_config.validate_all_config()
            if not config_validation["valid"]:
                logger.error(f"Security configuration validation failed: {config_validation['errors']}")
                raise ValueError("Invalid security configuration")
            
            logger.info("Security components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security components: {e}")
            raise
    
    def _apply_security_middleware(self):
        """Apply all security middleware to the FastAPI app."""
        
        # 1. Rate limiting middleware (outermost)
        self.app.add_middleware(
            RateLimitMiddleware,
            redis_url=self.redis_url,
            default_limit=100,
            default_window=60,
            strategy="sliding_window",
            skip_paths=["/health", "/api/health", "/metrics", "/api/metrics"]
        )
        
        # 2. Security monitoring middleware
        class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
            def __init__(self, app, security_monitor: SecurityMonitor):
                super().__init__(app)
                self.monitor = security_monitor
                self.security_middleware = SecurityMiddleware(security_monitor)
            
            async def dispatch(self, request: Request, call_next):
                # Check if IP is blocked
                client_ip = self._get_client_ip(request)
                if await self.monitor.is_ip_blocked(client_ip):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied"
                    )
                
                # Log suspicious requests
                await self._check_suspicious_request(request)
                
                response = await call_next(request)
                return response
            
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
                suspicious_patterns = [
                    "../../", "..\\..",  # Path traversal
                    "<script", "javascript:",  # XSS
                    "SELECT", "INSERT", "UPDATE", "DELETE",  # SQL injection
                    "union", "or 1=1", "and 1=1",  # SQL injection
                ]
                
                # Check URL and headers
                url_str = str(request.url)
                headers_str = str(request.headers)
                
                for pattern in suspicious_patterns:
                    if pattern.lower() in url_str.lower() or pattern.lower() in headers_str.lower():
                        await self.security_middleware.log_suspicious_request(
                            request, f"Suspicious pattern detected: {pattern}"
                        )
                        break
        
        self.app.add_middleware(SecurityMonitoringMiddleware, security_monitor=self.security_monitor)
        
        # 3. CSRF protection middleware (skip for API endpoints that use JWT)
        self.app.add_middleware(
            CSRFMiddleware,
            csrf=self.csrf_protection,
            exclude_methods=["GET", "HEAD", "OPTIONS", "TRACE"]
        )
        
        # 4. Input validation middleware
        class InputValidationMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Validate request body for POST/PUT/PATCH requests
                if request.method in ["POST", "PUT", "PATCH"]:
                    try:
                        # Get request body
                        body = await request.body()
                        if body:
                            # Try to parse as JSON for validation
                            import json
                            try:
                                json_data = json.loads(body.decode())
                                validated_data = validate_and_sanitize_input(json_data)
                                # Store validated data in request state
                                request.state.validated_body = validated_data
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                # Not JSON, check for other suspicious patterns
                                body_str = body.decode(errors='ignore')
                                if not SecurityValidator.validate_sql_input(body_str):
                                    await self.security_monitor.log_security_violation(
                                        request, "SQL_INJECTION_ATTEMPT",
                                        {"body_preview": body_str[:200]}
                                    )
                                if not SecurityValidator.validate_command_input(body_str):
                                    await self.security_monitor.log_security_violation(
                                        request, "COMMAND_INJECTION_ATTEMPT",
                                        {"body_preview": body_str[:200]}
                                    )
                    except Exception as e:
                        logger.error(f"Input validation error: {e}")
                
                response = await call_next(request)
                return response
        
        self.app.add_middleware(InputValidationMiddleware)
        
        # 5. CORS middleware with security headers
        secure_origins = self.secure_config.get_config_value("CORS_ORIGINS", "http://localhost:3000")
        if isinstance(secure_origins, str):
            origins = [origin.strip() for origin in secure_origins.split(",")]
        else:
            origins = secure_origins
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-CSRF-Token"]
        )
        
        logger.info("Security middleware applied successfully")
    
    async def get_security_status(self) -> dict:
        """Get comprehensive security status."""
        try:
            # Get security stats
            security_stats = await self.security_monitor.get_security_stats()
            
            # Get security report
            security_report = self.secure_config.get_security_report()
            
            # Get rate limiter status
            rate_limiter_status = {
                "redis_connected": self.rate_limiter.redis is not None,
                "strategy": self.rate_limiter.strategy.value,
                "default_limit": self.rate_limiter.default_limit,
                "default_window": self.rate_limiter.default_window,
            }
            
            return {
                "security_monitor": security_stats,
                "configuration": security_report,
                "rate_limiter": rate_limiter_status,
                "csrf_protection": True,
                "input_validation": True,
                "cors_configured": True,
                "overall_status": "healthy" if security_report["validation"]["valid"] else "warning"
            }
        except Exception as e:
            logger.error(f"Failed to get security status: {e}")
            return {"error": str(e), "overall_status": "error"}


def apply_security(app: FastAPI, redis_url: Optional[str] = None) -> SecurityIntegration:
    """
    Apply comprehensive security to FastAPI application.
    
    Args:
        app: FastAPI application instance
        redis_url: Redis connection URL
        
    Returns:
        SecurityIntegration instance
    """
    return SecurityIntegration(app, redis_url)


# Security decorators for endpoints
def secure_endpoint(
    rate_limit: Optional[int] = None,
    require_csrf: bool = True,
    validate_input: bool = True
):
    """
    Decorator for securing individual endpoints.
    
    Args:
        rate_limit: Custom rate limit for this endpoint
        require_csrf: Whether to require CSRF protection
        validate_input: Whether to validate input
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                # Custom rate limiting
                if rate_limit:
                    limiter = get_rate_limiter()
                    limiter.default_limit = rate_limit
                    allowed, remaining, retry_after = await limiter.is_allowed(request)
                    if not allowed:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=f"Rate limit exceeded. Retry after {retry_after} seconds."
                        )
                
                # CSRF validation
                if require_csrf:
                    csrf = CSRFProtection()
                    if not csrf.validate_token(request):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="CSRF token validation failed"
                        )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def admin_endpoint():
    """
    Decorator for admin-only endpoints with additional security.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                # Check for admin role
                if hasattr(request.state, 'user') and request.state.user:
                    user_role = getattr(request.state.user, 'role', 'user')
                    if user_role != 'admin':
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required"
                        )
                
                # Log admin access
                monitor = get_security_monitor()
                from .security_monitoring import SecurityEvent, SecurityEventType, SecurityEventSeverity
                event = SecurityEvent(
                    event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                    severity=SecurityEventSeverity.LOW,
                    user_id=getattr(request.state.user, 'id', None) if hasattr(request.state, 'user') else None,
                    ip_address=request.client.host if request.client else None,
                    endpoint=str(request.url),
                    details={"action": "admin_access"}
                )
                await monitor.log_event(event)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
