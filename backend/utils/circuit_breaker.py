"""
Circuit Breaker Pattern Implementation for GraftAI Backend.

Prevents cascade failures when external services are down.
States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)

Usage:
    @circuit_breaker(name="sendgrid", failure_threshold=5, recovery_timeout=60)
    async def send_email(...) -> dict:
        ...
"""

import time
import asyncio
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import threading

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation - requests pass through
    OPEN = "open"  # Failing fast - requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    name: str
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 60.0  # Seconds before trying again
    half_open_max_calls: int = 3  # Test calls in half-open state
    success_threshold: int = 2  # Successes needed to close


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[float] = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    total_calls: int = 0
    rejected_calls: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for external service protection.

    Example:
        breaker = CircuitBreaker(
            name="sendgrid",
            failure_threshold=5,
            recovery_timeout=60
        )

        # Use as decorator
        @breaker
        async def send_email(...) -> dict:
            ...

        # Or use directly
        if breaker.can_execute():
            try:
                result = await send_email(...)
                breaker.record_success()
            except Exception as e:
                breaker.record_failure()
        else:
            # Circuit is open, fail fast
            raise CircuitBreakerOpen("SendGrid circuit is open")
    """

    _instances: Dict[str, "CircuitBreaker"] = {}
    _lock = threading.Lock()

    def __new__(cls, name: str, *args, **kwargs):
        """Singleton pattern - one circuit breaker per name."""
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[name] = instance
            return cls._instances[name]

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
    ):
        # Only initialize once (singleton)
        if hasattr(self, "_initialized"):
            return

        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        self._initialized = True

        logger.info(
            f"[CircuitBreaker:{name}] Initialized "
            f"(threshold={failure_threshold}, timeout={recovery_timeout}s)"
        )

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Current statistics (copy)."""
        return CircuitBreakerStats(
            failures=self._stats.failures,
            successes=self._stats.successes,
            last_failure_time=self._stats.last_failure_time,
            consecutive_successes=self._stats.consecutive_successes,
            consecutive_failures=self._stats.consecutive_failures,
            total_calls=self._stats.total_calls,
            rejected_calls=self._stats.rejected_calls,
        )

    def can_execute(self) -> bool:
        """
        Check if a call can be executed through the circuit.

        Returns:
            True if call should proceed, False if circuit is open
        """
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._stats.last_failure_time:
                elapsed = time.time() - self._stats.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(
                        f"[CircuitBreaker:{self.name}] Recovery timeout passed, "
                        f"transitioning to HALF_OPEN"
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            # Limit test calls in half-open state
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

        return True

    def record_success(self):
        """Record a successful call."""

        async def _record():
            async with self._lock:
                self._stats.successes += 1
                self._stats.consecutive_successes += 1
                self._stats.consecutive_failures = 0
                self._stats.total_calls += 1

                if self._state == CircuitState.HALF_OPEN:
                    if self._stats.consecutive_successes >= self.success_threshold:
                        logger.info(
                            f"[CircuitBreaker:{self.name}] Success threshold reached, "
                            f"closing circuit"
                        )
                        self._state = CircuitState.CLOSED
                        self._half_open_calls = 0

        # Run async operation
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_record())
            else:
                loop.run_until_complete(_record())
        except RuntimeError:
            # No event loop running
            pass

    def record_failure(self):
        """Record a failed call."""

        async def _record():
            async with self._lock:
                self._stats.failures += 1
                self._stats.consecutive_failures += 1
                self._stats.consecutive_successes = 0
                self._stats.last_failure_time = time.time()
                self._stats.total_calls += 1

                if self._state == CircuitState.CLOSED:
                    if self._stats.consecutive_failures >= self.failure_threshold:
                        logger.warning(
                            f"[CircuitBreaker:{self.name}] Failure threshold reached "
                            f"({self.failure_threshold}), opening circuit"
                        )
                        self._state = CircuitState.OPEN

                elif self._state == CircuitState.HALF_OPEN:
                    logger.warning(
                        f"[CircuitBreaker:{self.name}] Failure in half-open state, "
                        f"re-opening circuit"
                    )
                    self._state = CircuitState.OPEN
                    self._half_open_calls = 0

        # Run async operation
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_record())
            else:
                loop.run_until_complete(_record())
        except RuntimeError:
            pass

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to wrap a function with circuit breaker protection.

        Usage:
            breaker = CircuitBreaker("sendgrid")

            @breaker
            async def send_email(...) -> dict:
                ...
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.can_execute():
                self._stats.rejected_calls += 1
                raise CircuitBreakerOpen(
                    f"Circuit '{self.name}' is OPEN - service unavailable"
                )

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                # Don't count certain exceptions as failures
                if not isinstance(e, (CircuitBreakerOpen, asyncio.TimeoutError)):
                    self.record_failure()
                raise

        return wrapper

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status for monitoring."""
        return {
            "name": self.name,
            "state": self._state.value,
            "stats": {
                "failures": self._stats.failures,
                "successes": self._stats.successes,
                "consecutive_failures": self._stats.consecutive_failures,
                "consecutive_successes": self._stats.consecutive_successes,
                "total_calls": self._stats.total_calls,
                "rejected_calls": self._stats.rejected_calls,
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "half_open_max_calls": self.half_open_max_calls,
                "success_threshold": self.success_threshold,
            },
            "last_failure": self._stats.last_failure_time,
        }

    def reset(self):
        """Manually reset circuit to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._half_open_calls = 0
        logger.info(f"[CircuitBreaker:{self.name}] Manually reset to CLOSED")


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    pass


# Pre-configured circuit breakers for common services
SENDGRID_BREAKER = CircuitBreaker(
    name="sendgrid", failure_threshold=5, recovery_timeout=60, success_threshold=2
)

TWILIO_BREAKER = CircuitBreaker(
    name="twilio", failure_threshold=5, recovery_timeout=60, success_threshold=2
)

SLACK_BREAKER = CircuitBreaker(
    name="slack", failure_threshold=5, recovery_timeout=60, success_threshold=2
)

GOOGLE_CALENDAR_BREAKER = CircuitBreaker(
    name="google_calendar",
    failure_threshold=5,
    recovery_timeout=120,  # Longer timeout for calendar
    success_threshold=2,
)


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    half_open_max_calls: int = 3,
    success_threshold: int = 2,
):
    """
    Decorator factory for circuit breaker protection.

    Usage:
        @circuit_breaker(name="sendgrid", failure_threshold=5)
        async def send_email(...) -> dict:
            ...
    """
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=half_open_max_calls,
        success_threshold=success_threshold,
    )
    return breaker


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get existing circuit breaker by name."""
    return CircuitBreaker._instances.get(name)


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return dict(CircuitBreaker._instances)
