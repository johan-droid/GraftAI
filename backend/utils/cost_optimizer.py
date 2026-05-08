"""
Cost Optimization Utilities for GraftAI

Implements intelligent cost controls and optimizations for:
- AI token usage monitoring and throttling
- Database query optimization
- Cache efficiency improvements
- Resource usage limits and alerts
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from functools import wraps
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.redis import get_redis
from backend.utils.cache import get_cache, set_cache
from backend.utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)


@dataclass
class CostMetrics:
    """Real-time cost tracking metrics"""
    ai_tokens_used: int = 0
    ai_cost_estimate: float = 0.0
    db_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    external_api_calls: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class CostOptimizer:
    """Centralized cost optimization and monitoring"""
    
    # Cost constants (USD per unit)
    GROQ_COST_PER_1M_TOKENS = 0.50
    OPENAI_COST_PER_1M_TOKENS = 5.00
    PINECONE_COST_PER_1M_VECTORS = 0.70
    DB_READ_COST_PER_1M = 0.10
    DB_WRITE_COST_PER_1M = 1.00
    REDIS_COST_PER_1M_OPS = 0.15
    
    # Optimization thresholds
    MAX_TOKENS_PER_USER_PER_HOUR = 10000
    MAX_DB_QUERIES_PER_MINUTE = 1000
    CACHE_EFFICIENCY_THRESHOLD = 0.8
    COST_ALERT_THRESHOLD = 100.0  # $100 per hour
    
    def __init__(self):
        self.redis_client = None
        self.metrics_cache_key = "cost_metrics:"
        self.user_metrics_key = "user_cost_metrics:"
        self.global_metrics_key = "global_cost_metrics"
        
    async def initialize(self):
        """Initialize Redis client for distributed tracking"""
        try:
            self.redis_client = await get_redis_client()
        except Exception as e:
            logger.warning(f"Redis not available for cost optimization: {e}")
    
    async def track_ai_usage(self, user_id: str, tokens: int, model: str = "groq") -> float:
        """Track AI token usage and estimate cost"""
        cost_per_token = self.GROQ_COST_PER_1M_TOKENS / 1_000_000
        if "openai" in model.lower():
            cost_per_token = self.OPENAI_COST_PER_1M_TOKENS / 1_000_000
            
        cost = tokens * cost_per_token
        
        # Update user metrics
        await self._update_user_metrics(user_id, {
            "ai_tokens_used": tokens,
            "ai_cost_estimate": cost
        })
        
        # Check hourly limits
        await self._check_user_limits(user_id, tokens)
        
        return cost
    
    async def track_db_usage(self, operation: str, table: str, rows_affected: int = 1):
        """Track database operations for cost analysis"""
        cost_multiplier = self.DB_READ_COST_PER_1M / 1_000_000
        if operation in ["INSERT", "UPDATE", "DELETE"]:
            cost_multiplier = self.DB_WRITE_COST_PER_1M / 1_000_000
            
        cost = rows_affected * cost_multiplier
        
        # Track expensive queries
        if rows_affected > 100:
            logger.warning(f"Expensive DB operation: {operation} on {table} affecting {rows_affected} rows")
        
        await self._update_global_metrics({
            "db_queries": 1,
            "estimated_db_cost": cost
        })
    
    async def track_cache_performance(self, hit: bool):
        """Track cache hit/miss ratios"""
        metric_key = "cache_hits" if hit else "cache_misses"
        await self._update_global_metrics({metric_key: 1})
    
    async def get_cost_report(self, user_id: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Generate cost analysis report"""
        if user_id:
            return await self._get_user_cost_report(user_id, hours)
        else:
            return await self._get_global_cost_report(hours)
    
    async def _update_user_metrics(self, user_id: str, metrics: Dict[str, Any]):
        """Update per-user cost metrics with hourly aggregation"""
        if not self.redis_client:
            return
            
        key = f"{self.user_metrics_key}{user_id}"
        hour_key = f"{key}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
        
        # Use Redis HINCRBY for atomic increments
        pipe = self.redis_client.pipeline()
        for field, value in metrics.items():
            if isinstance(value, (int, float)):
                pipe.hincrby(hour_key, field, int(value))
        
        # Set expiry for hourly data (keep 7 days)
        pipe.expire(hour_key, 7 * 24 * 3600)
        await pipe.execute()
    
    async def _update_global_metrics(self, metrics: Dict[str, Any]):
        """Update global cost metrics"""
        if not self.redis_client:
            return
            
        key = f"{self.global_metrics_key}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
        
        pipe = self.redis_client.pipeline()
        for field, value in metrics.items():
            if isinstance(value, (int, float)):
                pipe.hincrby(key, field, int(value))
        
        pipe.expire(key, 24 * 3600)  # Keep 24 hours
        await pipe.execute()
    
    async def _check_user_limits(self, user_id: str, tokens: int):
        """Check if user is approaching cost limits"""
        if not self.redis_client:
            return
            
        hour_key = f"{self.user_metrics_key}{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
        
        try:
            current_tokens = await self.redis_client.hget(hour_key, "ai_tokens_used")
            if current_tokens and int(current_tokens) + tokens > self.MAX_TOKENS_PER_USER_PER_HOUR:
                logger.warning(f"User {user_id} approaching token limit: {current_tokens} + {tokens}")
                # Could trigger rate limiting or user notification here
        except Exception as e:
            logger.error(f"Error checking user limits: {e}")
    
    async def _get_user_cost_report(self, user_id: str, hours: int) -> Dict[str, Any]:
        """Generate per-user cost report"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        # Aggregate data across hours
        now = datetime.now(timezone.utc)
        total_metrics = CostMetrics()
        
        for i in range(hours):
            hour_key = f"{self.user_metrics_key}{user_id}:{(now - timedelta(hours=i)).strftime('%Y%m%d%H')}"
            try:
                data = await self.redis_client.hgetall(hour_key)
                for field, value in data.items():
                    if hasattr(total_metrics, field):
                        setattr(total_metrics, field, getattr(total_metrics, field) + int(value))
            except Exception:
                continue
        
        return asdict(total_metrics)
    
    async def _get_global_cost_report(self, hours: int) -> Dict[str, Any]:
        """Generate global cost report"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        now = datetime.now(timezone.utc)
        total_metrics = CostMetrics()
        
        for i in range(hours):
            hour_key = f"{self.global_metrics_key}:{(now - timedelta(hours=i)).strftime('%Y%m%d%H')}"
            try:
                data = await self.redis_client.hgetall(hour_key)
                for field, value in data.items():
                    if hasattr(total_metrics, field):
                        setattr(total_metrics, field, getattr(total_metrics, field) + int(value))
            except Exception:
                continue
        
        # Calculate cache efficiency
        cache_total = total_metrics.cache_hits + total_metrics.cache_misses
        cache_efficiency = total_metrics.cache_hits / cache_total if cache_total > 0 else 0
        
        report = asdict(total_metrics)
        report["cache_efficiency"] = cache_efficiency
        report["estimated_hourly_cost"] = total_metrics.ai_cost_estimate
        
        return report


# Global cost optimizer instance
cost_optimizer = CostOptimizer()


def cost_track_ai(func):
    """Decorator to track AI costs automatically"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract user_id and estimate tokens from function call
        user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', None)
        
        # Estimate tokens from prompt (rough heuristic)
        prompt = kwargs.get('prompt', '') or getattr(args[0] if args else None, 'prompt', '')
        estimated_tokens = len(prompt) // 4  # Rough estimate
        
        # Track before execution
        start_time = datetime.now(timezone.utc)
        
        try:
            result = await func(*args, **kwargs)
            
            # Track actual usage (would need to be returned by the function)
            actual_tokens = getattr(result, 'tokens_used', estimated_tokens)
            model = getattr(result, 'model', 'groq')
            
            if user_id:
                await cost_optimizer.track_ai_usage(user_id, actual_tokens, model)
            
            return result
            
        except Exception as e:
            logger.error(f"AI function failed: {e}")
            raise
            
    return wrapper


def cost_track_db(func):
    """Decorator to track database costs"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now(timezone.utc)
        
        try:
            result = await func(*args, **kwargs)
            
            # Estimate operation cost based on result
            if hasattr(result, 'rowcount'):
                operation = kwargs.get('operation', 'SELECT')
                table = kwargs.get('table', 'unknown')
                await cost_optimizer.track_db_usage(operation, table, result.rowcount)
            
            return result
            
        except Exception as e:
            logger.error(f"DB function failed: {e}")
            raise
            
    return wrapper


async def optimize_database_queries(db: AsyncSession) -> Dict[str, Any]:
    """Analyze and suggest database query optimizations"""
    
    # Check for slow queries (would need query logging enabled)
    slow_queries_sql = """
    SELECT query, mean_time, calls, total_time
    FROM pg_stat_statements
    WHERE mean_time > 100  -- queries taking more than 100ms
    ORDER BY mean_time DESC
    LIMIT 10
    """
    
    optimization_suggestions = []
    
    try:
        result = await db.execute(text(slow_queries_sql))
        slow_queries = result.fetchall()
        
        for query in slow_queries:
            optimization_suggestions.append({
                "type": "slow_query",
                "query": query.query[:100] + "...",
                "mean_time": query.mean_time,
                "suggestion": "Consider adding index or optimizing query structure"
            })
    except Exception as e:
        logger.warning(f"Could not analyze slow queries: {e}")
    
    # Check cache efficiency
    cache_report = await cost_optimizer.get_cost_report(hours=1)
    cache_efficiency = cache_report.get("cache_efficiency", 0)
    
    if cache_efficiency < cost_optimizer.CACHE_EFFICIENCY_THRESHOLD:
        optimization_suggestions.append({
            "type": "cache_efficiency",
            "current_efficiency": cache_efficiency,
            "suggestion": "Cache efficiency below threshold. Consider cache warming or TTL optimization"
        })
    
    return {
        "optimizations": optimization_suggestions,
        "cache_efficiency": cache_efficiency,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def implement_cost_controls():
    """Implement active cost control measures"""
    
    # Initialize cost optimizer
    await cost_optimizer.initialize()
    
    # Set up cost monitoring alerts
    async def monitor_costs():
        while True:
            try:
                report = await cost_optimizer.get_cost_report(hours=1)
                hourly_cost = report.get("estimated_hourly_cost", 0)
                
                if hourly_cost > cost_optimizer.COST_ALERT_THRESHOLD:
                    logger.critical(f"Cost alert: Hourly cost ${hourly_cost:.2f} exceeds threshold")
                    # Could trigger scaling decisions or user notifications here
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Cost monitoring error: {e}")
                await asyncio.sleep(300)
    
    # Start background monitoring
    asyncio.create_task(monitor_costs())
    
    logger.info("Cost optimization controls initialized")


# Usage monitoring middleware
class CostMonitoringMiddleware:
    """FastAPI middleware for cost monitoring"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Track request start
        start_time = datetime.now(timezone.utc)
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate request duration and estimate cost
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                # Track based on endpoint
                path = scope.get("path", "")
                if "/ai" in path:
                    await cost_optimizer.track_ai_usage("anonymous", 100)  # Estimate
                elif "/api" in path:
                    await cost_optimizer.track_db_usage("SELECT", "unknown", 1)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
