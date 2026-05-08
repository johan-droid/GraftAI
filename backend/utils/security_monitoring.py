"""
Security monitoring and logging utilities for GraftAI backend.
Provides comprehensive security event tracking and alerting.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import Request
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SecurityEventSeverity(Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Security event types."""
    FAILED_LOGIN = "failed_login"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SUSPICIOUS_REQUEST = "suspicious_request"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_VIOLATION = "csrf_violation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}


class SecurityMonitor:
    """Security monitoring and alerting system."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.events_key = "security_events"
        self.alerts_key = "security_alerts"
        self.blocked_ips_key = "blocked_ips"
        self.suspicious_ips_key = "suspicious_ips"
        
        # Event thresholds for alerting
        self.thresholds = {
            SecurityEventType.FAILED_LOGIN: {"count": 5, "window": 300},  # 5 failures in 5 minutes
            SecurityEventType.BRUTE_FORCE_ATTEMPT: {"count": 3, "window": 300},
            SecurityEventType.RATE_LIMIT_EXCEEDED: {"count": 10, "window": 300},
            SecurityEventType.INVALID_TOKEN: {"count": 20, "window": 3600},
            SecurityEventType.SQL_INJECTION_ATTEMPT: {"count": 1, "window": 3600},
            SecurityEventType.XSS_ATTEMPT: {"count": 1, "window": 3600},
        }
    
    async def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event.
        
        Args:
            event: Security event to log
        """
        # Log to standard logging
        log_level = {
            SecurityEventSeverity.LOW: logging.INFO,
            SecurityEventSeverity.MEDIUM: logging.WARNING,
            SecurityEventSeverity.HIGH: logging.ERROR,
            SecurityEventSeverity.CRITICAL: logging.CRITICAL,
        }.get(event.severity, logging.INFO)
        
        logger.log(
            log_level,
            f"Security Event: {event.event_type.value} - {event.severity.value} - "
            f"User: {event.user_id} - IP: {event.ip_address} - "
            f"Endpoint: {event.endpoint} - Details: {event.details}"
        )
        
        # Store in Redis for analysis
        if self.redis:
            try:
                event_data = asdict(event)
                event_data["timestamp"] = event.timestamp.isoformat()
                event_data["event_type"] = event.event_type.value
                event_data["severity"] = event.severity.value
                
                # Store event
                await self.redis.lpush(
                    self.events_key,
                    json.dumps(event_data)
                )
                
                # Trim events list (keep last 10000)
                await self.redis.ltrim(self.events_key, 0, 9999)
                
                # Check thresholds and create alerts
                await self._check_thresholds(event)
                
            except Exception as e:
                logger.error(f"Failed to log security event to Redis: {e}")
    
    async def _check_thresholds(self, event: SecurityEvent) -> None:
        """
        Check if event exceeds thresholds and create alerts.
        
        Args:
            event: Security event to check
        """
        if not self.redis or event.event_type not in self.thresholds:
            return
        
        threshold = self.thresholds[event.event_type]
        key = f"event_counts:{event.event_type.value}:{event.ip_address}"
        
        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, threshold["window"])
        count = await pipe.execute()[0]
        
        # Check if threshold exceeded
        if count >= threshold["count"]:
            await self._create_alert(event, count, threshold)
            
            # Auto-block for critical events
            if event.severity in [SecurityEventSeverity.HIGH, SecurityEventSeverity.CRITICAL]:
                await self._block_ip(event.ip_address, duration=3600)
    
    async def _create_alert(self, event: SecurityEvent, count: int, threshold: Dict) -> None:
        """
        Create security alert.
        
        Args:
            event: Security event
            count: Event count
            threshold: Threshold configuration
        """
        alert = {
            "alert_type": "threshold_exceeded",
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "ip_address": event.ip_address,
            "count": count,
            "threshold": threshold["count"],
            "window": threshold["window"],
            "timestamp": datetime.utcnow().isoformat(),
            "details": event.details
        }
        
        # Store alert
        await self.redis.lpush(self.alerts_key, json.dumps(alert))
        await self.redis.ltrim(self.alerts_key, 0, 999)
        
        # Log critical alert
        logger.critical(
            f"SECURITY ALERT: {event.event_type.value} threshold exceeded - "
            f"Count: {count}/{threshold['count']} - IP: {event.ip_address}"
        )
    
    async def _block_ip(self, ip_address: str, duration: int = 3600) -> None:
        """
        Block an IP address.
        
        Args:
            ip_address: IP address to block
            duration: Block duration in seconds
        """
        if not self.redis or not ip_address:
            return
        
        await self.redis.setex(
            f"blocked_ip:{ip_address}",
            duration,
            datetime.utcnow().isoformat()
        )
        
        logger.warning(f"IP address blocked: {ip_address} for {duration} seconds")
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Check if IP address is blocked.
        
        Args:
            ip_address: IP address to check
            
        Returns:
            bool: True if blocked, False otherwise
        """
        if not self.redis or not ip_address:
            return False
        
        result = await self.redis.get(f"blocked_ip:{ip_address}")
        return result is not None
    
    async def get_security_stats(self) -> Dict[str, Any]:
        """
        Get security statistics.
        
        Returns:
            Dict containing security statistics
        """
        if not self.redis:
            return {}
        
        try:
            # Get recent events count
            recent_events = await self.redis.lrange(self.events_key, 0, -1)
            
            # Get active alerts
            active_alerts = await self.redis.lrange(self.alerts_key, 0, -1)
            
            # Get blocked IPs count
            blocked_keys = await self.redis.keys("blocked_ip:*")
            
            return {
                "total_events": len(recent_events),
                "active_alerts": len(active_alerts),
                "blocked_ips": len(blocked_keys),
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get security stats: {e}")
            return {}
    
    async def cleanup_old_events(self, days: int = 30) -> None:
        """
        Clean up old security events.
        
        Args:
            days: Number of days to keep events
        """
        if not self.redis:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        try:
            # Clean up old events (simplified - in production, use more efficient methods)
            events = await self.redis.lrange(self.events_key, 0, -1)
            events_to_keep = []
            
            for event_json in events:
                try:
                    event = json.loads(event_json)
                    event_time = datetime.fromisoformat(event["timestamp"])
                    if event_time > cutoff_time:
                        events_to_keep.append(event_json)
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
            
            # Update events list
            await self.redis.delete(self.events_key)
            if events_to_keep:
                await self.redis.lpush(self.events_key, *events_to_keep)
            
            logger.info(f"Cleaned up old security events, kept {len(events_to_keep)} events")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")


class SecurityMiddleware:
    """Security monitoring middleware for FastAPI."""
    
    def __init__(self, security_monitor: SecurityMonitor):
        self.monitor = security_monitor
    
    async def log_failed_login(self, request: Request, user_id: Optional[str] = None, details: Optional[Dict] = None):
        """Log failed login attempt."""
        event = SecurityEvent(
            event_type=SecurityEventType.FAILED_LOGIN,
            severity=SecurityEventSeverity.MEDIUM,
            user_id=user_id,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            endpoint=str(request.url),
            details=details or {}
        )
        await self.monitor.log_event(event)
    
    async def log_suspicious_request(self, request: Request, reason: str, details: Optional[Dict] = None):
        """Log suspicious request."""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_REQUEST,
            severity=SecurityEventSeverity.HIGH,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            endpoint=str(request.url),
            details={"reason": reason, **(details or {})}
        )
        await self.monitor.log_event(event)
    
    async def log_security_violation(self, request: Request, violation_type: str, details: Optional[Dict] = None):
        """Log security violation."""
        event = SecurityEvent(
            event_type=SecurityEventType[violation_type.upper()],
            severity=SecurityEventSeverity.HIGH,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            endpoint=str(request.url),
            details=details or {}
        )
        await self.monitor.log_event(event)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        return request.client.host if request.client else "unknown"


# Global security monitor instance
_security_monitor: Optional[SecurityMonitor] = None


def get_security_monitor(redis_client: Optional[redis.Redis] = None) -> SecurityMonitor:
    """Get or create global security monitor instance."""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityMonitor(redis_client)
    return _security_monitor


def reset_security_monitor():
    """Reset global security monitor instance (primarily for testing)."""
    global _security_monitor
    _security_monitor = None
