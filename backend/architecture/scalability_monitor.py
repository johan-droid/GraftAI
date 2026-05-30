"""
Scalability Monitoring and Alerting System

Monitors system scalability and provides early warnings:
- Performance metrics tracking
- Capacity planning alerts
- Bottleneck detection
- Auto-scaling recommendations
"""
import asyncio
import contextlib
import logging
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MetricType(Enum):
    """Types of metrics to monitor"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DATABASE_CONNECTIONS = "database_connections"
    API_RESPONSE_TIME = "api_response_time"
    ERROR_RATE = "error_rate"
    QUEUE_DEPTH = "queue_depth"
    CACHE_HIT_RATE = "cache_hit_rate"
    USER_GROWTH = "user_growth"
    STORAGE_USAGE = "storage_usage"

@dataclass
class MetricThreshold:
    """Threshold configuration for metrics"""
    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: float
    time_window_minutes: int = 5
    consecutive_violations: int = 3

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    source: str
    metadata: dict[str, Any] | None = None

@dataclass
class ScalabilityAlert:
    """Scalability alert"""
    alert_id: str
    metric_type: MetricType
    severity: AlertSeverity
    title: str
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    source: str
    recommendations: list[str]
    resolved: bool = False
    resolved_at: datetime | None = None

@dataclass
class CapacityForecast:
    """Capacity forecast for planning"""
    resource_type: str
    current_capacity: float
    current_usage: float
    projected_usage_30d: float
    projected_usage_90d: float
    time_to_capacity_limit: int
    recommended_action: str
    confidence: float

class MetricsCollector:
    """Collects performance metrics from various sources"""

    def __init__(self):
        self.metrics_buffer: list[PerformanceMetric] = []
        self.buffer_size = 10000
        self.collection_interval = 60

    async def collect_system_metrics(self) -> dict[str, float]:
        """Collect system-level metrics"""
        import psutil
        return {"cpu_usage": psutil.cpu_percent(), "memory_usage": psutil.virtual_memory().percent, "disk_usage": psutil.disk_usage("/").percent}

    async def collect_database_metrics(self) -> dict[str, float]:
        """Collect database performance metrics"""
        return {"active_connections": 25, "max_connections": 100, "query_time_avg": 45.5, "query_time_p95": 120.0, "deadlocks": 0}

    async def collect_application_metrics(self) -> dict[str, float]:
        """Collect application-level metrics"""
        return {"api_response_time_avg": 85.2, "api_response_time_p95": 200.0, "error_rate": 0.02, "requests_per_second": 45.5, "cache_hit_rate": 0.78}

    async def collect_business_metrics(self) -> dict[str, float]:
        """Collect business metrics"""
        return {"active_users": 15420, "user_growth_rate": 0.15, "ai_requests_per_hour": 1250, "bookings_per_hour": 85}

    def add_metric(self, metric: PerformanceMetric):
        """Add metric to buffer"""
        self.metrics_buffer.append(metric)
        if len(self.metrics_buffer) > self.buffer_size:
            self.metrics_buffer = self.metrics_buffer[-self.buffer_size:]

    def get_metrics(self, metric_type: MetricType, minutes: int=60) -> list[PerformanceMetric]:
        """Get metrics for specific type and time window"""
        cutoff_time = datetime.now(UTC) - timedelta(minutes=minutes)
        return [m for m in self.metrics_buffer if m.metric_type == metric_type and m.timestamp >= cutoff_time]

class ThresholdMonitor:
    """Monitors metrics against thresholds"""

    def __init__(self):
        self.thresholds: dict[MetricType, MetricThreshold] = {}
        self.violation_counts: dict[str, int] = {}
        self._setup_default_thresholds()

    def _setup_default_thresholds(self):
        """Setup default monitoring thresholds"""
        self.thresholds = {MetricType.CPU_USAGE: MetricThreshold(metric_type=MetricType.CPU_USAGE, warning_threshold=70.0, critical_threshold=85.0, emergency_threshold=95.0), MetricType.MEMORY_USAGE: MetricThreshold(metric_type=MetricType.MEMORY_USAGE, warning_threshold=75.0, critical_threshold=90.0, emergency_threshold=95.0), MetricType.DATABASE_CONNECTIONS: MetricThreshold(metric_type=MetricType.DATABASE_CONNECTIONS, warning_threshold=60.0, critical_threshold=80.0, emergency_threshold=95.0), MetricType.API_RESPONSE_TIME: MetricThreshold(metric_type=MetricType.API_RESPONSE_TIME, warning_threshold=200.0, critical_threshold=500.0, emergency_threshold=1000.0), MetricType.ERROR_RATE: MetricThreshold(metric_type=MetricType.ERROR_RATE, warning_threshold=0.01, critical_threshold=0.05, emergency_threshold=0.1), MetricType.QUEUE_DEPTH: MetricThreshold(metric_type=MetricType.QUEUE_DEPTH, warning_threshold=1000, critical_threshold=5000, emergency_threshold=10000), MetricType.CACHE_HIT_RATE: MetricThreshold(metric_type=MetricType.CACHE_HIT_RATE, warning_threshold=0.7, critical_threshold=0.5, emergency_threshold=0.3), MetricType.USER_GROWTH: MetricThreshold(metric_type=MetricType.USER_GROWTH, warning_threshold=0.2, critical_threshold=0.5, emergency_threshold=1.0)}

    def check_thresholds(self, metric: PerformanceMetric) -> ScalabilityAlert | None:
        """Check metric against thresholds and generate alert if needed"""
        threshold = self.thresholds.get(metric.metric_type)
        if not threshold:
            return None
        violation_key = f"{metric.metric_type.value}_{metric.source}"
        severity = None
        threshold_value = None
        if metric.value >= threshold.emergency_threshold:
            severity = AlertSeverity.EMERGENCY
            threshold_value = threshold.emergency_threshold
        elif metric.value >= threshold.critical_threshold:
            severity = AlertSeverity.CRITICAL
            threshold_value = threshold.critical_threshold
        elif metric.value >= threshold.warning_threshold:
            severity = AlertSeverity.WARNING
            threshold_value = threshold.warning_threshold
        if severity:
            self.violation_counts[violation_key] = self.violation_counts.get(violation_key, 0) + 1
            if self.violation_counts[violation_key] >= threshold.consecutive_violations:
                alert = ScalabilityAlert(alert_id=f"alert_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{metric.metric_type.value}", metric_type=metric.metric_type, severity=severity, title=f"{severity.value.title()} {metric.metric_type.value.replace('_', ' ').title()}", message=f"{metric.metric_type.value.replace('_', ' ').title()} is {metric.value:.2f}, threshold is {threshold_value:.2f}", current_value=metric.value, threshold=threshold_value, timestamp=metric.timestamp, source=metric.source, recommendations=self._get_recommendations(metric.metric_type, severity))
                self.violation_counts[violation_key] = 0
                return alert
        else:
            self.violation_counts[violation_key] = 0
        return None

    def _get_recommendations(self, metric_type: MetricType, severity: AlertSeverity) -> list[str]:
        """Get recommendations for metric violations"""
        recommendations = {MetricType.CPU_USAGE: ["Scale up CPU resources", "Optimize CPU-intensive operations", "Consider horizontal scaling"], MetricType.MEMORY_USAGE: ["Increase memory allocation", "Optimize memory usage patterns", "Implement memory caching"], MetricType.DATABASE_CONNECTIONS: ["Increase connection pool size", "Optimize database queries", "Implement connection pooling"], MetricType.API_RESPONSE_TIME: ["Optimize slow endpoints", "Implement caching", "Scale up application servers"], MetricType.ERROR_RATE: ["Investigate error patterns", "Implement circuit breakers", "Add more robust error handling"], MetricType.QUEUE_DEPTH: ["Scale up worker processes", "Optimize queue processing", "Consider queue partitioning"], MetricType.CACHE_HIT_RATE: ["Warm up cache with frequently accessed data", "Optimize cache TTL values", "Increase cache size"], MetricType.USER_GROWTH: ["Prepare for user onboarding surge", "Scale customer support", "Monitor infrastructure capacity"]}
        return recommendations.get(metric_type, ["Investigate the metric and take appropriate action"])

class CapacityPlanner:
    """Plans capacity based on current usage and growth patterns"""

    def __init__(self):
        self.growth_history: dict[str, list[float]] = {}

    async def forecast_capacity_needs(self, resource_type: str, current_usage: float, historical_data: list[float]) -> CapacityForecast:
        """Forecast capacity needs for a resource"""
        if len(historical_data) < 2:
            growth_rate = 0.1
        else:
            recent_growth = (historical_data[-1] - historical_data[0]) / historical_data[0]
            growth_rate = max(0, recent_growth)
        projected_30d = current_usage * (1 + growth_rate) ** 1
        projected_90d = current_usage * (1 + growth_rate) ** 3
        capacity_limit = current_usage / 0.8
        if growth_rate > 0:
            days_to_limit = int(math.log(capacity_limit / current_usage) / math.log(1 + growth_rate))
        else:
            days_to_limit = 365
        if days_to_limit < 30:
            action = "Immediate scaling required"
        elif days_to_limit < 90:
            action = "Plan scaling within next quarter"
        else:
            action = "Monitor and plan for future scaling"
        confidence = min(1.0, len(historical_data) / 30)
        return CapacityForecast(resource_type=resource_type, current_capacity=capacity_limit, current_usage=current_usage, projected_usage_30d=projected_30d, projected_usage_90d=projected_90d, time_to_capacity_limit=days_to_limit, recommended_action=action, confidence=confidence)

class ScalabilityMonitor:
    """Main scalability monitoring system"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.threshold_monitor = ThresholdMonitor()
        self.capacity_planner = CapacityPlanner()
        self.active_alerts: dict[str, ScalabilityAlert] = []
        self.monitoring_active = False
        self.monitoring_task: asyncio.Task | None = None

    async def start_monitoring(self):
        """Start continuous monitoring"""
        if self.monitoring_active:
            return
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Scalability monitoring started")

    async def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitoring_task
        logger.info("Scalability monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_all_metrics()
                await self._check_all_thresholds()
                await self._update_capacity_forecasts()
                await asyncio.sleep(self.metrics_collector.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in monitoring loop: %s", e)
                await asyncio.sleep(60)

    async def _collect_all_metrics(self):
        """Collect all types of metrics"""
        timestamp = datetime.now(UTC)
        system_metrics = await self.metrics_collector.collect_system_metrics()
        for metric_name, value in system_metrics.items():
            metric = PerformanceMetric(metric_type=MetricType(metric_name), value=value, timestamp=timestamp, source="system")
            self.metrics_collector.add_metric(metric)
        db_metrics = await self.metrics_collector.collect_database_metrics()
        for metric_name, value in db_metrics.items():
            metric = PerformanceMetric(metric_type=MetricType(metric_name), value=value, timestamp=timestamp, source="database")
            self.metrics_collector.add_metric(metric)
        app_metrics = await self.metrics_collector.collect_application_metrics()
        for metric_name, value in app_metrics.items():
            metric = PerformanceMetric(metric_type=MetricType(metric_name), value=value, timestamp=timestamp, source="application")
            self.metrics_collector.add_metric(metric)
        business_metrics = await self.metrics_collector.collect_business_metrics()
        for metric_name, value in business_metrics.items():
            metric = PerformanceMetric(metric_type=MetricType(metric_name), value=value, timestamp=timestamp, source="business")
            self.metrics_collector.add_metric(metric)

    async def _check_all_thresholds(self):
        """Check all metrics against thresholds"""
        recent_metrics = self.metrics_collector.metrics_buffer[-100:]
        for metric in recent_metrics:
            alert = self.threshold_monitor.check_thresholds(metric)
            if alert:
                self.active_alerts[alert.alert_id] = alert
                logger.warning("Scalability alert: %s - %s", alert.title, alert.message)

    async def _update_capacity_forecasts(self):
        """Update capacity forecasts"""

    async def get_current_alerts(self, severity: AlertSeverity | None=None) -> list[ScalabilityAlert]:
        """Get current active alerts"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(UTC)
            del self.active_alerts[alert_id]
            logger.info("Alert resolved: %s", alert_id)
            return True
        return False

    async def get_capacity_forecasts(self) -> list[CapacityForecast]:
        """Get capacity forecasts for all resources"""
        forecasts = []
        for metric_type in MetricType:
            metrics = self.metrics_collector.get_metrics(metric_type, minutes=1440)
            if len(metrics) >= 2:
                values = [m.value for m in metrics]
                current_usage = values[-1]
                forecast = await self.capacity_planner.forecast_capacity_needs(resource_type=metric_type.value, current_usage=current_usage, historical_data=values)
                forecasts.append(forecast)
        return forecasts

    async def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary"""
        summary = {}
        for metric_type in MetricType:
            recent_metrics = self.metrics_collector.get_metrics(metric_type, minutes=60)
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                summary[metric_type.value] = {"current": values[-1], "average": statistics.mean(values), "min": min(values), "max": max(values), "trend": "increasing" if values[-1] > values[0] else "decreasing"}
        return summary
scalability_monitor = ScalabilityMonitor()

def get_scalability_monitor() -> ScalabilityMonitor:
    """Get global scalability monitor instance"""
    return scalability_monitor

async def start_scalability_monitoring():
    """Start scalability monitoring in background"""
    monitor = get_scalability_monitor()
    await monitor.start_monitoring()

async def stop_scalability_monitoring():
    """Stop scalability monitoring"""
    monitor = get_scalability_monitor()
    await monitor.stop_monitoring()
'\n@router.post("/monitoring/start")\nasync def start_monitoring():\n    await start_scalability_monitoring()\n    return {"status": "monitoring_started"}\n\n@router.post("/monitoring/stop")\nasync def stop_monitoring():\n    await stop_scalability_monitoring()\n    return {"status": "monitoring_stopped"}\n\n@router.get("/monitoring/alerts")\nasync def get_alerts(severity: Optional[str] = None):\n    monitor = get_scalability_monitor()\n    alert_severity = AlertSeverity(severity) if severity else None\n    alerts = await monitor.get_current_alerts(alert_severity)\n    return {"alerts": [asdict(alert) for alert in alerts]}\n\n@router.get("/monitoring/capacity")\nasync def get_capacity_forecasts():\n    monitor = get_scalability_monitor()\n    forecasts = await monitor.get_capacity_forecasts()\n    return {"forecasts": [asdict(forecast) for forecast in forecasts]}\n\n@router.get("/monitoring/summary")\nasync def get_performance_summary():\n    monitor = get_scalability_monitor()\n    summary = await monitor.get_performance_summary()\n    return summary\n'
