"""
Vendor-Agnostic Architecture for GraftAI

Implements abstraction layers to reduce vendor lock-in:
- AI Provider Abstraction
- Payment Provider Abstraction
- Calendar Provider Abstraction
- Database Abstraction
- Cache Abstraction
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Provider types for vendor-agnostic architecture"""
    AI = "ai"
    PAYMENT = "payment"
    CALENDAR = "calendar"
    DATABASE = "database"
    CACHE = "cache"
    STORAGE = "storage"

@dataclass
class ProviderConfig:
    """Provider configuration"""
    provider_name: str
    provider_type: ProviderType
    config: dict[str, Any]
    is_primary: bool = True
    priority: int = 1
    rate_limit: int | None = None
    timeout: int | None = None

class BaseProvider(ABC):
    """Base interface for all providers"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.provider_name = config.provider_name
        self.is_healthy = True
        self.last_health_check = datetime.now(UTC)

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize provider connection"""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health"""

    @abstractmethod
    async def cleanup(self):
        """Cleanup provider resources"""

class AIProvider(BaseProvider):
    """Abstract AI provider interface"""

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Generate text using AI model"""

    @abstractmethod
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate text embeddings"""

    @abstractmethod
    async def get_model_info(self) -> dict[str, Any]:
        """Get model information"""

    @abstractmethod
    def get_cost_per_token(self) -> float:
        """Get cost per 1M tokens"""

class PaymentProvider(BaseProvider):
    """Abstract payment provider interface"""

    @abstractmethod
    async def create_customer(self, customer_data: dict[str, Any]) -> dict[str, Any]:
        """Create customer"""

    @abstractmethod
    async def create_subscription(self, customer_id: str, plan_id: str) -> dict[str, Any]:
        """Create subscription"""

    @abstractmethod
    async def process_payment(self, payment_data: dict[str, Any]) -> dict[str, Any]:
        """Process payment"""

    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: int | None=None) -> dict[str, Any]:
        """Refund payment"""

    @abstractmethod
    async def get_customer_subscriptions(self, customer_id: str) -> list[dict[str, Any]]:
        """Get customer subscriptions"""

class CalendarProvider(BaseProvider):
    """Abstract calendar provider interface"""

    @abstractmethod
    async def get_calendars(self, user_token: str) -> list[dict[str, Any]]:
        """Get user calendars"""

    @abstractmethod
    async def create_event(self, user_token: str, event_data: dict[str, Any]) -> dict[str, Any]:
        """Create calendar event"""

    @abstractmethod
    async def update_event(self, user_token: str, event_id: str, event_data: dict[str, Any]) -> dict[str, Any]:
        """Update calendar event"""

    @abstractmethod
    async def delete_event(self, user_token: str, event_id: str) -> bool:
        """Delete calendar event"""

    @abstractmethod
    async def sync_events(self, user_token: str, since: datetime | None=None) -> list[dict[str, Any]]:
        """Sync calendar events"""

class DatabaseProvider(BaseProvider):
    """Abstract database provider interface"""

    @abstractmethod
    async def execute_query(self, query: str, params: dict | None=None) -> list[dict[str, Any]]:
        """Execute database query"""

    @abstractmethod
    async def execute_transaction(self, queries: list[tuple]) -> bool:
        """Execute database transaction"""

    @abstractmethod
    async def get_connection_info(self) -> dict[str, Any]:
        """Get database connection info"""

    @abstractmethod
    async def backup_data(self, tables: list[str] | None=None) -> str:
        """Backup database data"""

    @abstractmethod
    async def restore_data(self, backup_path: str) -> bool:
        """Restore database data"""

class CacheProvider(BaseProvider):
    """Abstract cache provider interface"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache"""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None=None) -> bool:
        """Set value in cache"""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""

    @abstractmethod
    async def clear(self, pattern: str | None=None) -> int:
        """Clear cache values"""

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""

class ProviderManager:
    """Manages multiple providers with failover and load balancing"""

    def __init__(self):
        self.providers: dict[ProviderType, list[BaseProvider]] = {}
        self.primary_providers: dict[ProviderType, BaseProvider] = {}
        self.circuit_breakers: dict[str, dict] = {}
        self.metrics: dict[str, dict] = {}

    def register_provider(self, provider: BaseProvider):
        """Register a provider"""
        provider_type = ProviderType(provider.config.provider_type)
        if provider_type not in self.providers:
            self.providers[provider_type] = []
        self.providers[provider_type].append(provider)
        self.providers[provider_type].sort(key=lambda p: p.config.priority)
        if provider.config.is_primary or not self.primary_providers.get(provider_type):
            self.primary_providers[provider_type] = provider
        circuit_key = f"{provider_type.value}:{provider.provider_name}"
        self.circuit_breakers[circuit_key] = {"failures": 0, "last_failure": None, "state": "closed", "threshold": 5, "timeout": 60}
        self.metrics[circuit_key] = {"requests": 0, "successes": 0, "failures": 0, "latency": []}
        logger.info("Registered %s provider: %s", provider_type.value, provider.provider_name)

    async def get_provider(self, provider_type: ProviderType, force_primary: bool=False) -> BaseProvider | None:
        """Get best available provider for type"""
        if provider_type not in self.providers:
            return None
        if force_primary:
            primary = self.primary_providers.get(provider_type)
            if primary and await self._is_provider_available(primary):
                return primary
            return None
        for provider in self.providers[provider_type]:
            if await self._is_provider_available(provider):
                return provider
        return None

    async def _is_provider_available(self, provider: BaseProvider) -> bool:
        """Check if provider is available"""
        circuit_key = f"{provider.config.provider_type.value}:{provider.provider_name}"
        circuit = self.circuit_breakers[circuit_key]
        if circuit["state"] == "open":
            if (datetime.now(UTC) - circuit["last_failure"]).total_seconds() > circuit["timeout"]:
                circuit["state"] = "half_open"
            else:
                return False
        try:
            is_healthy = await provider.health_check()
            if not is_healthy:
                await self._record_failure(provider)
                return False
            if circuit["state"] == "half_open":
                circuit["state"] = "closed"
                circuit["failures"] = 0
            return True
        except Exception as e:
            logger.exception("Health check failed for %s: %s", provider.provider_name, e)
            await self._record_failure(provider)
            return False

    async def _record_failure(self, provider: BaseProvider):
        """Record provider failure"""
        circuit_key = f"{provider.config.provider_type.value}:{provider.provider_name}"
        circuit = self.circuit_breakers[circuit_key]
        circuit["failures"] += 1
        circuit["last_failure"] = datetime.now(UTC)
        if circuit["failures"] >= circuit["threshold"]:
            circuit["state"] = "open"
        self.metrics[circuit_key]["failures"] += 1

    async def execute_with_provider(self, provider_type: ProviderType, method_name: str, *args, **kwargs):
        """Execute method with automatic failover"""
        provider = await self.get_provider(provider_type)
        if not provider:
            msg = f"No available {provider_type.value} provider"
            raise Exception(msg)
        circuit_key = f"{provider_type.value}:{provider.provider_name}"
        start_time = datetime.now(UTC)
        try:
            self.metrics[circuit_key]["requests"] += 1
            method = getattr(provider, method_name)
            result = await method(*args, **kwargs)
            self.metrics[circuit_key]["successes"] += 1
            latency = (datetime.now(UTC) - start_time).total_seconds()
            self.metrics[circuit_key]["latency"].append(latency)
            return result
        except Exception:
            await self._record_failure(provider)
            next_provider = await self.get_provider(provider_type)
            if next_provider and next_provider != provider:
                logger.warning("Failing over to %s", next_provider.provider_name)
                return await self.execute_with_provider(provider_type, method_name, *args, **kwargs)
            raise

    async def get_provider_metrics(self) -> dict[str, Any]:
        """Get provider performance metrics"""
        metrics_summary = {}
        for circuit_key, metrics in self.metrics.items():
            if metrics["requests"] > 0:
                success_rate = metrics["successes"] / metrics["requests"]
                avg_latency = sum(metrics["latency"]) / len(metrics["latency"]) if metrics["latency"] else 0
                metrics_summary[circuit_key] = {"requests": metrics["requests"], "success_rate": success_rate, "avg_latency": avg_latency, "circuit_state": self.circuit_breakers[circuit_key]["state"]}
        return metrics_summary

    async def switch_primary_provider(self, provider_type: ProviderType, new_provider_name: str):
        """Switch primary provider for type"""
        for provider in self.providers.get(provider_type, []):
            if provider.provider_name == new_provider_name:
                self.primary_providers[provider_type] = provider
                logger.info("Switched primary %s provider to %s", provider_type.value, new_provider_name)
                return True
        return False
provider_manager = ProviderManager()

def get_provider_manager() -> ProviderManager:
    """Get global provider manager instance"""
    return provider_manager

async def initialize_vendor_agnostic_system():
    """Initialize vendor-agnostic system"""
    logger.info("Vendor-agnostic system initialized")

def with_ai_provider(method_name: str="generate_text"):
    """Decorator for AI provider method execution"""

    def decorator(func):

        async def wrapper(*args, **kwargs):
            return await provider_manager.execute_with_provider(ProviderType.AI, method_name, *args, **kwargs)
        return wrapper
    return decorator

def with_payment_provider(method_name: str="process_payment"):
    """Decorator for payment provider method execution"""

    def decorator(func):

        async def wrapper(*args, **kwargs):
            return await provider_manager.execute_with_provider(ProviderType.PAYMENT, method_name, *args, **kwargs)
        return wrapper
    return decorator

def with_calendar_provider(method_name: str="create_event"):
    """Decorator for calendar provider method execution"""

    def decorator(func):

        async def wrapper(*args, **kwargs):
            return await provider_manager.execute_with_provider(ProviderType.CALENDAR, method_name, *args, **kwargs)
        return wrapper
    return decorator
