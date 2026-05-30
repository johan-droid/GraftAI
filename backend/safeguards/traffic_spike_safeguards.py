"""
Traffic Spike Architectural Safeguards

Comprehensive safeguards to handle traffic spikes:
- Rate limiting and throttling
- Circuit breakers
- Load shedding
- Graceful degradation
- Auto-scaling triggers
"""
import asyncio
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class SafeguardType(Enum):
    """Types of safeguards"""
    RATE_LIMITER = "rate_limiter"
    CIRCUIT_BREAKER = "circuit_breaker"
    LOAD_SHEDDER = "load_shedder"
    DEGRADATION_MANAGER = "degradation_manager"
    AUTO_SCALER = "auto_scaler"
    QUEUE_MANAGER = "queue_manager"
    CACHE_MANAGER = "cache_manager"

class DegradationLevel(Enum):
    """Service degradation levels"""
    FULL = "full"
    DEGRADED = "degraded"
    MINIMAL = "minimal"
    OFFLINE = "offline"

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_second: int
    burst_size: int
    window_seconds: int = 60
    user_based: bool = True
    ip_based: bool = True
    endpoint_based: bool = True

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    success_threshold: int = 3

@dataclass
class LoadSheddingConfig:
    """Load shedding configuration"""
    max_concurrent_requests: int
    priority_levels: int = 3
    timeout_seconds: int = 30
    rejection_rate_threshold: float = 0.1

@dataclass
class DegradationConfig:
    """Service degradation configuration"""
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    response_time_threshold: float = 1000.0
    error_rate_threshold: float = 0.05
    auto_recovery: bool = True

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.user_counters: dict[str, deque] = defaultdict(lambda: deque(maxlen=config.burst_size))
        self.ip_counters: dict[str, deque] = defaultdict(lambda: deque(maxlen=config.burst_size))
        self.endpoint_counters: dict[str, deque] = defaultdict(lambda: deque(maxlen=config.burst_size))
        self.global_counter: deque = deque(maxlen=config.burst_size * 10)

    async def is_allowed(self, user_id: str, ip: str, endpoint: str) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.config.window_seconds
        await self._cleanup_counter(self.global_counter, window_start)
        if len(self.global_counter) >= self.config.requests_per_second * self.config.window_seconds:
            return (False, {"reason": "global_rate_limit", "retry_after": self.config.window_seconds})
        if self.config.user_based and user_id:
            await self._cleanup_counter(self.user_counters[user_id], window_start)
            if len(self.user_counters[user_id]) >= self.config.requests_per_second:
                return (False, {"reason": "user_rate_limit", "retry_after": self.config.window_seconds})
        if self.config.ip_based and ip:
            await self._cleanup_counter(self.ip_counters[ip], window_start)
            if len(self.ip_counters[ip]) >= self.config.requests_per_second:
                return (False, {"reason": "ip_rate_limit", "retry_after": self.config.window_seconds})
        if self.config.endpoint_based and endpoint:
            await self._cleanup_counter(self.endpoint_counters[endpoint], window_start)
            if len(self.endpoint_counters[endpoint]) >= self.config.requests_per_second:
                return (False, {"reason": "endpoint_rate_limit", "retry_after": self.config.window_seconds})
        self.global_counter.append(now)
        if self.config.user_based and user_id:
            self.user_counters[user_id].append(now)
        if self.config.ip_based and ip:
            self.ip_counters[ip].append(now)
        if self.config.endpoint_based and endpoint:
            self.endpoint_counters[endpoint].append(now)
        return (True, {})

    async def _cleanup_counter(self, counter: deque, cutoff_time: float):
        """Clean up old entries from counter"""
        while counter and counter[0] < cutoff_time:
            counter.popleft()

class CircuitBreaker:
    """Circuit breaker for external service protection"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "closed"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                self.success_count = 0
            else:
                msg = "Circuit breaker is open"
                raise Exception(msg)
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.config.expected_exception:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call"""
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = "closed"
                self.failure_count = 0
        else:
            self.failure_count = 0

    async def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.config.failure_threshold:
            self.state = "open"

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return self.last_failure_time and time.time() - self.last_failure_time >= self.config.recovery_timeout

class LoadShedder:
    """Load shedding to prevent system overload"""

    def __init__(self, config: LoadSheddingConfig):
        self.config = config
        self.active_requests = 0
        self.request_queue = asyncio.Queue(maxsize=config.max_concurrent_requests)
        self.rejection_count = 0
        self.total_requests = 0

    async def acquire_slot(self, priority: int=1) -> bool:
        """Acquire request slot"""
        self.total_requests += 1
        if self.active_requests >= self.config.max_concurrent_requests:
            if priority <= self.config.priority_levels // 2:
                return False
            rejection_rate = self.rejection_count / self.total_requests
            if rejection_rate >= self.config.rejection_rate_threshold:
                return False
        self.active_requests += 1
        return True

    async def release_slot(self):
        """Release request slot"""
        self.active_requests = max(0, self.active_requests - 1)

    async def reject_request(self):
        """Record rejected request"""
        self.rejection_count += 1

class DegradationManager:
    """Manages service degradation under load"""

    def __init__(self, config: DegradationConfig):
        self.config = config
        self.current_level = DegradationLevel.FULL
        self.degradation_history: list[dict] = []
        self.last_check = datetime.now(UTC)

    async def check_degradation(self, metrics: dict[str, float]) -> DegradationLevel:
        """Check if service should be degraded"""
        cpu_usage = metrics.get("cpu_usage", 0)
        memory_usage = metrics.get("memory_usage", 0)
        response_time = metrics.get("response_time", 0)
        error_rate = metrics.get("error_rate", 0)
        if cpu_usage >= 95 or memory_usage >= 95 or response_time >= 5000 or (error_rate >= 0.2):
            new_level = DegradationLevel.OFFLINE
        elif cpu_usage >= 85 or memory_usage >= 90 or response_time >= 2000 or (error_rate >= 0.1):
            new_level = DegradationLevel.MINIMAL
        elif cpu_usage >= self.config.cpu_threshold or memory_usage >= self.config.memory_threshold or response_time >= self.config.response_time_threshold or (error_rate >= self.config.error_rate_threshold):
            new_level = DegradationLevel.DEGRADED
        else:
            new_level = DegradationLevel.FULL
        if new_level != self.current_level:
            await self._record_degradation_change(self.current_level, new_level, metrics)
            self.current_level = new_level
        self.last_check = datetime.now(UTC)
        return self.current_level

    async def _record_degradation_change(self, old_level: DegradationLevel, new_level: DegradationLevel, metrics: dict[str, float]):
        """Record degradation change"""
        record = {"timestamp": datetime.now(UTC).isoformat(), "old_level": old_level.value, "new_level": new_level.value, "metrics": metrics, "reason": self._get_degradation_reason(metrics, new_level)}
        self.degradation_history.append(record)
        logger.warning("Service degradation: %s -> %s", old_level.value, new_level.value)

    def _get_degradation_reason(self, metrics: dict[str, float], level: DegradationLevel) -> str:
        """Get reason for degradation"""
        reasons = []
        if metrics.get("cpu_usage", 0) >= 85:
            reasons.append("high_cpu")
        if metrics.get("memory_usage", 0) >= 85:
            reasons.append("high_memory")
        if metrics.get("response_time", 0) >= 1000:
            reasons.append("slow_response")
        if metrics.get("error_rate", 0) >= 0.05:
            reasons.append("high_error_rate")
        return ", ".join(reasons) if reasons else "system_load"

    async def get_degraded_features(self) -> dict[str, bool]:
        """Get feature availability based on degradation level"""
        feature_mapping = {DegradationLevel.FULL: {"ai_chat": True, "calendar_sync": True, "booking_creation": True, "analytics": True, "notifications": True}, DegradationLevel.DEGRADED: {"ai_chat": False, "calendar_sync": True, "booking_creation": True, "analytics": False, "notifications": True}, DegradationLevel.MINIMAL: {"ai_chat": False, "calendar_sync": False, "booking_creation": True, "analytics": False, "notifications": False}, DegradationLevel.OFFLINE: {"ai_chat": False, "calendar_sync": False, "booking_creation": False, "analytics": False, "notifications": False}}
        return feature_mapping.get(self.current_level, {})

class AutoScaler:
    """Auto-scaling based on system metrics"""

    def __init__(self):
        self.scale_up_threshold = 70.0
        self.scale_down_threshold = 30.0
        self.scale_cooldown = 300
        self.last_scale_time = 0
        self.min_instances = 1
        self.max_instances = 10
        self.current_instances = 1

    async def check_scaling(self, metrics: dict[str, float]) -> str | None:
        """Check if scaling is needed"""
        now = time.time()
        if now - self.last_scale_time < self.scale_cooldown:
            return None
        cpu_usage = metrics.get("cpu_usage", 0)
        memory_usage = metrics.get("memory_usage", 0)
        metrics.get("request_rate", 0)
        avg_usage = (cpu_usage + memory_usage) / 2
        if avg_usage >= self.scale_up_threshold and self.current_instances < self.max_instances:
            self.current_instances += 1
            self.last_scale_time = now
            return f"scale_up_to_{self.current_instances}"
        if avg_usage <= self.scale_down_threshold and self.current_instances > self.min_instances:
            self.current_instances -= 1
            self.last_scale_time = now
            return f"scale_down_to_{self.current_instances}"
        return None

class TrafficSpikeSafeguards:
    """Main safeguards coordinator"""

    def __init__(self):
        self.rate_limiters: dict[str, RateLimiter] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.load_shedder: LoadShedder | None = None
        self.degradation_manager: DegradationManager
        self.auto_scaler: AutoScaler
        self.safeguards_active = False
        self._initialize_safeguards()

    def _initialize_safeguards(self):
        """Initialize all safeguard components"""
        self.rate_limiters = {"global": RateLimiter(RateLimitConfig(requests_per_second=1000, burst_size=2000, user_based=False, ip_based=True, endpoint_based=False)), "api": RateLimiter(RateLimitConfig(requests_per_second=100, burst_size=200, user_based=True, ip_based=True, endpoint_based=True)), "ai": RateLimiter(RateLimitConfig(requests_per_second=50, burst_size=100, user_based=True, ip_based=False, endpoint_based=True)), "bookings": RateLimiter(RateLimitConfig(requests_per_second=200, burst_size=400, user_based=True, ip_based=True, endpoint_based=True))}
        self.circuit_breakers = {"database": CircuitBreaker(CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)), "ai_service": CircuitBreaker(CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30, expected_exception=Exception)), "calendar_sync": CircuitBreaker(CircuitBreakerConfig(failure_threshold=5, recovery_timeout=120, expected_exception=Exception)), "payment_gateway": CircuitBreaker(CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60, expected_exception=Exception))}
        self.load_shedder = LoadShedder(LoadSheddingConfig(max_concurrent_requests=1000, priority_levels=3, timeout_seconds=30, rejection_rate_threshold=0.1))
        self.degradation_manager = DegradationManager(DegradationConfig(cpu_threshold=80.0, memory_threshold=85.0, response_time_threshold=1000.0, error_rate_threshold=0.05, auto_recovery=True))
        self.auto_scaler = AutoScaler()

    async def start_safeguards(self):
        """Start all safeguards"""
        self.safeguards_active = True
        logger.info("Traffic spike safeguards activated")

    async def stop_safeguards(self):
        """Stop all safeguards"""
        self.safeguards_active = False
        logger.info("Traffic spike safeguards deactivated")

    async def process_request(self, endpoint: str, user_id: str, ip: str, priority: int=1) -> tuple[bool, dict[str, Any]]:
        """Process request through safeguards"""
        if not self.safeguards_active:
            return (True, {})
        rate_limiter = self._get_rate_limiter(endpoint)
        allowed, limit_info = await rate_limiter.is_allowed(user_id, ip, endpoint)
        if not allowed:
            return (False, {"type": "rate_limit", "info": limit_info})
        if self.load_shedder:
            can_process = await self.load_shedder.acquire_slot(priority)
            if not can_process:
                await self.load_shedder.reject_request()
                return (False, {"type": "load_shedding", "info": {"reason": "overload"}})
        degraded_features = await self.degradation_manager.get_degraded_features()
        feature_name = self._get_feature_name(endpoint)
        if not degraded_features.get(feature_name, True):
            return (False, {"type": "degradation", "info": {"feature": feature_name}})
        return (True, {})

    async def release_request(self):
        """Release request slot"""
        if self.load_shedder:
            await self.load_shedder.release_slot()

    async def check_circuit_breaker(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        circuit_breaker = self.circuit_breakers.get(service_name)
        if circuit_breaker:
            return await circuit_breaker.call(func, *args, **kwargs)
        return await func(*args, **kwargs)

    async def update_metrics(self, metrics: dict[str, float]):
        """Update metrics for safeguards"""
        await self.degradation_manager.check_degradation(metrics)
        scaling_action = await self.auto_scaler.check_scaling(metrics)
        if scaling_action:
            logger.info("Auto-scaling action: %s", scaling_action)

    def _get_rate_limiter(self, endpoint: str) -> RateLimiter:
        """Get appropriate rate limiter for endpoint"""
        if endpoint.startswith("/api/v1/ai"):
            return self.rate_limiters["ai"]
        if endpoint.startswith("/api/v1/bookings"):
            return self.rate_limiters["bookings"]
        return self.rate_limiters["api"]

    def _get_feature_name(self, endpoint: str) -> str:
        """Get feature name from endpoint"""
        if endpoint.startswith("/api/v1/ai"):
            return "ai_chat"
        if endpoint.startswith("/api/v1/calendar"):
            return "calendar_sync"
        if endpoint.startswith("/api/v1/bookings"):
            return "booking_creation"
        if endpoint.startswith("/api/v1/analytics"):
            return "analytics"
        return "notifications"

    async def get_safeguard_status(self) -> dict[str, Any]:
        """Get current safeguard status"""
        return {"safeguards_active": self.safeguards_active, "degradation_level": self.degradation_manager.current_level.value, "degraded_features": await self.degradation_manager.get_degraded_features(), "auto_scaler": {"current_instances": self.auto_scaler.current_instances, "min_instances": self.auto_scaler.min_instances, "max_instances": self.auto_scaler.max_instances}, "load_shedder": {"active_requests": self.load_shedder.active_requests if self.load_shedder else 0, "rejection_count": self.load_shedder.rejection_count if self.load_shedder else 0, "total_requests": self.load_shedder.total_requests if self.load_shedder else 0}, "circuit_breakers": {name: breaker.state for name, breaker in self.circuit_breakers.items()}}
traffic_spike_safeguards = TrafficSpikeSafeguards()

def get_traffic_spike_safeguards() -> TrafficSpikeSafeguards:
    """Get global traffic spike safeguards instance"""
    return traffic_spike_safeguards
from fastapi import HTTPException, Request


async def traffic_spike_middleware(request: Request, call_next):
    """FastAPI middleware for traffic spike safeguards"""
    safeguards = get_traffic_spike_safeguards()
    endpoint = request.url.path
    user_id = getattr(request.state, "user_id", None)
    ip = request.client.host
    priority = getattr(request.state, "priority", 1)
    can_process, safeguard_info = await safeguards.process_request(endpoint, user_id, ip, priority)
    if not can_process:
        if safeguard_info["type"] == "rate_limit":
            raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": str(safeguard_info["info"]["retry_after"])})
        if safeguard_info["type"] == "load_shedding":
            raise HTTPException(status_code=503, detail="Service temporarily unavailable due to high load")
        if safeguard_info["type"] == "degradation":
            raise HTTPException(status_code=503, detail=f"Feature temporarily unavailable: {safeguard_info['info']['feature']}")
    try:
        return await call_next(request)
    finally:
        await safeguards.release_request()
