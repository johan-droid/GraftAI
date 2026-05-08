"""
Vendor-Agnostic Architecture for GraftAI

Implements abstraction layers to reduce vendor lock-in:
- AI Provider Abstraction
- Payment Provider Abstraction  
- Calendar Provider Abstraction
- Database Abstraction
- Cache Abstraction
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timezone

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
    config: Dict[str, Any]
    is_primary: bool = True
    priority: int = 1
    rate_limit: Optional[int] = None
    timeout: Optional[int] = None


class BaseProvider(ABC):
    """Base interface for all providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.provider_name = config.provider_name
        self.is_healthy = True
        self.last_health_check = datetime.now(timezone.utc)
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize provider connection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup provider resources"""
        pass


class AIProvider(BaseProvider):
    """Abstract AI provider interface"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using AI model"""
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate text embeddings"""
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass
    
    @abstractmethod
    def get_cost_per_token(self) -> float:
        """Get cost per 1M tokens"""
        pass


class PaymentProvider(BaseProvider):
    """Abstract payment provider interface"""
    
    @abstractmethod
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer"""
        pass
    
    @abstractmethod
    async def create_subscription(self, customer_id: str, plan_id: str) -> Dict[str, Any]:
        """Create subscription"""
        pass
    
    @abstractmethod
    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment"""
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Refund payment"""
        pass
    
    @abstractmethod
    async def get_customer_subscriptions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer subscriptions"""
        pass


class CalendarProvider(BaseProvider):
    """Abstract calendar provider interface"""
    
    @abstractmethod
    async def get_calendars(self, user_token: str) -> List[Dict[str, Any]]:
        """Get user calendars"""
        pass
    
    @abstractmethod
    async def create_event(self, user_token: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create calendar event"""
        pass
    
    @abstractmethod
    async def update_event(self, user_token: str, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update calendar event"""
        pass
    
    @abstractmethod
    async def delete_event(self, user_token: str, event_id: str) -> bool:
        """Delete calendar event"""
        pass
    
    @abstractmethod
    async def sync_events(self, user_token: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Sync calendar events"""
        pass


class DatabaseProvider(BaseProvider):
    """Abstract database provider interface"""
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute database query"""
        pass
    
    @abstractmethod
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute database transaction"""
        pass
    
    @abstractmethod
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection info"""
        pass
    
    @abstractmethod
    async def backup_data(self, tables: Optional[List[str]] = None) -> str:
        """Backup database data"""
        pass
    
    @abstractmethod
    async def restore_data(self, backup_path: str) -> bool:
        """Restore database data"""
        pass


class CacheProvider(BaseProvider):
    """Abstract cache provider interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache values"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass


class ProviderManager:
    """Manages multiple providers with failover and load balancing"""
    
    def __init__(self):
        self.providers: Dict[ProviderType, List[BaseProvider]] = {}
        self.primary_providers: Dict[ProviderType, BaseProvider] = {}
        self.circuit_breakers: Dict[str, Dict] = {}
        self.metrics: Dict[str, Dict] = {}
    
    def register_provider(self, provider: BaseProvider):
        """Register a provider"""
        provider_type = ProviderType(provider.config.provider_type)
        
        if provider_type not in self.providers:
            self.providers[provider_type] = []
        
        self.providers[provider_type].append(provider)
        
        # Sort by priority
        self.providers[provider_type].sort(key=lambda p: p.config.priority)
        
        # Set primary provider
        if provider.config.is_primary or not self.primary_providers.get(provider_type):
            self.primary_providers[provider_type] = provider
        
        # Initialize circuit breaker
        circuit_key = f"{provider_type.value}:{provider.provider_name}"
        self.circuit_breakers[circuit_key] = {
            "failures": 0,
            "last_failure": None,
            "state": "closed",  # closed, open, half_open
            "threshold": 5,
            "timeout": 60
        }
        
        # Initialize metrics
        self.metrics[circuit_key] = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "latency": []
        }
        
        logger.info(f"Registered {provider_type.value} provider: {provider.provider_name}")
    
    async def get_provider(self, provider_type: ProviderType, force_primary: bool = False) -> Optional[BaseProvider]:
        """Get best available provider for type"""
        if provider_type not in self.providers:
            return None
        
        if force_primary:
            primary = self.primary_providers.get(provider_type)
            if primary and await self._is_provider_available(primary):
                return primary
            return None
        
        # Try providers in order of priority
        for provider in self.providers[provider_type]:
            if await self._is_provider_available(provider):
                return provider
        
        return None
    
    async def _is_provider_available(self, provider: BaseProvider) -> bool:
        """Check if provider is available"""
        circuit_key = f"{provider.config.provider_type.value}:{provider.provider_name}"
        circuit = self.circuit_breakers[circuit_key]
        
        # Check circuit breaker
        if circuit["state"] == "open":
            if (datetime.now(timezone.utc) - circuit["last_failure"]).total_seconds() > circuit["timeout"]:
                circuit["state"] = "half_open"
            else:
                return False
        
        # Check health
        try:
            is_healthy = await provider.health_check()
            if not is_healthy:
                await self._record_failure(provider)
                return False
            
            # Reset circuit breaker on success
            if circuit["state"] == "half_open":
                circuit["state"] = "closed"
                circuit["failures"] = 0
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed for {provider.provider_name}: {e}")
            await self._record_failure(provider)
            return False
    
    async def _record_failure(self, provider: BaseProvider):
        """Record provider failure"""
        circuit_key = f"{provider.config.provider_type.value}:{provider.provider_name}"
        circuit = self.circuit_breakers[circuit_key]
        
        circuit["failures"] += 1
        circuit["last_failure"] = datetime.now(timezone.utc)
        
        # Open circuit breaker if threshold exceeded
        if circuit["failures"] >= circuit["threshold"]:
            circuit["state"] = "open"
        
        self.metrics[circuit_key]["failures"] += 1
    
    async def execute_with_provider(self, provider_type: ProviderType, method_name: str, *args, **kwargs):
        """Execute method with automatic failover"""
        provider = await self.get_provider(provider_type)
        if not provider:
            raise Exception(f"No available {provider_type.value} provider")
        
        circuit_key = f"{provider_type.value}:{provider.provider_name}"
        start_time = datetime.now(timezone.utc)
        
        try:
            self.metrics[circuit_key]["requests"] += 1
            
            # Execute method
            method = getattr(provider, method_name)
            result = await method(*args, **kwargs)
            
            # Record success
            self.metrics[circuit_key]["successes"] += 1
            latency = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.metrics[circuit_key]["latency"].append(latency)
            
            return result
            
        except Exception as e:
            await self._record_failure(provider)
            
            # Try next provider
            next_provider = await self.get_provider(provider_type)
            if next_provider and next_provider != provider:
                logger.warning(f"Failing over to {next_provider.provider_name}")
                return await self.execute_with_provider(provider_type, method_name, *args, **kwargs)
            
            raise e
    
    async def get_provider_metrics(self) -> Dict[str, Any]:
        """Get provider performance metrics"""
        metrics_summary = {}
        
        for circuit_key, metrics in self.metrics.items():
            if metrics["requests"] > 0:
                success_rate = metrics["successes"] / metrics["requests"]
                avg_latency = sum(metrics["latency"]) / len(metrics["latency"]) if metrics["latency"] else 0
                
                metrics_summary[circuit_key] = {
                    "requests": metrics["requests"],
                    "success_rate": success_rate,
                    "avg_latency": avg_latency,
                    "circuit_state": self.circuit_breakers[circuit_key]["state"]
                }
        
        return metrics_summary
    
    async def switch_primary_provider(self, provider_type: ProviderType, new_provider_name: str):
        """Switch primary provider for type"""
        for provider in self.providers.get(provider_type, []):
            if provider.provider_name == new_provider_name:
                self.primary_providers[provider_type] = provider
                logger.info(f"Switched primary {provider_type.value} provider to {new_provider_name}")
                return True
        
        return False


# Global provider manager
provider_manager = ProviderManager()


def get_provider_manager() -> ProviderManager:
    """Get global provider manager instance"""
    return provider_manager


async def initialize_vendor_agnostic_system():
    """Initialize vendor-agnostic system"""
    # This would be called during application startup
    # Providers would be registered based on configuration
    logger.info("Vendor-agnostic system initialized")


# Example usage decorators
def with_ai_provider(method_name: str = "generate_text"):
    """Decorator for AI provider method execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await provider_manager.execute_with_provider(
                ProviderType.AI, method_name, *args, **kwargs
            )
        return wrapper
    return decorator


def with_payment_provider(method_name: str = "process_payment"):
    """Decorator for payment provider method execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await provider_manager.execute_with_provider(
                ProviderType.PAYMENT, method_name, *args, **kwargs
            )
        return wrapper
    return decorator


def with_calendar_provider(method_name: str = "create_event"):
    """Decorator for calendar provider method execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await provider_manager.execute_with_provider(
                ProviderType.CALENDAR, method_name, *args, **kwargs
            )
        return wrapper
    return decorator
