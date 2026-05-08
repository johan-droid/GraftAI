"""
Comprehensive Health Checks and Metrics System

Provides system health monitoring with:
- Component health checks
- Performance metrics collection
- Service dependency monitoring
- Alerting and notifications
- Health dashboard data
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from collections import deque
import aiohttp
import aioredis

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Dict[str, Any] = None
    tags: List[str] = None


@dataclass
class ComponentHealth:
    """Component health summary"""
    component_name: str
    overall_status: HealthStatus
    checks: List[HealthCheck]
    last_updated: datetime
    uptime_percentage: float = 100.0


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    request_rate: float
    error_rate: float
    response_time_p95: float
    cache_hit_rate: float


class HealthChecker:
    """Base class for health checkers"""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self.last_check: Optional[HealthCheck] = None
    
    async def check_health(self) -> HealthCheck:
        """Perform health check"""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        
        try:
            result = await self._perform_check()
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name=self.name,
                status=result["status"],
                message=result["message"],
                response_time_ms=response_time,
                timestamp=timestamp,
                details=result.get("details", {}),
                tags=result.get("tags", [])
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=timestamp,
                details={"error": str(e)},
                tags=["error"]
            )
    
    @abstractmethod
    async def _perform_check(self) -> Dict[str, Any]:
        """Perform actual health check"""
        pass


class DatabaseHealthChecker(HealthChecker):
    """Database health checker"""
    
    def __init__(self, db_session_factory, timeout: float = 5.0):
        super().__init__("database", timeout)
        self.db_session_factory = db_session_factory
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            async with self.db_session_factory() as db:
                # Test basic connectivity
                result = await db.execute("SELECT 1")
                await result.fetchone()
                
                # Check connection pool
                pool = db.bind.pool
                pool_status = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow()
                }
                
                # Check table counts
                user_count = await db.execute("SELECT COUNT(*) FROM users")
                booking_count = await db.execute("SELECT COUNT(*) FROM bookings")
                
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "Database is healthy",
                    "details": {
                        "connection_pool": pool_status,
                        "tables": {
                            "users": user_count.scalar(),
                            "bookings": booking_count.scalar()
                        }
                    },
                    "tags": ["database", "connectivity"]
                }
                
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database connection failed: {str(e)}",
                "details": {"error": str(e)},
                "tags": ["database", "error"]
            }


class RedisHealthChecker(HealthChecker):
    """Redis health checker"""
    
    def __init__(self, redis_client: aioredis.Redis, timeout: float = 5.0):
        super().__init__("redis", timeout)
        self.redis_client = redis_client
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            # Test connectivity
            await self.redis_client.ping()
            
            # Test basic operations
            test_key = "health_check_test"
            await self.redis_client.set(test_key, "test_value", ex=10)
            value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            if value != "test_value":
                raise ValueError("Redis read/write test failed")
            
            # Get Redis info
            info = await self.redis_client.info()
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Redis is healthy",
                "details": {
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                },
                "tags": ["redis", "cache"]
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Redis connection failed: {str(e)}",
                "details": {"error": str(e)},
                "tags": ["redis", "error"]
            }


class ExternalAPIHealthChecker(HealthChecker):
    """External API health checker"""
    
    def __init__(self, api_name: str, api_url: str, timeout: float = 5.0):
        super().__init__(f"external_api_{api_name}", timeout)
        self.api_url = api_url
        self.api_name = api_name
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check external API health"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.api_url) as response:
                    if response.status == 200:
                        return {
                            "status": HealthStatus.HEALTHY,
                            "message": f"{self.api_name} API is healthy",
                            "details": {
                                "status_code": response.status,
                                "response_time": response.headers.get("X-Response-Time", "unknown")
                            },
                            "tags": ["external_api", self.api_name]
                        }
                    else:
                        return {
                            "status": HealthStatus.DEGRADED,
                            "message": f"{self.api_name} API returned status {response.status}",
                            "details": {"status_code": response.status},
                            "tags": ["external_api", self.api_name, "degraded"]
                        }
                        
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"{self.api_name} API check failed: {str(e)}",
                "details": {"error": str(e)},
                "tags": ["external_api", self.api_name, "error"]
            }


class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 data points
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.timers: Dict[str, List[float]] = {}
        self.collection_interval = 60  # seconds
        self.collection_task: Optional[asyncio.Task] = None
    
    async def start_collection(self):
        """Start metrics collection"""
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collection stopped")
    
    async def _collection_loop(self):
        """Main metrics collection loop"""
        while True:
            try:
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics"""
        timestamp = datetime.now(timezone.utc)
        
        # CPU metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Application metrics (would be collected from actual application)
        active_connections = len(psutil.net_connections())
        request_rate = self.counters.get("requests_per_minute", 0)
        error_rate = self.counters.get("errors_per_minute", 0)
        response_time_p95 = self._calculate_percentile("response_times", 95)
        cache_hit_rate = self._calculate_cache_hit_rate()
        
        return SystemMetrics(
            timestamp=timestamp,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            active_connections=active_connections,
            request_rate=request_rate,
            error_rate=error_rate,
            response_time_p95=response_time_p95,
            cache_hit_rate=cache_hit_rate
        )
    
    def _calculate_percentile(self, metric_name: str, percentile: float) -> float:
        """Calculate percentile for metric"""
        if metric_name not in self.histograms:
            return 0.0
        
        values = self.histograms[metric_name]
        if not values:
            return 0.0
        
        values.sort()
        index = int(len(values) * (percentile / 100))
        return values[min(index, len(values) - 1)]
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        hits = self.counters.get("cache_hits", 0)
        misses = self.counters.get("cache_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return (hits / total) * 100
    
    def increment_counter(self, name: str, value: float = 1.0):
        """Increment counter metric"""
        self.counters[name] = self.counters.get(name, 0) + value
    
    def set_gauge(self, name: str, value: float):
        """Set gauge metric"""
        self.gauges[name] = value
    
    def record_histogram(self, name: str, value: float):
        """Record histogram metric"""
        if name not in self.histograms:
            self.histograms[name] = []
        
        self.histograms[name].append(value)
        
        # Keep only last 1000 values
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]
    
    def record_timer(self, name: str, duration_ms: float):
        """Record timer metric"""
        if name not in self.timers:
            self.timers[name] = []
        
        self.timers[name].append(duration_ms)
        
        # Keep only last 1000 values
        if len(self.timers[name]) > 1000:
            self.timers[name] = self.timers[name][-1000:]
    
    def get_metrics_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get metrics summary for time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No metrics available"}
        
        # Calculate averages and percentiles
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_usage for m in recent_metrics]
        response_times = [m.response_time_p95 for m in recent_metrics]
        
        return {
            "time_window_minutes": minutes,
            "data_points": len(recent_metrics),
            "cpu": {
                "avg": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "response_time_p95": {
                "avg": statistics.mean(response_times),
                "max": max(response_times),
                "min": min(response_times)
            },
            "current_counters": self.counters.copy(),
            "current_gauges": self.gauges.copy()
        }


class HealthMonitor:
    """Main health monitoring system"""
    
    def __init__(self):
        self.health_checkers: Dict[str, HealthChecker] = {}
        self.component_health: Dict[str, ComponentHealth] = {}
        self.metrics_collector = MetricsCollector()
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.health_history: deque = deque(maxlen=100)
        self.alert_callbacks: List[Callable] = []
    
    def register_health_checker(self, checker: HealthChecker):
        """Register a health checker"""
        self.health_checkers[checker.name] = checker
        logger.info(f"Registered health checker: {checker.name}")
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start health monitoring"""
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        await self.metrics_collector.start_collection()
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        await self.metrics_collector.stop_collection()
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_checks(self):
        """Perform all health checks"""
        timestamp = datetime.now(timezone.utc)
        
        for checker_name, checker in self.health_checkers.items():
            try:
                health_check = await checker.check_health()
                
                # Update component health
                if checker_name not in self.component_health:
                    self.component_health[checker_name] = ComponentHealth(
                        component_name=checker_name,
                        overall_status=health_check.status,
                        checks=[],
                        last_updated=timestamp
                    )
                
                component = self.component_health[checker_name]
                component.checks.append(health_check)
                component.last_updated = timestamp
                
                # Update overall status
                component.overall_status = self._calculate_overall_status(component.checks)
                
                # Calculate uptime
                component.uptime_percentage = self._calculate_uptime_percentage(component.checks)
                
                # Keep only last 10 checks
                if len(component.checks) > 10:
                    component.checks = component.checks[-10:]
                
                # Check for alerts
                await self._check_for_alerts(checker_name, health_check)
                
            except Exception as e:
                logger.error(f"Error performing health check for {checker_name}: {e}")
    
    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calculate overall status from checks"""
        if not checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in checks]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif HealthStatus.HEALTHY in statuses:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _calculate_uptime_percentage(self, checks: List[HealthCheck]) -> float:
        """Calculate uptime percentage from checks"""
        if not checks:
            return 100.0
        
        healthy_checks = len([c for c in checks if c.status == HealthStatus.HEALTHY])
        return (healthy_checks / len(checks)) * 100
    
    async def _check_for_alerts(self, component_name: str, health_check: HealthCheck):
        """Check if alerts should be triggered"""
        # Alert on unhealthy status
        if health_check.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
            alert_data = {
                "type": "health_check_failure",
                "component": component_name,
                "status": health_check.status.value,
                "message": health_check.message,
                "timestamp": health_check.timestamp.isoformat()
            }
            
            await self._trigger_alert(alert_data)
        
        # Alert on slow response times
        if health_check.response_time_ms > 5000:  # 5 seconds
            alert_data = {
                "type": "slow_response",
                "component": component_name,
                "response_time_ms": health_check.response_time_ms,
                "timestamp": health_check.timestamp.isoformat()
            }
            
            await self._trigger_alert(alert_data)
    
    async def _trigger_alert(self, alert_data: Dict[str, Any]):
        """Trigger alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        overall_status = HealthStatus.HEALTHY
        
        component_statuses = {}
        for name, component in self.component_health.items():
            component_statuses[name] = {
                "status": component.overall_status.value,
                "uptime_percentage": component.uptime_percentage,
                "last_updated": component.last_updated.isoformat(),
                "checks": [
                    {
                        "name": check.name,
                        "status": check.status.value,
                        "message": check.message,
                        "response_time_ms": check.response_time_ms,
                        "timestamp": check.timestamp.isoformat(),
                        "details": check.details,
                        "tags": check.tags
                    }
                    for check in component.checks
                ]
            }
            
            # Determine overall status
            if component.overall_status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
            elif component.overall_status == HealthStatus.UNHEALTHY and overall_status != HealthStatus.CRITICAL:
                overall_status = HealthStatus.UNHEALTHY
            elif component.overall_status == HealthStatus.DEGRADED and overall_status in [HealthStatus.HEALTHY]:
                overall_status = HealthStatus.DEGRADED
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": component_statuses,
            "summary": {
                "total_components": len(self.component_health),
                "healthy": len([c for c in self.component_health.values() if c.overall_status == HealthStatus.HEALTHY]),
                "degraded": len([c for c in self.component_health.values() if c.overall_status == HealthStatus.DEGRADED]),
                "unhealthy": len([c for c in self.component_health.values() if c.overall_status == HealthStatus.UNHEALTHY]),
                "critical": len([c for c in self.component_health.values() if c.overall_status == HealthStatus.CRITICAL])
            }
        }
    
    async def get_system_metrics(self, minutes: int = 5) -> Dict[str, Any]:
        """Get system metrics"""
        return self.metrics_collector.get_metrics_summary(minutes)
    
    async def get_health_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive health dashboard data"""
        health_status = await self.get_health_status()
        system_metrics = await self.get_system_metrics()
        
        return {
            "health": health_status,
            "metrics": system_metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global health monitor
health_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance"""
    return health_monitor


# Alert callback example
async def console_alert_callback(alert_data: Dict[str, Any]):
    """Console alert callback"""
    logger.warning(f"ALERT: {alert_data}")


# Initialize health monitor with default checkers
async def initialize_health_monitoring(db_session_factory, redis_client: aioredis.Redis):
    """Initialize health monitoring system"""
    monitor = get_health_monitor()
    
    # Add alert callback
    monitor.add_alert_callback(console_alert_callback)
    
    # Register database health checker
    db_checker = DatabaseHealthChecker(db_session_factory)
    monitor.register_health_checker(db_checker)
    
    # Register Redis health checker
    redis_checker = RedisHealthChecker(redis_client)
    monitor.register_health_checker(redis_checker)
    
    # Register external API health checkers
    # Example: Groq API
    groq_checker = ExternalAPIHealthChecker("groq", "https://api.groq.com/health")
    monitor.register_health_checker(groq_checker)
    
    # Example: OpenAI API
    openai_checker = ExternalAPIHealthChecker("openai", "https://api.openai.com/v1/health")
    monitor.register_health_checker(openai_checker)
    
    logger.info("Health monitoring system initialized")
    return monitor
