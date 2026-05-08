"""
Traffic Spike Monitoring System

Comprehensive monitoring for traffic spikes and system health:
- Real-time metrics collection
- Anomaly detection
- Alerting system
- Performance dashboard
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
import time
from collections import deque

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
    affected_endpoints: List[str]
    recommended_actions: List[str]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class AnomalyDetection:
    """Anomaly detection configuration"""
    metric_type: MetricType
    detection_method: str  # "statistical", "ml", "threshold"
    sensitivity: float  # 0.0 to 1.0
    baseline_window_minutes: int = 30
    anomaly_threshold_multiplier: float = 2.0


class TrafficSpikeMonitor:
    """Monitors traffic spikes and system performance"""
    
    def __init__(self):
        self.metrics_history: Dict[MetricType, deque] = {}
        self.thresholds: Dict[MetricType, MetricThreshold] = {}
        self.anomaly_detectors: Dict[MetricType, AnomalyDetection] = []
        self.active_alerts: Dict[str, TrafficSpikeAlert] = {}
        self.alert_handlers: List[Callable] = []
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Initialize metrics history
        for metric_type in MetricType:
            self.metrics_history[metric_type] = deque(maxlen=1000)
        
        # Setup default thresholds
        self._setup_default_thresholds()
        
        # Setup anomaly detectors
        self._setup_anomaly_detectors()
    
    def _setup_default_thresholds(self):
        """Setup default monitoring thresholds"""
        self.thresholds = {
            MetricType.REQUEST_RATE: MetricThreshold(
                metric_type=MetricType.REQUEST_RATE,
                warning_threshold=500.0,  # 500 RPS
                critical_threshold=1000.0,  # 1000 RPS
                emergency_threshold=2000.0,  # 2000 RPS
                time_window_seconds=60
            ),
            MetricType.RESPONSE_TIME: MetricThreshold(
                metric_type=MetricType.RESPONSE_TIME,
                warning_threshold=500.0,  # 500ms
                critical_threshold=1000.0,  # 1000ms
                emergency_threshold=2000.0,  # 2000ms
                time_window_seconds=60
            ),
            MetricType.ERROR_RATE: MetricThreshold(
                metric_type=MetricType.ERROR_RATE,
                warning_threshold=0.01,  # 1%
                critical_threshold=0.05,  # 5%
                emergency_threshold=0.10,  # 10%
                time_window_seconds=60
            ),
            MetricType.CPU_USAGE: MetricThreshold(
                metric_type=MetricType.CPU_USAGE,
                warning_threshold=70.0,  # 70%
                critical_threshold=85.0,  # 85%
                emergency_threshold=95.0,  # 95%
                time_window_seconds=60
            ),
            MetricType.MEMORY_USAGE: MetricThreshold(
                metric_type=MetricType.MEMORY_USAGE,
                warning_threshold=75.0,  # 75%
                critical_threshold=90.0,  # 90%
                emergency_threshold=95.0,  # 95%
                time_window_seconds=60
            ),
            MetricType.DATABASE_CONNECTIONS: MetricThreshold(
                metric_type=MetricType.DATABASE_CONNECTIONS,
                warning_threshold=60.0,  # 60% of max connections
                critical_threshold=80.0,  # 80% of max connections
                emergency_threshold=95.0,  # 95% of max connections
                time_window_seconds=60
            ),
            MetricType.CACHE_HIT_RATE: MetricThreshold(
                metric_type=MetricType.CACHE_HIT_RATE,
                warning_threshold=0.70,  # 70%
                critical_threshold=0.50,  # 50%
                emergency_threshold=0.30,  # 30%
                time_window_seconds=60
            ),
            MetricType.QUEUE_DEPTH: MetricThreshold(
                metric_type=MetricType.QUEUE_DEPTH,
                warning_threshold=1000.0,
                critical_threshold=5000.0,
                emergency_threshold=10000.0,
                time_window_seconds=60
            ),
            MetricType.CONCURRENT_USERS: MetricThreshold(
                metric_type=MetricType.CONCURRENT_USERS,
                warning_threshold=1000.0,
                critical_threshold=5000.0,
                emergency_threshold=10000.0,
                time_window_seconds=60
            )
        }
    
    def _setup_anomaly_detectors(self):
        """Setup anomaly detection configurations"""
        self.anomaly_detectors = [
            AnomalyDetection(
                metric_type=MetricType.REQUEST_RATE,
                detection_method="statistical",
                sensitivity=0.8,
                baseline_window_minutes=30,
                anomaly_threshold_multiplier=3.0
            ),
            AnomalyDetection(
                metric_type=MetricType.RESPONSE_TIME,
                detection_method="statistical",
                sensitivity=0.7,
                baseline_window_minutes=15,
                anomaly_threshold_multiplier=2.5
            ),
            AnomalyDetection(
                metric_type=MetricType.ERROR_RATE,
                detection_method="statistical",
                sensitivity=0.9,
                baseline_window_minutes=10,
                anomaly_threshold_multiplier=5.0
            )
        ]
    
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
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Traffic spike monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                await self._collect_metrics()
                
                # Check thresholds
                await self._check_thresholds()
                
                # Detect anomalies
                await self._detect_anomalies()
                
                # Process alerts
                await self._process_alerts()
                
                # Wait for next collection
                await asyncio.sleep(10)  # Collect every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error
    
    async def _collect_metrics(self):
        """Collect system metrics"""
        timestamp = datetime.now(timezone.utc)
        
        # Collect request rate
        request_rate = await self._collect_request_rate()
        self._add_metric(MetricType.REQUEST_RATE, request_rate, timestamp)
        
        # Collect response time
        response_time = await self._collect_response_time()
        self._add_metric(MetricType.RESPONSE_TIME, response_time, timestamp)
        
        # Collect error rate
        error_rate = await self._collect_error_rate()
        self._add_metric(MetricType.ERROR_RATE, error_rate, timestamp)
        
        # Collect system metrics
        cpu_usage = await self._collect_cpu_usage()
        self._add_metric(MetricType.CPU_USAGE, cpu_usage, timestamp)
        
        memory_usage = await self._collect_memory_usage()
        self._add_metric(MetricType.MEMORY_USAGE, memory_usage, timestamp)
        
        # Collect database metrics
        db_connections = await self._collect_database_connections()
        self._add_metric(MetricType.DATABASE_CONNECTIONS, db_connections, timestamp)
        
        # Collect cache metrics
        cache_hit_rate = await self._collect_cache_hit_rate()
        self._add_metric(MetricType.CACHE_HIT_RATE, cache_hit_rate, timestamp)
        
        # Collect queue metrics
        queue_depth = await self._collect_queue_depth()
        self._add_metric(MetricType.QUEUE_DEPTH, queue_depth, timestamp)
        
        # Collect concurrent users
        concurrent_users = await self._collect_concurrent_users()
        self._add_metric(MetricType.CONCURRENT_USERS, concurrent_users, timestamp)
    
    async def _collect_request_rate(self) -> float:
        """Collect request rate metric"""
        # This would integrate with application metrics
        # For now, return simulated data
        import random
        return random.uniform(50, 200)  # Simulated RPS
    
    async def _collect_response_time(self) -> float:
        """Collect response time metric"""
        # This would integrate with application metrics
        import random
        return random.uniform(100, 500)  # Simulated response time in ms
    
    async def _collect_error_rate(self) -> float:
        """Collect error rate metric"""
        # This would integrate with application metrics
        import random
        return random.uniform(0.001, 0.02)  # Simulated error rate
    
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
        # This would query database for connection count
        # For now, return simulated data
        import random
        return random.uniform(10, 50)  # Simulated connection count
    
    async def _collect_cache_hit_rate(self) -> float:
        """Collect cache hit rate metric"""
        # This would query cache for hit rate
        import random
        return random.uniform(0.6, 0.9)  # Simulated hit rate
    
    async def _collect_queue_depth(self) -> float:
        """Collect queue depth metric"""
        # This would query message queue for depth
        import random
        return random.uniform(0, 100)  # Simulated queue depth
    
    async def _collect_concurrent_users(self) -> float:
        """Collect concurrent users metric"""
        # This would track active user sessions
        import random
        return random.uniform(100, 1000)  # Simulated concurrent users
    
    def _add_metric(self, metric_type: MetricType, value: float, timestamp: datetime):
        """Add metric to history"""
        self.metrics_history[metric_type].append({
            "value": value,
            "timestamp": timestamp
        })
    
    async def _check_thresholds(self):
        """Check metrics against thresholds"""
        for metric_type, threshold in self.thresholds.items():
            recent_metrics = self._get_recent_metrics(metric_type, threshold.time_window_seconds)
            
            if not recent_metrics:
                continue
            
            # Calculate average value
            values = [m["value"] for m in recent_metrics]
            avg_value = statistics.mean(values)
            
            # Check thresholds
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
                
                alert = TrafficSpikeAlert(
                    alert_id=alert_id,
                    metric_type=metric_type,
                    severity=severity,
                    title=f"{severity.value.title()} {metric_type.value.replace('_', ' ').title()}",
                    message=f"{metric_type.value.replace('_', ' ').title()} is {avg_value:.2f}, threshold is {threshold_value:.2f}",
                    current_value=avg_value,
                    threshold=threshold_value,
                    timestamp=datetime.now(timezone.utc),
                    duration_seconds=threshold.time_window_seconds,
                    affected_endpoints=self._get_affected_endpoints(metric_type),
                    recommended_actions=self._get_recommended_actions(metric_type, severity)
                )
                
                self.active_alerts[alert_id] = alert
                logger.warning(f"Traffic spike alert: {alert.title} - {alert.message}")
    
    async def _detect_anomalies(self):
        """Detect anomalies in metrics"""
        for detector in self.anomaly_detectors:
            metric_type = detector.metric_type
            recent_metrics = self._get_recent_metrics(metric_type, detector.baseline_window_minutes * 60)
            
            if len(recent_metrics) < 10:  # Need minimum data points
                continue
            
            # Calculate baseline
            values = [m["value"] for m in recent_metrics]
            baseline_mean = statistics.mean(values)
            baseline_std = statistics.stdev(values) if len(values) > 1 else 0
            
            # Get current value
            current_metrics = self._get_recent_metrics(metric_type, 60)
            if not current_metrics:
                continue
            
            current_value = current_metrics[-1]["value"]
            
            # Detect anomaly
            if detector.detection_method == "statistical":
                if baseline_std > 0:
                    z_score = abs(current_value - baseline_mean) / baseline_std
                    if z_score > detector.anomaly_threshold_multiplier:
                        await self._create_anomaly_alert(metric_type, current_value, baseline_mean, z_score)
    
    async def _create_anomaly_alert(self, metric_type: MetricType, current_value: float, 
                                   baseline_mean: float, z_score: float):
        """Create anomaly alert"""
        alert_id = f"anomaly_{metric_type.value}_{int(time.time())}"
        
        alert = TrafficSpikeAlert(
            alert_id=alert_id,
            metric_type=metric_type,
            severity=AlertSeverity.WARNING,
            title=f"Anomaly Detected in {metric_type.value.replace('_', ' ').title()}",
            message=f"{metric_type.value.replace('_', ' ').title()} is {current_value:.2f}, baseline is {baseline_mean:.2f} (z-score: {z_score:.2f})",
            current_value=current_value,
            threshold=baseline_mean,
            timestamp=datetime.now(timezone.utc),
            duration_seconds=60,
            affected_endpoints=self._get_affected_endpoints(metric_type),
            recommended_actions=self._get_anomaly_actions(metric_type)
        )
        
        self.active_alerts[alert_id] = alert
        logger.warning(f"Anomaly alert: {alert.title} - {alert.message}")
    
    async def _process_alerts(self):
        """Process active alerts"""
        for alert in self.active_alerts.values():
            if not alert.resolved:
                # Send to alert handlers
                for handler in self.alert_handlers:
                    try:
                        await handler(alert)
                    except Exception as e:
                        logger.error(f"Error in alert handler: {e}")
    
    def _get_recent_metrics(self, metric_type: MetricType, seconds: int) -> List[Dict]:
        """Get recent metrics for given time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        
        return [
            metric for metric in self.metrics_history[metric_type]
            if metric["timestamp"] >= cutoff_time
        ]
    
    def _get_affected_endpoints(self, metric_type: MetricType) -> List[str]:
        """Get affected endpoints for metric type"""
        endpoint_mapping = {
            MetricType.REQUEST_RATE: ["/api/v1/*"],
            MetricType.RESPONSE_TIME: ["/api/v1/bookings", "/api/v1/ai/chat"],
            MetricType.ERROR_RATE: ["/api/v1/*"],
            MetricType.CPU_USAGE: ["/api/v1/*"],
            MetricType.MEMORY_USAGE: ["/api/v1/*"],
            MetricType.DATABASE_CONNECTIONS: ["/api/v1/bookings", "/api/v1/users"],
            MetricType.CACHE_HIT_RATE: ["/api/v1/bookings", "/api/v1/users"],
            MetricType.QUEUE_DEPTH: ["/api/v1/*"],
            MetricType.CONCURRENT_USERS: ["/api/v1/*"]
        }
        
        return endpoint_mapping.get(metric_type, ["/api/v1/*"])
    
    def _get_recommended_actions(self, metric_type: MetricType, severity: AlertSeverity) -> List[str]:
        """Get recommended actions for metric threshold violation"""
        action_mapping = {
            MetricType.REQUEST_RATE: [
                "Scale up application instances",
                "Implement rate limiting",
                "Add load balancer",
                "Enable request queuing"
            ],
            MetricType.RESPONSE_TIME: [
                "Optimize slow endpoints",
                "Add caching",
                "Scale up resources",
                "Implement timeout handling"
            ],
            MetricType.ERROR_RATE: [
                "Investigate error patterns",
                "Implement circuit breakers",
                "Add retry logic",
                "Check external dependencies"
            ],
            MetricType.CPU_USAGE: [
                "Scale up CPU resources",
                "Optimize CPU-intensive operations",
                "Add load balancing",
                "Implement request throttling"
            ],
            MetricType.MEMORY_USAGE: [
                "Increase memory allocation",
                "Optimize memory usage",
                "Add memory caching",
                "Implement memory cleanup"
            ],
            MetricType.DATABASE_CONNECTIONS: [
                "Increase connection pool size",
                "Add read replicas",
                "Optimize database queries",
                "Implement connection pooling"
            ],
            MetricType.CACHE_HIT_RATE: [
                "Warm up cache",
                "Optimize cache TTL",
                "Increase cache size",
                "Implement cache warming"
            ],
            MetricType.QUEUE_DEPTH: [
                "Scale up workers",
                "Optimize queue processing",
                "Add queue partitioning",
                "Implement priority queuing"
            ],
            MetricType.CONCURRENT_USERS: [
                "Scale up resources",
                "Implement session management",
                "Add load balancing",
                "Optimize user sessions"
            ]
        }
        
        return action_mapping.get(metric_type, ["Investigate the issue"])
    
    def _get_anomaly_actions(self, metric_type: MetricType) -> List[str]:
        """Get recommended actions for anomaly detection"""
        return [
            "Investigate sudden change in metric",
            "Check for traffic spikes",
            "Verify system health",
            "Review recent deployments",
            "Check external dependencies"
        ]
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        current_metrics = {}
        
        for metric_type in MetricType:
            recent_metrics = self._get_recent_metrics(metric_type, 60)
            if recent_metrics:
                values = [m["value"] for m in recent_metrics]
                current_metrics[metric_type.value] = {
                    "current": values[-1],
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "trend": "increasing" if values[-1] > values[0] else "decreasing"
                }
        
        return current_metrics
    
    async def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[TrafficSpikeAlert]:
        """Get active alerts"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return alerts
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    def add_alert_handler(self, handler: Callable):
        """Add alert handler"""
        self.alert_handlers.append(handler)
    
    def remove_alert_handler(self, handler: Callable):
        """Remove alert handler"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)


# Global traffic spike monitor
traffic_spike_monitor = TrafficSpikeMonitor()


def get_traffic_spike_monitor() -> TrafficSpikeMonitor:
    """Get global traffic spike monitor instance"""
    return traffic_spike_monitor


# Alert handler examples
async def console_alert_handler(alert: TrafficSpikeAlert):
    """Console alert handler"""
    print(f"[ALERT] {alert.title}: {alert.message}")


async def webhook_alert_handler(alert: TrafficSpikeAlert):
    """Webhook alert handler"""
    # This would send alert to webhook endpoint
    logger.info(f"Webhook alert sent: {alert.alert_id}")


async def email_alert_handler(alert: TrafficSpikeAlert):
    """Email alert handler"""
    # This would send email alert
    if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
        logger.info(f"Email alert sent: {alert.alert_id}")


# Setup default alert handlers
traffic_spike_monitor.add_alert_handler(console_alert_handler)
traffic_spike_monitor.add_alert_handler(webhook_alert_handler)
traffic_spike_monitor.add_alert_handler(email_alert_handler)
