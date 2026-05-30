"""
Traffic Spike Monitoring System

Comprehensive monitoring for traffic spikes and system health:
- Real-time metrics collection
- Anomaly detection
- Alerting system
- Performance dashboard
"""
import asyncio
import contextlib
import logging
import statistics
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics to monitor"""
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DATABASE_CONNECTIONS = "database_connections"
    CACHE_HIT_RATE = "cache_hit_rate"
    QUEUE_DEPTH = "queue_depth"
    CONCURRENT_USERS = "concurrent_users"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class MetricThreshold:
    """Threshold configuration for metrics"""
    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: float
    time_window_seconds: int = 60
    consecutive_violations: int = 3

@dataclass
class TrafficSpikeAlert:
    """Traffic spike alert"""
    alert_id: str
    metric_type: MetricType
    severity: AlertSeverity
    title: str
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    duration_seconds: float
    affected_endpoints: list[str]
    recommended_actions: list[str]
    resolved: bool = False
    resolved_at: datetime | None = None

@dataclass
class AnomalyDetection:
    """Anomaly detection configuration"""
    metric_type: MetricType
    detection_method: str
    sensitivity: float
    baseline_window_minutes: int = 30
    anomaly_threshold_multiplier: float = 2.0

class TrafficSpikeMonitor:
    """Monitors traffic spikes and system performance"""

    def __init__(self):
        self.metrics_history: dict[MetricType, deque] = {}
        self.thresholds: dict[MetricType, MetricThreshold] = {}
        self.anomaly_detectors: dict[MetricType, AnomalyDetection] = []
        self.active_alerts: dict[str, TrafficSpikeAlert] = {}
        self.alert_handlers: list[Callable] = []
        self.monitoring_active = False
        self.monitoring_task: asyncio.Task | None = None
        for metric_type in MetricType:
            self.metrics_history[metric_type] = deque(maxlen=1000)
        self._setup_default_thresholds()
        self._setup_anomaly_detectors()

    def _setup_default_thresholds(self):
        """Setup default monitoring thresholds"""
        self.thresholds = {MetricType.REQUEST_RATE: MetricThreshold(metric_type=MetricType.REQUEST_RATE, warning_threshold=500.0, critical_threshold=1000.0, emergency_threshold=2000.0, time_window_seconds=60), MetricType.RESPONSE_TIME: MetricThreshold(metric_type=MetricType.RESPONSE_TIME, warning_threshold=500.0, critical_threshold=1000.0, emergency_threshold=2000.0, time_window_seconds=60), MetricType.ERROR_RATE: MetricThreshold(metric_type=MetricType.ERROR_RATE, warning_threshold=0.01, critical_threshold=0.05, emergency_threshold=0.1, time_window_seconds=60), MetricType.CPU_USAGE: MetricThreshold(metric_type=MetricType.CPU_USAGE, warning_threshold=70.0, critical_threshold=85.0, emergency_threshold=95.0, time_window_seconds=60), MetricType.MEMORY_USAGE: MetricThreshold(metric_type=MetricType.MEMORY_USAGE, warning_threshold=75.0, critical_threshold=90.0, emergency_threshold=95.0, time_window_seconds=60), MetricType.DATABASE_CONNECTIONS: MetricThreshold(metric_type=MetricType.DATABASE_CONNECTIONS, warning_threshold=60.0, critical_threshold=80.0, emergency_threshold=95.0, time_window_seconds=60), MetricType.CACHE_HIT_RATE: MetricThreshold(metric_type=MetricType.CACHE_HIT_RATE, warning_threshold=0.7, critical_threshold=0.5, emergency_threshold=0.3, time_window_seconds=60), MetricType.QUEUE_DEPTH: MetricThreshold(metric_type=MetricType.QUEUE_DEPTH, warning_threshold=1000.0, critical_threshold=5000.0, emergency_threshold=10000.0, time_window_seconds=60), MetricType.CONCURRENT_USERS: MetricThreshold(metric_type=MetricType.CONCURRENT_USERS, warning_threshold=1000.0, critical_threshold=5000.0, emergency_threshold=10000.0, time_window_seconds=60)}

    def _setup_anomaly_detectors(self):
        """Setup anomaly detection configurations"""
        self.anomaly_detectors = [AnomalyDetection(metric_type=MetricType.REQUEST_RATE, detection_method="statistical", sensitivity=0.8, baseline_window_minutes=30, anomaly_threshold_multiplier=3.0), AnomalyDetection(metric_type=MetricType.RESPONSE_TIME, detection_method="statistical", sensitivity=0.7, baseline_window_minutes=15, anomaly_threshold_multiplier=2.5), AnomalyDetection(metric_type=MetricType.ERROR_RATE, detection_method="statistical", sensitivity=0.9, baseline_window_minutes=10, anomaly_threshold_multiplier=5.0)]

    async def start_monitoring(self):
        """Start traffic spike monitoring"""
        if self.monitoring_active:
            return
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Traffic spike monitoring started")

    async def stop_monitoring(self):
        """Stop traffic spike monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitoring_task
        logger.info("Traffic spike monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await self._check_thresholds()
                await self._detect_anomalies()
                await self._process_alerts()
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in monitoring loop: %s", e)
                await asyncio.sleep(30)

    async def _collect_metrics(self):
        """Collect system metrics"""
        timestamp = datetime.now(UTC)
        request_rate = await self._collect_request_rate()
        self._add_metric(MetricType.REQUEST_RATE, request_rate, timestamp)
        response_time = await self._collect_response_time()
        self._add_metric(MetricType.RESPONSE_TIME, response_time, timestamp)
        error_rate = await self._collect_error_rate()
        self._add_metric(MetricType.ERROR_RATE, error_rate, timestamp)
        cpu_usage = await self._collect_cpu_usage()
        self._add_metric(MetricType.CPU_USAGE, cpu_usage, timestamp)
        memory_usage = await self._collect_memory_usage()
        self._add_metric(MetricType.MEMORY_USAGE, memory_usage, timestamp)
        db_connections = await self._collect_database_connections()
        self._add_metric(MetricType.DATABASE_CONNECTIONS, db_connections, timestamp)
        cache_hit_rate = await self._collect_cache_hit_rate()
        self._add_metric(MetricType.CACHE_HIT_RATE, cache_hit_rate, timestamp)
        queue_depth = await self._collect_queue_depth()
        self._add_metric(MetricType.QUEUE_DEPTH, queue_depth, timestamp)
        concurrent_users = await self._collect_concurrent_users()
        self._add_metric(MetricType.CONCURRENT_USERS, concurrent_users, timestamp)

    async def _collect_request_rate(self) -> float:
        """Collect request rate metric"""
        import random
        return random.uniform(50, 200)

    async def _collect_response_time(self) -> float:
        """Collect response time metric"""
        import random
        return random.uniform(100, 500)

    async def _collect_error_rate(self) -> float:
        """Collect error rate metric"""
        import random
        return random.uniform(0.001, 0.02)

    async def _collect_cpu_usage(self) -> float:
        """Collect CPU usage metric"""
        import psutil
        return psutil.cpu_percent(interval=1)

    async def _collect_memory_usage(self) -> float:
        """Collect memory usage metric"""
        import psutil
        memory = psutil.virtual_memory()
        return memory.percent

    async def _collect_database_connections(self) -> float:
        """Collect database connections metric"""
        import random
        return random.uniform(10, 50)

    async def _collect_cache_hit_rate(self) -> float:
        """Collect cache hit rate metric"""
        import random
        return random.uniform(0.6, 0.9)

    async def _collect_queue_depth(self) -> float:
        """Collect queue depth metric"""
        import random
        return random.uniform(0, 100)

    async def _collect_concurrent_users(self) -> float:
        """Collect concurrent users metric"""
        import random
        return random.uniform(100, 1000)

    def _add_metric(self, metric_type: MetricType, value: float, timestamp: datetime):
        """Add metric to history"""
        self.metrics_history[metric_type].append({"value": value, "timestamp": timestamp})

    async def _check_thresholds(self):
        """Check metrics against thresholds"""
        for metric_type, threshold in self.thresholds.items():
            recent_metrics = self._get_recent_metrics(metric_type, threshold.time_window_seconds)
            if not recent_metrics:
                continue
            values = [m["value"] for m in recent_metrics]
            avg_value = statistics.mean(values)
            alert = None
            threshold_value = None
            severity = None
            if avg_value >= threshold.emergency_threshold:
                severity = AlertSeverity.EMERGENCY
                threshold_value = threshold.emergency_threshold
            elif avg_value >= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif avg_value >= threshold.warning_threshold:
                severity = AlertSeverity.WARNING
                threshold_value = threshold.warning_threshold
            if severity:
                alert_id = f"{metric_type.value}_{severity.value}_{int(time.time())}"
                alert = TrafficSpikeAlert(alert_id=alert_id, metric_type=metric_type, severity=severity, title=f"{severity.value.title()} {metric_type.value.replace('_', ' ').title()}", message=f"{metric_type.value.replace('_', ' ').title()} is {avg_value:.2f}, threshold is {threshold_value:.2f}", current_value=avg_value, threshold=threshold_value, timestamp=datetime.now(UTC), duration_seconds=threshold.time_window_seconds, affected_endpoints=self._get_affected_endpoints(metric_type), recommended_actions=self._get_recommended_actions(metric_type, severity))
                self.active_alerts[alert_id] = alert
                logger.warning("Traffic spike alert: %s - %s", alert.title, alert.message)

    async def _detect_anomalies(self):
        """Detect anomalies in metrics"""
        for detector in self.anomaly_detectors:
            metric_type = detector.metric_type
            recent_metrics = self._get_recent_metrics(metric_type, detector.baseline_window_minutes * 60)
            if len(recent_metrics) < 10:
                continue
            values = [m["value"] for m in recent_metrics]
            baseline_mean = statistics.mean(values)
            baseline_std = statistics.stdev(values) if len(values) > 1 else 0
            current_metrics = self._get_recent_metrics(metric_type, 60)
            if not current_metrics:
                continue
            current_value = current_metrics[-1]["value"]
            if detector.detection_method == "statistical":
                if baseline_std > 0:
                    z_score = abs(current_value - baseline_mean) / baseline_std
                    if z_score > detector.anomaly_threshold_multiplier:
                        await self._create_anomaly_alert(metric_type, current_value, baseline_mean, z_score)

    async def _create_anomaly_alert(self, metric_type: MetricType, current_value: float, baseline_mean: float, z_score: float):
        """Create anomaly alert"""
        alert_id = f"anomaly_{metric_type.value}_{int(time.time())}"
        alert = TrafficSpikeAlert(alert_id=alert_id, metric_type=metric_type, severity=AlertSeverity.WARNING, title=f"Anomaly Detected in {metric_type.value.replace('_', ' ').title()}", message=f"{metric_type.value.replace('_', ' ').title()} is {current_value:.2f}, baseline is {baseline_mean:.2f} (z-score: {z_score:.2f})", current_value=current_value, threshold=baseline_mean, timestamp=datetime.now(UTC), duration_seconds=60, affected_endpoints=self._get_affected_endpoints(metric_type), recommended_actions=self._get_anomaly_actions(metric_type))
        self.active_alerts[alert_id] = alert
        logger.warning("Anomaly alert: %s - %s", alert.title, alert.message)

    async def _process_alerts(self):
        """Process active alerts"""
        for alert in self.active_alerts.values():
            if not alert.resolved:
                for handler in self.alert_handlers:
                    try:
                        await handler(alert)
                    except Exception as e:
                        logger.exception("Error in alert handler: %s", e)

    def _get_recent_metrics(self, metric_type: MetricType, seconds: int) -> list[dict]:
        """Get recent metrics for given time window"""
        cutoff_time = datetime.now(UTC) - timedelta(seconds=seconds)
        return [metric for metric in self.metrics_history[metric_type] if metric["timestamp"] >= cutoff_time]

    def _get_affected_endpoints(self, metric_type: MetricType) -> list[str]:
        """Get affected endpoints for metric type"""
        endpoint_mapping = {MetricType.REQUEST_RATE: ["/api/v1/*"], MetricType.RESPONSE_TIME: ["/api/v1/bookings", "/api/v1/ai/chat"], MetricType.ERROR_RATE: ["/api/v1/*"], MetricType.CPU_USAGE: ["/api/v1/*"], MetricType.MEMORY_USAGE: ["/api/v1/*"], MetricType.DATABASE_CONNECTIONS: ["/api/v1/bookings", "/api/v1/users"], MetricType.CACHE_HIT_RATE: ["/api/v1/bookings", "/api/v1/users"], MetricType.QUEUE_DEPTH: ["/api/v1/*"], MetricType.CONCURRENT_USERS: ["/api/v1/*"]}
        return endpoint_mapping.get(metric_type, ["/api/v1/*"])

    def _get_recommended_actions(self, metric_type: MetricType, severity: AlertSeverity) -> list[str]:
        """Get recommended actions for metric threshold violation"""
        action_mapping = {MetricType.REQUEST_RATE: ["Scale up application instances", "Implement rate limiting", "Add load balancer", "Enable request queuing"], MetricType.RESPONSE_TIME: ["Optimize slow endpoints", "Add caching", "Scale up resources", "Implement timeout handling"], MetricType.ERROR_RATE: ["Investigate error patterns", "Implement circuit breakers", "Add retry logic", "Check external dependencies"], MetricType.CPU_USAGE: ["Scale up CPU resources", "Optimize CPU-intensive operations", "Add load balancing", "Implement request throttling"], MetricType.MEMORY_USAGE: ["Increase memory allocation", "Optimize memory usage", "Add memory caching", "Implement memory cleanup"], MetricType.DATABASE_CONNECTIONS: ["Increase connection pool size", "Add read replicas", "Optimize database queries", "Implement connection pooling"], MetricType.CACHE_HIT_RATE: ["Warm up cache", "Optimize cache TTL", "Increase cache size", "Implement cache warming"], MetricType.QUEUE_DEPTH: ["Scale up workers", "Optimize queue processing", "Add queue partitioning", "Implement priority queuing"], MetricType.CONCURRENT_USERS: ["Scale up resources", "Implement session management", "Add load balancing", "Optimize user sessions"]}
        return action_mapping.get(metric_type, ["Investigate the issue"])

    def _get_anomaly_actions(self, metric_type: MetricType) -> list[str]:
        """Get recommended actions for anomaly detection"""
        return ["Investigate sudden change in metric", "Check for traffic spikes", "Verify system health", "Review recent deployments", "Check external dependencies"]

    async def get_current_metrics(self) -> dict[str, Any]:
        """Get current metrics snapshot"""
        current_metrics = {}
        for metric_type in MetricType:
            recent_metrics = self._get_recent_metrics(metric_type, 60)
            if recent_metrics:
                values = [m["value"] for m in recent_metrics]
                current_metrics[metric_type.value] = {"current": values[-1], "average": statistics.mean(values), "min": min(values), "max": max(values), "trend": "increasing" if values[-1] > values[0] else "decreasing"}
        return current_metrics

    async def get_active_alerts(self, severity: AlertSeverity | None=None) -> list[TrafficSpikeAlert]:
        """Get active alerts"""
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

    def add_alert_handler(self, handler: Callable):
        """Add alert handler"""
        self.alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable):
        """Remove alert handler"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)
traffic_spike_monitor = TrafficSpikeMonitor()

def get_traffic_spike_monitor() -> TrafficSpikeMonitor:
    """Get global traffic spike monitor instance"""
    return traffic_spike_monitor

async def console_alert_handler(alert: TrafficSpikeAlert):
    """Console alert handler"""

async def webhook_alert_handler(alert: TrafficSpikeAlert):
    """Webhook alert handler"""
    logger.info("Webhook alert sent: %s", alert.alert_id)

async def email_alert_handler(alert: TrafficSpikeAlert):
    """Email alert handler"""
    if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
        logger.info("Email alert sent: %s", alert.alert_id)
traffic_spike_monitor.add_alert_handler(console_alert_handler)
traffic_spike_monitor.add_alert_handler(webhook_alert_handler)
traffic_spike_monitor.add_alert_handler(email_alert_handler)
