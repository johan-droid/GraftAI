import asyncio
import time
import enum
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(enum.Enum):
    CLOSED = "closed"    # Normal: requests pass through
    OPEN = "open"        # Broken: requests fail fast 
    HALF_OPEN = "half-open" # Recovery: testing the service

class CircuitBreaker:
    """
    SaaS-Grade Resilience:
    Prevents the backend from hanging or timing out synchronously when 
    3rd-party services (Groq, Google, Microsoft) are slow or failing.
    """
    def __init__(self, name: str, threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.threshold = threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0

    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        # 1. Check if we should fail fast
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"🔄 [RESILIENCE] {self.name} is HALF-OPEN. Testing recovery...")
            else:
                raise RuntimeError(f"Circuit '{self.name}' is temporarily OPEN due to repeated failures.")

        # 2. Execute the call
        try:
            # We enforce a strict execution timeout (e.g., 20s) even for non-circuit reasons
            # to keep the "Small CPU" responsive.
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=25.0)
            
            if self.state == CircuitState.HALF_OPEN:
                self.on_success()
            return result
        except asyncio.TimeoutError:
            self.on_failure("TimeoutError")
            raise
        except Exception as e:
            self.on_failure(type(e).__name__)
            raise

    def on_failure(self, error_type: str):
        self.failures += 1
        self.last_failure_time = time.time()
        logger.warning(f"⚠️ [RESILIENCE] {self.name} failure ({error_type}). Count: {self.failures}/{self.threshold}")
        
        if self.failures >= self.threshold:
            self.state = CircuitState.OPEN
            logger.error(f"🚨 [RESILIENCE] {self.name} is now OPEN. Failing fast to protect system.")

    def on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
        logger.info(f"✅ [RESILIENCE] {self.name} is now CLOSED. Service healthy.")

# Registry for centralized management and monitoring
_registry = {}

def get_breaker(name: str, threshold: int = 5, recovery_timeout: int = 60) -> CircuitBreaker:
    if name not in _registry:
        _registry[name] = CircuitBreaker(name, threshold, recovery_timeout)
    return _registry[name]
