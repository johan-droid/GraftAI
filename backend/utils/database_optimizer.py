"""
Database Cost Optimization Utilities

Implements intelligent database optimizations for:
- Query performance monitoring
- Connection pool optimization
- Index recommendations
- Storage cost optimization
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.redis import get_redis_client
from backend.utils.cache import get_cache, set_cache

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Database query performance metrics"""
    query_hash: str
    execution_count: int
    avg_duration: float
    total_duration: float
    rows_returned: int
    timestamp: datetime
    is_slow: bool = False


@dataclass
class TableMetrics:
    """Table-level metrics for optimization"""
    table_name: str
    row_count: int
    size_bytes: int
    index_count: int
    unused_indexes: List[str]
    last_analyzed: datetime


class DatabaseOptimizer:
    """Intelligent database cost optimization"""
    
    # Performance thresholds
    SLOW_QUERY_THRESHOLD = 100  # milliseconds
    HIGH_FREQUENCY_QUERY_THRESHOLD = 1000  # executions per hour
    LARGE_RESULT_THRESHOLD = 10000  # rows
    
    # Cost optimization settings
    CONNECTION_POOL_SIZE = 20
    MAX_OVERFLOW = 30
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600  # 1 hour
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.redis_client = None
        self.query_metrics_key = "db_query_metrics:"
        self.table_metrics_key = "db_table_metrics:"
        self.optimization_cache_key = "db_optimizations:"
        
    async def initialize(self):
        """Initialize database optimizer"""
        try:
            self.redis_client = await get_redis_client()
            
            # Set up optimized engine configuration
            self.engine = create_async_engine(
                self.database_url,
                pool_size=self.CONNECTION_POOL_SIZE,
                max_overflow=self.MAX_OVERFLOW,
                pool_timeout=self.POOL_TIMEOUT,
                pool_recycle=self.POOL_RECYCLE,
                echo=False,  # Disable SQL logging in production
            )
            
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize database optimizer: {e}")
    
    async def track_query(self, query: str, duration_ms: float, rows_returned: int = 0):
        """Track query performance for optimization analysis"""
        if not self.redis_client:
            return
        
        # Create query hash (normalized)
        query_hash = self._normalize_query(query)
        
        metrics = QueryMetrics(
            query_hash=query_hash,
            execution_count=1,
            avg_duration=duration_ms,
            total_duration=duration_ms,
            rows_returned=rows_returned,
            timestamp=datetime.now(timezone.utc),
            is_slow=duration_ms > self.SLOW_QUERY_THRESHOLD
        )
        
        # Update metrics in Redis
        hour_key = f"{self.query_metrics_key}{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
        
        try:
            pipe = self.redis_client.pipeline()
            
            # Update query metrics
            pipe.hincrby(hour_key, f"{query_hash}:count", 1)
            pipe.hincrbyfloat(hour_key, f"{query_hash}:total_duration", duration_ms)
            pipe.hincrby(hour_key, f"{query_hash}:rows", rows_returned)
            pipe.hset(hour_key, f"{query_hash}:query", query[:500])  # Store sample query
            pipe.hset(hour_key, f"{query_hash}:last_seen", datetime.now(timezone.utc).isoformat())
            
            # Mark as slow if threshold exceeded
            if duration_ms > self.SLOW_QUERY_THRESHOLD:
                pipe.hset(hour_key, f"{query_hash}:slow", "1")
            
            pipe.expire(hour_key, 24 * 3600)  # Keep 24 hours
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"Error tracking query metrics: {e}")
    
    async def analyze_slow_queries(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Analyze slow queries and provide optimization recommendations"""
        if not self.redis_client:
            return []
        
        slow_queries = []
        now = datetime.now(timezone.utc)
        
        for i in range(hours):
            hour_key = f"{self.query_metrics_key}{(now - timedelta(hours=i)).strftime('%Y%m%d%H')}"
            
            try:
                # Get all query metrics for this hour
                query_data = await self.redis_client.hgetall(hour_key)
                
                # Process query metrics
                for key, value in query_data.items():
                    if key.endswith(":slow") and value == "1":
                        query_hash = key.replace(":slow", "")
                        
                        count = int(await self.redis_client.hget(hour_key, f"{query_hash}:count") or 0)
                        total_duration = float(await self.redis_client.hget(hour_key, f"{query_hash}:total_duration") or 0)
                        rows = int(await self.redis_client.hget(hour_key, f"{query_hash}:rows") or 0)
                        query_sample = await self.redis_client.hget(hour_key, f"{query_hash}:query") or ""
                        
                        avg_duration = total_duration / count if count > 0 else 0
                        
                        slow_queries.append({
                            "query": query_sample,
                            "query_hash": query_hash,
                            "execution_count": count,
                            "avg_duration_ms": avg_duration,
                            "total_duration_ms": total_duration,
                            "rows_returned": rows,
                            "hour": (now - timedelta(hours=i)).strftime('%Y-%m-%d %H:00'),
                            "optimization_suggestions": self._suggest_query_optimization(query_sample, avg_duration, rows)
                        })
                
            except Exception as e:
                logger.error(f"Error analyzing slow queries for hour {i}: {e}")
        
        # Sort by average duration (slowest first)
        slow_queries.sort(key=lambda x: x["avg_duration_ms"], reverse=True)
        
        return slow_queries[:20]  # Return top 20 slow queries
    
    async def analyze_table_metrics(self, db: AsyncSession) -> List[TableMetrics]:
        """Analyze table-level metrics for optimization opportunities"""
        table_metrics = []
        
        try:
            # Get table statistics
            tables_query = """
            SELECT 
                schemaname || '.' || tablename as table_name,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_analyze,
                vacuum_count,
                autovacuum_count
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            """
            
            result = await db.execute(text(tables_query))
            table_stats = result.fetchall()
            
            for stat in table_stats:
                table_name = stat.table_name
                
                # Get table size
                size_query = f"""
                SELECT pg_total_relation_size('{table_name}') as size_bytes
                """
                size_result = await db.execute(text(size_query))
                size_bytes = size_result.scalar() or 0
                
                # Get index information
                index_query = f"""
                SELECT 
                    indexname,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes 
                WHERE schemaname || '.' || tablename = '{table_name}'
                """
                index_result = await db.execute(text(index_query))
                index_stats = index_result.fetchall()
                
                # Identify unused indexes
                unused_indexes = [
                    idx.indexname for idx in index_stats 
                    if idx.scans == 0 and not idx.indexname.startswith("pg_")
                ]
                
                metrics = TableMetrics(
                    table_name=table_name,
                    row_count=stat.live_rows or 0,
                    size_bytes=size_bytes,
                    index_count=len(index_stats),
                    unused_indexes=unused_indexes,
                    last_analyzed=stat.last_analyze or datetime.min.replace(tzinfo=timezone.utc)
                )
                
                table_metrics.append(metrics)
                
        except Exception as e:
            logger.error(f"Error analyzing table metrics: {e}")
        
        return table_metrics
    
    async def generate_optimization_recommendations(self, db: AsyncSession) -> Dict[str, Any]:
        """Generate comprehensive database optimization recommendations"""
        recommendations = {
            "query_optimizations": [],
            "index_optimizations": [],
            "table_optimizations": [],
            "connection_optimizations": [],
            "storage_optimizations": []
        }
        
        # Analyze slow queries
        slow_queries = await self.analyze_slow_queries()
        for query in slow_queries:
            if query["avg_duration_ms"] > 500:  # Very slow queries
                recommendations["query_optimizations"].append({
                    "type": "critical",
                    "query": query["query"][:100] + "...",
                    "issue": f"Very slow query ({query['avg_duration_ms']:.1f}ms avg)",
                    "suggestion": query["optimization_suggestions"][0] if query["optimization_suggestions"] else "Consider query optimization"
                })
        
        # Analyze table metrics
        table_metrics = await self.analyze_table_metrics(db)
        for table in table_metrics:
            # Unused indexes
            if table.unused_indexes:
                recommendations["index_optimizations"].append({
                    "type": "unused_indexes",
                    "table": table.table_name,
                    "indexes": table.unused_indexes,
                    "suggestion": f"Remove {len(table.unused_indexes)} unused indexes to save storage and improve write performance"
                })
            
            # Large tables
            if table.row_count > 100000 and table.index_count < 3:
                recommendations["index_optimizations"].append({
                    "type": "missing_indexes",
                    "table": table.table_name,
                    "rows": table.row_count,
                    "suggestion": "Consider adding indexes for frequently queried columns"
                })
            
            # Table bloat
            if table.size_bytes > 100 * 1024 * 1024:  # > 100MB
                recommendations["storage_optimizations"].append({
                    "type": "large_table",
                    "table": table.table_name,
                    "size_mb": table.size_bytes / (1024 * 1024),
                    "suggestion": "Consider table partitioning or archiving old data"
                })
        
        # Connection pool recommendations
        recommendations["connection_optimizations"] = [
            {
                "type": "pool_size",
                "current": self.CONNECTION_POOL_SIZE,
                "suggestion": "Monitor connection pool utilization and adjust based on load"
            },
            {
                "type": "timeout",
                "current": self.POOL_TIMEOUT,
                "suggestion": "Consider increasing timeout if experiencing connection timeouts"
            }
        ]
        
        return recommendations
    
    def _normalize_query(self, query: str) -> str:
        """Normalize SQL query for consistent hashing"""
        # Remove extra whitespace and normalize case
        normalized = ' '.join(query.split()).lower()
        
        # Remove parameter values (basic approach)
        import re
        normalized = re.sub(r"'[^']*'", "'?'", normalized)  # Replace string literals
        normalized = re.sub(r"\b\d+\b", "?", normalized)  # Replace numbers
        
        return normalized
    
    def _suggest_query_optimization(self, query: str, duration_ms: float, rows: int) -> List[str]:
        """Suggest optimizations for a specific query"""
        suggestions = []
        
        query_lower = query.lower()
        
        # Missing WHERE clause
        if "select" in query_lower and "where" not in query_lower and rows > 1000:
            suggestions.append("Add WHERE clause to limit result set")
        
        # Missing LIMIT clause
        if "select" in query_lower and "limit" not in query_lower and rows > 1000:
            suggestions.append("Add LIMIT clause to prevent large result sets")
        
        # JOIN optimization
        if "join" in query_lower and duration_ms > 200:
            suggestions.append("Consider adding indexes on JOIN columns")
        
        # ORDER BY optimization
        if "order by" in query_lower and duration_ms > 200:
            suggestions.append("Add index on ORDER BY columns")
        
        # General performance
        if duration_ms > 500:
            suggestions.append("Query is very slow - consider EXPLAIN ANALYZE for detailed analysis")
        
        return suggestions
    
    async def implement_optimizations(self, db: AsyncSession, recommendations: Dict[str, Any]):
        """Implement safe database optimizations"""
        implemented = []
        
        for opt in recommendations.get("index_optimizations", []):
            if opt["type"] == "unused_indexes" and len(opt["indexes"]) <= 2:  # Safe to remove
                try:
                    for index_name in opt["indexes"]:
                        drop_sql = f"DROP INDEX IF EXISTS {index_name}"
                        await db.execute(text(drop_sql))
                        implemented.append(f"Dropped unused index: {index_name}")
                except Exception as e:
                    logger.error(f"Failed to drop index {opt['indexes']}: {e}")
        
        # Commit changes
        await db.commit()
        
        return implemented
    
    async def get_cost_savings_estimate(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate potential cost savings from optimizations"""
        savings = {
            "query_time_reduction_ms": 0,
            "storage_reduction_mb": 0,
            "estimated_monthly_savings_usd": 0.0
        }
        
        # Estimate query time savings
        for opt in recommendations.get("query_optimizations", []):
            if opt["type"] == "critical":
                savings["query_time_reduction_ms"] += 400  # Estimate 400ms saved per critical query
        
        # Estimate storage savings from unused indexes
        for opt in recommendations.get("index_optimizations", []):
            if opt["type"] == "unused_indexes":
                # Estimate 10MB per unused index
                savings["storage_reduction_mb"] += len(opt["indexes"]) * 10
        
        # Convert to USD (rough estimates)
        # Assume $0.10 per GB storage, $0.50 per 1M query ms
        storage_savings = (savings["storage_reduction_mb"] / 1024) * 0.10
        query_savings = (savings["query_time_reduction_ms"] / 1000) * 0.50
        
        savings["estimated_monthly_savings_usd"] = (storage_savings + query_savings) * 30
        
        return savings


# Global database optimizer instance
db_optimizer = None


def db_performance_monitor(func):
    """Decorator to monitor database query performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not db_optimizer:
            return await func(*args, **kwargs)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            result = await func(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Estimate rows returned (basic approach)
            rows_returned = 0
            if hasattr(result, 'rowcount'):
                rows_returned = result.rowcount
            elif isinstance(result, list):
                rows_returned = len(result)
            
            # Track the query
            # This is a simplified approach - in practice, you'd want to capture the actual SQL
            await db_optimizer.track_query(
                query=func.__name__,
                duration_ms=duration_ms,
                rows_returned=rows_returned
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Database function failed: {e}")
            raise
    
    return wrapper


async def initialize_database_optimizer(database_url: str):
    """Initialize the database optimizer"""
    global db_optimizer
    db_optimizer = DatabaseOptimizer(database_url)
    await db_optimizer.initialize()
    logger.info("Database optimizer initialized")


async def get_database_optimization_report(db: AsyncSession) -> Dict[str, Any]:
    """Generate comprehensive database optimization report"""
    if not db_optimizer:
        return {"error": "Database optimizer not initialized"}
    
    recommendations = await db_optimizer.generate_optimization_recommendations(db)
    cost_savings = await db_optimizer.get_cost_savings_estimate(recommendations)
    
    return {
        "recommendations": recommendations,
        "cost_savings_estimate": cost_savings,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
