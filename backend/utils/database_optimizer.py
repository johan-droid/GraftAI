"""
Database Cost Optimization Utilities

Implements intelligent database optimizations for:
- Query performance monitoring
- Connection pool optimization
- Index recommendations
- Storage cost optimization
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.redis import get_redis_client

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
    unused_indexes: list[str]
    last_analyzed: datetime

class DatabaseOptimizer:
    """Intelligent database cost optimization"""
    SLOW_QUERY_THRESHOLD = 100
    HIGH_FREQUENCY_QUERY_THRESHOLD = 1000
    LARGE_RESULT_THRESHOLD = 10000
    CONNECTION_POOL_SIZE = 20
    MAX_OVERFLOW = 30
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600

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
            self.engine = create_async_engine(self.database_url, pool_size=self.CONNECTION_POOL_SIZE, max_overflow=self.MAX_OVERFLOW, pool_timeout=self.POOL_TIMEOUT, pool_recycle=self.POOL_RECYCLE, echo=False)
            self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        except Exception as e:
            logger.exception("Failed to initialize database optimizer: %s", e)

    async def track_query(self, query: str, duration_ms: float, rows_returned: int=0):
        """Track query performance for optimization analysis"""
        if not self.redis_client:
            return
        query_hash = self._normalize_query(query)
        QueryMetrics(query_hash=query_hash, execution_count=1, avg_duration=duration_ms, total_duration=duration_ms, rows_returned=rows_returned, timestamp=datetime.now(UTC), is_slow=duration_ms > self.SLOW_QUERY_THRESHOLD)
        hour_key = f"{self.query_metrics_key}{datetime.now(UTC).strftime('%Y%m%d%H')}"
        try:
            pipe = self.redis_client.pipeline()
            pipe.hincrby(hour_key, f"{query_hash}:count", 1)
            pipe.hincrbyfloat(hour_key, f"{query_hash}:total_duration", duration_ms)
            pipe.hincrby(hour_key, f"{query_hash}:rows", rows_returned)
            pipe.hset(hour_key, f"{query_hash}:query", query[:500])
            pipe.hset(hour_key, f"{query_hash}:last_seen", datetime.now(UTC).isoformat())
            if duration_ms > self.SLOW_QUERY_THRESHOLD:
                pipe.hset(hour_key, f"{query_hash}:slow", "1")
            pipe.expire(hour_key, 24 * 3600)
            await pipe.execute()
        except Exception as e:
            logger.exception("Error tracking query metrics: %s", e)

    async def analyze_slow_queries(self, hours: int=24) -> list[dict[str, Any]]:
        """Analyze slow queries and provide optimization recommendations"""
        if not self.redis_client:
            return []
        slow_queries = []
        now = datetime.now(UTC)
        for i in range(hours):
            hour_key = f"{self.query_metrics_key}{(now - timedelta(hours=i)).strftime('%Y%m%d%H')}"
            try:
                query_data = await self.redis_client.hgetall(hour_key)
                for key, value in query_data.items():
                    if key.endswith(":slow") and value == "1":
                        query_hash = key.replace(":slow", "")
                        count = int(await self.redis_client.hget(hour_key, f"{query_hash}:count") or 0)
                        total_duration = float(await self.redis_client.hget(hour_key, f"{query_hash}:total_duration") or 0)
                        rows = int(await self.redis_client.hget(hour_key, f"{query_hash}:rows") or 0)
                        query_sample = await self.redis_client.hget(hour_key, f"{query_hash}:query") or ""
                        avg_duration = total_duration / count if count > 0 else 0
                        slow_queries.append({"query": query_sample, "query_hash": query_hash, "execution_count": count, "avg_duration_ms": avg_duration, "total_duration_ms": total_duration, "rows_returned": rows, "hour": (now - timedelta(hours=i)).strftime("%Y-%m-%d %H:00"), "optimization_suggestions": self._suggest_query_optimization(query_sample, avg_duration, rows)})
            except Exception as e:
                logger.exception("Error analyzing slow queries for hour %s: %s", i, e)
        slow_queries.sort(key=lambda x: x["avg_duration_ms"], reverse=True)
        return slow_queries[:20]

    async def analyze_table_metrics(self, db: AsyncSession) -> list[TableMetrics]:
        """Analyze table-level metrics for optimization opportunities"""
        table_metrics = []
        try:
            tables_query = "\n            SELECT\n                schemaname || '.' || tablename as table_name,\n                n_tup_ins as inserts,\n                n_tup_upd as updates,\n                n_tup_del as deletes,\n                n_live_tup as live_rows,\n                n_dead_tup as dead_rows,\n                last_vacuum,\n                last_analyze,\n                vacuum_count,\n                autovacuum_count\n            FROM pg_stat_user_tables\n            ORDER BY n_live_tup DESC\n            "
            result = await db.execute(text(tables_query))
            table_stats = result.fetchall()
            for stat in table_stats:
                table_name = stat.table_name
                size_query = f"\n                SELECT pg_total_relation_size('{table_name}') as size_bytes\n                "
                size_result = await db.execute(text(size_query))
                size_bytes = size_result.scalar() or 0
                index_query = f"\n                SELECT\n                    indexname,\n                    idx_scan as scans,\n                    idx_tup_read as tuples_read,\n                    idx_tup_fetch as tuples_fetched\n                FROM pg_stat_user_indexes\n                WHERE schemaname || '.' || tablename = '{table_name}'\n                "
                index_result = await db.execute(text(index_query))
                index_stats = index_result.fetchall()
                unused_indexes = [idx.indexname for idx in index_stats if idx.scans == 0 and (not idx.indexname.startswith("pg_"))]
                metrics = TableMetrics(table_name=table_name, row_count=stat.live_rows or 0, size_bytes=size_bytes, index_count=len(index_stats), unused_indexes=unused_indexes, last_analyzed=stat.last_analyze or datetime.min.replace(tzinfo=UTC))
                table_metrics.append(metrics)
        except Exception as e:
            logger.exception("Error analyzing table metrics: %s", e)
        return table_metrics

    async def generate_optimization_recommendations(self, db: AsyncSession) -> dict[str, Any]:
        """Generate comprehensive database optimization recommendations"""
        recommendations = {"query_optimizations": [], "index_optimizations": [], "table_optimizations": [], "connection_optimizations": [], "storage_optimizations": []}
        slow_queries = await self.analyze_slow_queries()
        for query in slow_queries:
            if query["avg_duration_ms"] > 500:
                recommendations["query_optimizations"].append({"type": "critical", "query": query["query"][:100] + "...", "issue": f"Very slow query ({query['avg_duration_ms']:.1f}ms avg)", "suggestion": query["optimization_suggestions"][0] if query["optimization_suggestions"] else "Consider query optimization"})
        table_metrics = await self.analyze_table_metrics(db)
        for table in table_metrics:
            if table.unused_indexes:
                recommendations["index_optimizations"].append({"type": "unused_indexes", "table": table.table_name, "indexes": table.unused_indexes, "suggestion": f"Remove {len(table.unused_indexes)} unused indexes to save storage and improve write performance"})
            if table.row_count > 100000 and table.index_count < 3:
                recommendations["index_optimizations"].append({"type": "missing_indexes", "table": table.table_name, "rows": table.row_count, "suggestion": "Consider adding indexes for frequently queried columns"})
            if table.size_bytes > 100 * 1024 * 1024:
                recommendations["storage_optimizations"].append({"type": "large_table", "table": table.table_name, "size_mb": table.size_bytes / (1024 * 1024), "suggestion": "Consider table partitioning or archiving old data"})
        recommendations["connection_optimizations"] = [{"type": "pool_size", "current": self.CONNECTION_POOL_SIZE, "suggestion": "Monitor connection pool utilization and adjust based on load"}, {"type": "timeout", "current": self.POOL_TIMEOUT, "suggestion": "Consider increasing timeout if experiencing connection timeouts"}]
        return recommendations

    def _normalize_query(self, query: str) -> str:
        """Normalize SQL query for consistent hashing"""
        normalized = " ".join(query.split()).lower()
        import re
        normalized = re.sub("'[^']*'", "'?'", normalized)
        return re.sub("\\b\\d+\\b", "?", normalized)

    def _suggest_query_optimization(self, query: str, duration_ms: float, rows: int) -> list[str]:
        """Suggest optimizations for a specific query"""
        suggestions = []
        query_lower = query.lower()
        if "select" in query_lower and "where" not in query_lower and (rows > 1000):
            suggestions.append("Add WHERE clause to limit result set")
        if "select" in query_lower and "limit" not in query_lower and (rows > 1000):
            suggestions.append("Add LIMIT clause to prevent large result sets")
        if "join" in query_lower and duration_ms > 200:
            suggestions.append("Consider adding indexes on JOIN columns")
        if "order by" in query_lower and duration_ms > 200:
            suggestions.append("Add index on ORDER BY columns")
        if duration_ms > 500:
            suggestions.append("Query is very slow - consider EXPLAIN ANALYZE for detailed analysis")
        return suggestions

    async def implement_optimizations(self, db: AsyncSession, recommendations: dict[str, Any]):
        """Implement safe database optimizations"""
        implemented = []
        for opt in recommendations.get("index_optimizations", []):
            if opt["type"] == "unused_indexes" and len(opt["indexes"]) <= 2:
                try:
                    for index_name in opt["indexes"]:
                        drop_sql = f"DROP INDEX IF EXISTS {index_name}"
                        await db.execute(text(drop_sql))
                        implemented.append(f"Dropped unused index: {index_name}")
                except Exception as e:
                    logger.exception("Failed to drop index %s: %s", opt["indexes"], e)
        await db.commit()
        return implemented

    async def get_cost_savings_estimate(self, recommendations: dict[str, Any]) -> dict[str, Any]:
        """Estimate potential cost savings from optimizations"""
        savings = {"query_time_reduction_ms": 0, "storage_reduction_mb": 0, "estimated_monthly_savings_usd": 0.0}
        for opt in recommendations.get("query_optimizations", []):
            if opt["type"] == "critical":
                savings["query_time_reduction_ms"] += 400
        for opt in recommendations.get("index_optimizations", []):
            if opt["type"] == "unused_indexes":
                savings["storage_reduction_mb"] += len(opt["indexes"]) * 10
        storage_savings = savings["storage_reduction_mb"] / 1024 * 0.1
        query_savings = savings["query_time_reduction_ms"] / 1000 * 0.5
        savings["estimated_monthly_savings_usd"] = (storage_savings + query_savings) * 30
        return savings
db_optimizer = None

def db_performance_monitor(func):
    """Decorator to monitor database query performance"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not db_optimizer:
            return await func(*args, **kwargs)
        start_time = datetime.now(UTC)
        try:
            result = await func(*args, **kwargs)
            duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
            rows_returned = 0
            if hasattr(result, "rowcount"):
                rows_returned = result.rowcount
            elif isinstance(result, list):
                rows_returned = len(result)
            await db_optimizer.track_query(query=func.__name__, duration_ms=duration_ms, rows_returned=rows_returned)
            return result
        except Exception as e:
            logger.exception("Database function failed: %s", e)
            raise
    return wrapper

async def initialize_database_optimizer(database_url: str):
    """Initialize the database optimizer"""
    global db_optimizer
    db_optimizer = DatabaseOptimizer(database_url)
    await db_optimizer.initialize()
    logger.info("Database optimizer initialized")

async def get_database_optimization_report(db: AsyncSession) -> dict[str, Any]:
    """Generate comprehensive database optimization report"""
    if not db_optimizer:
        return {"error": "Database optimizer not initialized"}
    recommendations = await db_optimizer.generate_optimization_recommendations(db)
    cost_savings = await db_optimizer.get_cost_savings_estimate(recommendations)
    return {"recommendations": recommendations, "cost_savings_estimate": cost_savings, "timestamp": datetime.now(UTC).isoformat()}
