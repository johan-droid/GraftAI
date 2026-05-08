"""
Cache Optimization Utilities

Implements intelligent caching strategies for:
- Multi-tier caching (memory, Redis, CDN)
- Cache warming and preloading
- Cache invalidation strategies
- Cost-effective cache sizing
"""

import asyncio
import json
import logging
import hashlib
import pickle
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from functools import wraps
from enum import Enum

from backend.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels"""
    MEMORY = "memory"
    REDIS = "redis"
    PERSISTENT = "persistent"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"  # Time-based expiration
    LRU = "lru"  # Least recently used
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    size_bytes: int = 0
    last_access: datetime = None
    
    def __post_init__(self):
        if self.last_access is None:
            self.last_access = datetime.now(timezone.utc)
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def efficiency_score(self) -> float:
        """Calculate cache efficiency (0-100)"""
        hit_rate_score = self.hit_rate * 50
        size_efficiency = min(50, (1000000 - self.size_bytes) / 1000000 * 50)  # Prefer smaller caches
        return hit_rate_score + size_efficiency


@dataclass
class CacheConfig:
    """Cache configuration settings"""
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    max_redis_size: int = 500 * 1024 * 1024   # 500MB
    default_ttl: int = 3600  # 1 hour
    cleanup_interval: int = 300  # 5 minutes
    compression_threshold: int = 1024  # Compress items > 1KB
    strategy: CacheStrategy = CacheStrategy.TTL


class MemoryCache:
    """In-memory LRU cache implementation"""
    
    def __init__(self, max_size: int = 100 * 1024 * 1024):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order: List[str] = []
        self.size_map: Dict[str, int] = {}
        self.current_size = 0
        self.metrics = CacheMetrics()
    
    def _evict_lru(self):
        """Evict least recently used items"""
        while self.current_size > self.max_size and self.access_order:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                item_size = self.size_map[oldest_key]
                del self.cache[oldest_key]
                del self.size_map[oldest_key]
                self.current_size -= item_size
                self.metrics.evictions += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            # Update access order
            self.access_order.remove(key)
            self.access_order.append(key)
            self.metrics.hits += 1
            self.metrics.last_access = datetime.now(timezone.utc)
            return self.cache[key]
        
        self.metrics.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set item in cache"""
        # Serialize value to estimate size
        serialized = pickle.dumps(value)
        item_size = len(serialized)
        
        # Check if we need to evict
        if key not in self.cache:
            self.current_size += item_size
        
        # Store item
        self.cache[key] = value
        self.size_map[key] = item_size
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        # Evict if necessary
        self._evict_lru()
        
        self.metrics.sets += 1
        self.metrics.size_bytes = self.current_size
    
    def delete(self, key: str):
        """Delete item from cache"""
        if key in self.cache:
            item_size = self.size_map[key]
            del self.cache[key]
            del self.size_map[key]
            self.current_size -= item_size
            
            if key in self.access_order:
                self.access_order.remove(key)
            
            self.metrics.deletes += 1
    
    def clear(self):
        """Clear all cache items"""
        self.cache.clear()
        self.access_order.clear()
        self.size_map.clear()
        self.current_size = 0
        self.metrics = CacheMetrics()


class CacheOptimizer:
    """Intelligent multi-tier cache optimization"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.memory_cache = MemoryCache(self.config.max_memory_size)
        self.redis_client = None
        self.metrics_cache_key = "cache_metrics:"
        self.warmup_cache_key = "cache_warmup:"
        
    async def initialize(self):
        """Initialize cache optimizer"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Cache optimizer initialized with Redis backend")
        except Exception as e:
            logger.warning(f"Redis not available for cache optimization: {e}")
    
    def _generate_key(self, prefix: str, identifier: str, params: Dict = None) -> str:
        """Generate consistent cache key"""
        key_parts = [prefix, identifier]
        if params:
            # Sort params for consistency
            sorted_params = sorted(params.items())
            param_str = json.dumps(sorted_params, sort_keys=True)
            key_parts.append(hashlib.md5(param_str.encode()).hexdigest())
        
        return ":".join(key_parts)
    
    async def get(self, key: str, tier: CacheTier = CacheTier.MEMORY) -> Optional[Any]:
        """Get item from cache with tier fallback"""
        start_time = datetime.now(timezone.utc)
        
        # Try memory cache first
        if tier == CacheTier.MEMORY or tier == CacheTier.REDIS:
            value = self.memory_cache.get(key)
            if value is not None:
                return value
        
        # Try Redis cache
        if tier == CacheTier.REDIS and self.redis_client:
            try:
                cached = await self.redis_client.get(key)
                if cached:
                    value = pickle.loads(cached)
                    # Promote to memory cache
                    self.memory_cache.set(key, value)
                    return value
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, tier: CacheTier = CacheTier.MEMORY):
        """Set item in cache with tier selection"""
        ttl = ttl or self.config.default_ttl
        
        # Always set in memory cache
        if tier in [CacheTier.MEMORY, CacheTier.REDIS]:
            self.memory_cache.set(key, value, ttl)
        
        # Set in Redis if requested
        if tier == CacheTier.REDIS and self.redis_client:
            try:
                serialized = pickle.dumps(value)
                await self.redis_client.setex(key, ttl, serialized)
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")
    
    async def delete(self, key: str, tier: CacheTier = CacheTier.MEMORY):
        """Delete item from cache"""
        # Delete from memory cache
        self.memory_cache.delete(key)
        
        # Delete from Redis
        if tier == CacheTier.REDIS and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis cache delete error: {e}")
    
    async def invalidate_pattern(self, pattern: str, tier: CacheTier = CacheTier.MEMORY):
        """Invalidate cache items matching pattern"""
        # Memory cache invalidation
        keys_to_delete = [k for k in self.memory_cache.cache.keys() if pattern in k]
        for key in keys_to_delete:
            self.memory_cache.delete(key)
        
        # Redis invalidation
        if tier == CacheTier.REDIS and self.redis_client:
            try:
                # Use SCAN for safe pattern matching
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                    if keys:
                        await self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error(f"Redis pattern invalidation error: {e}")
    
    async def warm_cache(self, warmup_data: Dict[str, Any]):
        """Warm up cache with frequently accessed data"""
        if not self.redis_client:
            return
        
        warmup_key = f"{self.warmup_cache_key}{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        
        try:
            # Store warmup data in Redis for persistence
            for key, value in warmup_data.items():
                serialized = pickle.dumps(value)
                await self.redis_client.setex(f"warmup:{key}", self.config.default_ttl * 2, serialized)
            
            # Mark warmup complete
            await self.redis_client.setex(warmup_key, 86400, "complete")
            
            logger.info(f"Cache warmed with {len(warmup_data)} items")
            
        except Exception as e:
            logger.error(f"Cache warmup error: {e}")
    
    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        memory_metrics = asdict(self.memory_cache.metrics)
        
        redis_metrics = {}
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                redis_metrics = {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
                
                # Calculate Redis hit rate
                redis_total = redis_metrics["keyspace_hits"] + redis_metrics["keyspace_misses"]
                redis_metrics["hit_rate"] = redis_metrics["keyspace_hits"] / redis_total if redis_total > 0 else 0
                
            except Exception as e:
                logger.error(f"Error getting Redis metrics: {e}")
        
        return {
            "memory_cache": memory_metrics,
            "redis_cache": redis_metrics,
            "overall_hit_rate": memory_metrics["hit_rate"],
            "efficiency_score": self.memory_cache.metrics.efficiency_score,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def optimize_cache_size(self):
        """Automatically optimize cache sizes based on usage patterns"""
        metrics = await self.get_cache_metrics()
        
        # Analyze hit rates and adjust sizes
        memory_hit_rate = metrics["memory_cache"]["hit_rate"]
        memory_size = metrics["memory_cache"]["size_bytes"]
        
        recommendations = []
        
        # If memory cache is inefficient, consider reducing size
        if memory_hit_rate < 0.5 and memory_size > self.config.max_memory_size * 0.8:
            recommendations.append({
                "type": "reduce_memory_cache",
                "current_size_mb": memory_size / (1024 * 1024),
                "hit_rate": memory_hit_rate,
                "suggestion": "Consider reducing memory cache size due to low hit rate"
            })
        
        # If memory cache is highly efficient, consider increasing size
        elif memory_hit_rate > 0.9 and memory_size < self.config.max_memory_size * 0.5:
            recommendations.append({
                "type": "increase_memory_cache",
                "current_size_mb": memory_size / (1024 * 1024),
                "hit_rate": memory_hit_rate,
                "suggestion": "Consider increasing memory cache size due to high hit rate"
            })
        
        return recommendations
    
    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        # Memory cache cleanup (handled by LRU)
        expired_count = 0
        
        # Redis cleanup (handled by Redis TTL)
        if self.redis_client:
            try:
                # Get all keys with TTL and check expiration
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor=cursor, count=1000)
                    
                    for key in keys:
                        ttl = await self.redis_client.ttl(key)
                        if ttl == -1:  # No TTL set, could be expired
                            # Check if key should have TTL based on pattern
                            if any(pattern in key.decode() for pattern in ["cache:", "temp:"]):
                                await self.redis_client.delete(key)
                                expired_count += 1
                    
                    if cursor == 0:
                        break
                        
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired cache entries")
    
    async def preload_frequent_data(self, data_loader: Callable[[], Dict[str, Any]]):
        """Preload frequently accessed data based on usage patterns"""
        if not self.redis_client:
            return
        
        try:
            # Get frequently accessed keys from metrics
            frequent_keys = await self._get_frequent_keys()
            
            if frequent_keys:
                # Load data for frequent keys
                data = await data_loader()
                
                for key in frequent_keys:
                    if key in data:
                        await self.set(key, data[key], ttl=self.config.default_ttl * 2)
                
                logger.info(f"Preloaded {len(frequent_keys)} frequently accessed items")
                
        except Exception as e:
            logger.error(f"Cache preload error: {e}")
    
    async def _get_frequent_keys(self) -> List[str]:
        """Get frequently accessed cache keys"""
        # This would require tracking access patterns
        # For now, return common patterns
        return [
            "user:profile:",
            "user:preferences:",
            "calendar:events:",
            "ai:responses:",
            "booking:recent:"
        ]


# Global cache optimizer instance
cache_optimizer = CacheOptimizer()


def smart_cache(prefix: str, ttl: int = 3600, tier: CacheTier = CacheTier.MEMORY):
    """Decorator for intelligent caching"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await cache_optimizer.initialize()
            
            # Generate cache key
            func_name = func.__name__
            params = {"args": str(args), "kwargs": str(kwargs)}
            cache_key = cache_optimizer._generate_key(prefix, func_name, params)
            
            # Try to get from cache
            cached_result = await cache_optimizer.get(cache_key, tier)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache_optimizer.set(cache_key, result, ttl, tier)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(prefix: str, pattern: str = None):
    """Decorator to invalidate cache after function execution"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            if pattern:
                await cache_optimizer.invalidate_pattern(pattern)
            else:
                # Invalidate all keys with this prefix
                await cache_optimizer.invalidate_pattern(f"{prefix}:*")
            
            return result
        
        return wrapper
    return decorator


async def initialize_cache_optimizer(config: CacheConfig = None):
    """Initialize the cache optimizer"""
    global cache_optimizer
    cache_optimizer = CacheOptimizer(config)
    await cache_optimizer.initialize()
    
    # Start background cleanup task
    asyncio.create_task(background_cache_cleanup())
    
    logger.info("Cache optimizer initialized with background cleanup")


async def background_cache_cleanup():
    """Background task for cache cleanup and optimization"""
    while True:
        try:
            await cache_optimizer.cleanup_expired()
            
            # Optimize cache sizes every hour
            if datetime.now(timezone.utc).minute == 0:
                recommendations = await cache_optimizer.optimize_cache_size()
                if recommendations:
                    logger.info(f"Cache optimization recommendations: {recommendations}")
            
            await asyncio.sleep(cache_optimizer.config.cleanup_interval)
            
        except Exception as e:
            logger.error(f"Background cache cleanup error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error


async def get_cache_optimization_report() -> Dict[str, Any]:
    """Generate comprehensive cache optimization report"""
    metrics = await cache_optimizer.get_cache_metrics()
    recommendations = await cache_optimizer.optimize_cache_size()
    
    return {
        "metrics": metrics,
        "recommendations": recommendations,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
