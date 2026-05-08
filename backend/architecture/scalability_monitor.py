"""
Scalability Monitoring and Alerting System

Monitors system scalability and provides early warnings:
- Performance metrics tracking
- Capacity planning alerts
- Bottleneck detection
- Auto-scaling recommendations
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics

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
    metadata: Optional[Dict[str, Any]] = None


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
    recommendations: List[str]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class CapacityForecast:
    """Capacity forecast for planning"""
    resource_type: str
    current_capacity: float
    current_usage: float
    projected_usage_30d: float
    projected_usage_90d: float
    time_to_capacity_limit: int  # days
    recommended_action: str
    confidence: float


class MetricsCollector:
    """Collects performance metrics from various sources"""
    
    def __init__(self):
        self.metrics_buffer: List[PerformanceMetric] = []
        self.buffer_size = 10000
        self.collection_interval = 60  # seconds
    
    async def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics"""
        # This would integrate with monitoring systems like Prometheus, DataDog, etc.
        # For now, return mock data
        
        import psutil
        
        metrics = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
        
        return metrics
    
    async def collect_database_metrics(self) -> Dict[str, float]:
        """Collect database performance metrics"""
        # This would connect to database and collect metrics
        # For now, return mock data
        
        metrics = {
            "active_connections": 25,
            "max_connections": 100,
            "query_time_avg": 45.5,
            "query_time_p95": 120.0,
            "deadlocks": 0
        }
        
        return metrics
    
    async def collect_application_metrics(self) -> Dict[str, float]:
        """Collect application-level metrics"""
        # This would collect metrics from application logs, tracing, etc.
        
        metrics = {
            "api_response_time_avg": 85.2,
            "api_response_time_p95": 200.0,
            "error_rate": 0.02,
            "requests_per_second": 45.5,
            "cache_hit_rate": 0.78
        }
        
        return metrics
    
    async def collect_business_metrics(self) -> Dict[str, float]:
        """Collect business metrics"""
        # This would collect user growth, usage patterns, etc.
        
        metrics = {
            "active_users": 15420,
            "user_growth_rate": 0.15,  # 15% monthly growth
            "ai_requests_per_hour": 1250,
            "bookings_per_hour": 85
        }
        
        return metrics
    
    def add_metric(self, metric: PerformanceMetric):
        """Add metric to buffer"""
        self.metrics_buffer.append(metric)
        
        # Maintain buffer size
        if len(self.metrics_buffer) > self.buffer_size:
            self.metrics_buffer = self.metrics_buffer[-self.buffer_size:]
    
    def get_metrics(self, metric_type: MetricType, minutes: int = 60) -> List[PerformanceMetric]:
        """Get metrics for specific type and time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        filtered_metrics = [
            m for m in self.metrics_buffer
            if m.metric_type == metric_type and m.timestamp >= cutoff_time
        ]
        
        return filtered_metrics


class ThresholdMonitor:
    """Monitors metrics against thresholds"""
    
    def __init__(self):
        self.thresholds: Dict[MetricType, MetricThreshold] = {}
        self.violation_counts: Dict[str, int] = {}
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default monitoring thresholds"""
        self.thresholds = {
            MetricType.CPU_USAGE: MetricThreshold(
                metric_type=MetricType.CPU_USAGE,
                warning_threshold=70.0,
                critical_threshold=85.0,
                emergency_threshold=95.0
            ),
            MetricType.MEMORY_USAGE: MetricThreshold(
                metric_type=MetricType.MEMORY_USAGE,
                warning_threshold=75.0,
                critical_threshold=90.0,
                emergency_threshold=95.0
            ),
            MetricType.DATABASE_CONNECTIONS: MetricThreshold(
                metric_type=MetricType.DATABASE_CONNECTIONS,
                warning_threshold=60.0,
                critical_threshold=80.0,
                emergency_threshold=95.0
            ),
            MetricType.API_RESPONSE_TIME: MetricThreshold(
                metric_type=MetricType.API_RESPONSE_TIME,
                warning_threshold=200.0,
                critical_threshold=500.0,
                emergency_threshold=1000.0
            ),
            MetricType.ERROR_RATE: MetricThreshold(
                metric_type=MetricType.ERROR_RATE,
                warning_threshold=0.01,  # 1%
                critical_threshold=0.05,  # 5%
                emergency_threshold=0.10  # 10%
            ),
            MetricType.QUEUE_DEPTH: MetricThreshold(
                metric_type=MetricType.QUEUE_DEPTH,
                warning_threshold=1000,
                critical_threshold=5000,
                emergency_threshold=10000
            ),
            MetricType.CACHE_HIT_RATE: MetricThreshold(
                metric_type=MetricType.CACHE_HIT_RATE,
                warning_threshold=0.70,  # 70%
                critical_threshold=0.50,  # 50%
                emergency_threshold=0.30   # 30%
            ),
            MetricType.USER_GROWTH: MetricThreshold(
                metric_type=MetricType.USER_GROWTH,
                warning_threshold=0.20,  # 20% monthly growth
                critical_threshold=0.50,  # 50% monthly growth
                emergency_threshold=1.00  # 100% monthly growth
            )
        }
    
    def check_thresholds(self, metric: PerformanceMetric) -> Optional[ScalabilityAlert]:
        """Check metric against thresholds and generate alert if needed"""
        threshold = self.thresholds.get(metric.metric_type)
        if not threshold:
            return None
        
        violation_key = f"{metric.metric_type.value}_{metric.source}"
        
        # Determine severity
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
            # Check consecutive violations
            self.violation_counts[violation_key] = self.violation_counts.get(violation_key, 0) + 1
            
            if self.violation_counts[violation_key] >= threshold.consecutive_violations:
                # Generate alert
                alert = ScalabilityAlert(
                    alert_id=f"alert_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{metric.metric_type.value}",
                    metric_type=metric.metric_type,
                    severity=severity,
                    title=f"{severity.value.title()} {metric.metric_type.value.replace('_', ' ').title()}",
                    message=f"{metric.metric_type.value.replace('_', ' ').title()} is {metric.value:.2f}, threshold is {threshold_value:.2f}",
                    current_value=metric.value,
                    threshold=threshold_value,
                    timestamp=metric.timestamp,
                    source=metric.source,
                    recommendations=self._get_recommendations(metric.metric_type, severity)
                )
                
                # Reset violation count after alert
                self.violation_counts[violation_key] = 0
                
                return alert
        else:
            # Reset violation count on normal values
            self.violation_counts[violation_key] = 0
        
        return None
    
    def _get_recommendations(self, metric_type: MetricType, severity: AlertSeverity) -> List[str]:
        """Get recommendations for metric violations"""
        recommendations = {
            MetricType.CPU_USAGE: [
                "Scale up CPU resources",
                "Optimize CPU-intensive operations",
                "Consider horizontal scaling"
            ],
            MetricType.MEMORY_USAGE: [
                "Increase memory allocation",
                "Optimize memory usage patterns",
                "Implement memory caching"
            ],
            MetricType.DATABASE_CONNECTIONS: [
                "Increase connection pool size",
                "Optimize database queries",
                "Implement connection pooling"
            ],
            MetricType.API_RESPONSE_TIME: [
                "Optimize slow endpoints",
                "Implement caching",
                "Scale up application servers"
            ],
            MetricType.ERROR_RATE: [
                "Investigate error patterns",
                "Implement circuit breakers",
                "Add more robust error handling"
            ],
            MetricType.QUEUE_DEPTH: [
                "Scale up worker processes",
                "Optimize queue processing",
                "Consider queue partitioning"
            ],
            MetricType.CACHE_HIT_RATE: [
                "Warm up cache with frequently accessed data",
                "Optimize cache TTL values",
                "Increase cache size"
            ],
            MetricType.USER_GROWTH: [
                "Prepare for user onboarding surge",
                "Scale customer support",
                "Monitor infrastructure capacity"
            ]
        }
        
        return recommendations.get(metric_type, ["Investigate the metric and take appropriate action"])


class CapacityPlanner:
    """Plans capacity based on current usage and growth patterns"""
    
    def __init__(self):
        self.growth_history: Dict[str, List[float]] = {}
    
    async def forecast_capacity_needs(self, resource_type: str, current_usage: float, 
                                   historical_data: List[float]) -> CapacityForecast:
        """Forecast capacity needs for a resource"""
        
        # Calculate growth rate
        if len(historical_data) < 2:
            growth_rate = 0.10  # Default 10% growth
        else:
            # Simple linear growth calculation
            recent_growth = (historical_data[-1] - historical_data[0]) / historical_data[0]
            growth_rate = max(0, recent_growth)  # Assume growth, not decline
        
        # Project future usage
        projected_30d = current_usage * (1 + growth_rate) ** 1
        projected_90d = current_usage * (1 + growth_rate) ** 3
        
        # Assume 80% capacity limit
        capacity_limit = current_usage / 0.8
        
        # Calculate days to capacity limit
        if growth_rate > 0:
            days_to_limit = int((math.log(capacity_limit / current_usage) / math.log(1 + growth_rate)))
        else:
            days_to_limit = 365  # No growth, assume 1 year
        
        # Determine recommended action
        if days_to_limit < 30:
            action = "Immediate scaling required"
        elif days_to_limit < 90:
            action = "Plan scaling within next quarter"
        else:
            action = "Monitor and plan for future scaling"
        
        # Calculate confidence based on data quality
        confidence = min(1.0, len(historical_data) / 30)  # More data = higher confidence
        
        return CapacityForecast(
            resource_type=resource_type,
            current_capacity=capacity_limit,
            current_usage=current_usage,
            projected_usage_30d=projected_30d,
            projected_usage_90d=projected_90d,
            time_to_capacity_limit=days_to_limit,
            recommended_action=action,
            confidence=confidence
        )


class ScalabilityMonitor:
    """Main scalability monitoring system"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.threshold_monitor = ThresholdMonitor()
        self.capacity_planner = CapacityPlanner()
        self.active_alerts: Dict[str, ScalabilityAlert] = []
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
    
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
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scalability monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                await self._collect_all_metrics()
                
                # Check thresholds
                await self._check_all_thresholds()
                
                # Update capacity forecasts
                await self._update_capacity_forecasts()
                
                # Wait for next collection
                await asyncio.sleep(self.metrics_collector.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _collect_all_metrics(self):
        """Collect all types of metrics"""
        timestamp = datetime.now(timezone.utc)
        
        # System metrics
        system_metrics = await self.metrics_collector.collect_system_metrics()
        for metric_name, value in system_metrics.items():
            metric = PerformanceMetric(
                metric_type=MetricType(metric_name),
                value=value,
                timestamp=timestamp,
                source="system"
            )
            self.metrics_collector.add_metric(metric)
        
        # Database metrics
        db_metrics = await self.metrics_collector.collect_database_metrics()
        for metric_name, value in db_metrics.items():
            metric = PerformanceMetric(
                metric_type=MetricType(metric_name),
                value=value,
                timestamp=timestamp,
                source="database"
            )
            self.metrics_collector.add_metric(metric)
        
        # Application metrics
        app_metrics = await self.metrics_collector.collect_application_metrics()
        for metric_name, value in app_metrics.items():
            metric = PerformanceMetric(
                metric_type=MetricType(metric_name),
                value=value,
                timestamp=timestamp,
                source="application"
            )
            self.metrics_collector.add_metric(metric)
        
        # Business metrics
        business_metrics = await self.metrics_collector.collect_business_metrics()
        for metric_name, value in business_metrics.items():
            metric = PerformanceMetric(
                metric_type=MetricType(metric_name),
                value=value,
                timestamp=timestamp,
                source="business"
            )
            self.metrics_collector.add_metric(metric)
    
    async def _check_all_thresholds(self):
        """Check all metrics against thresholds"""
        # Get recent metrics
        recent_metrics = self.metrics_collector.metrics_buffer[-100:]  # Last 100 metrics
        
        for metric in recent_metrics:
            alert = self.threshold_monitor.check_thresholds(metric)
            if alert:
                self.active_alerts[alert.alert_id] = alert
                logger.warning(f"Scalability alert: {alert.title} - {alert.message}")
    
    async def _update_capacity_forecasts(self):
        """Update capacity forecasts"""
        # This would analyze trends and update forecasts
        # For now, it's a placeholder
        pass
    
    async def get_current_alerts(self, severity: Optional[AlertSeverity] = None) -> List[ScalabilityAlert]:
        """Get current active alerts"""
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
    
    async def get_capacity_forecasts(self) -> List[CapacityForecast]:
        """Get capacity forecasts for all resources"""
        forecasts = []
        
        # Get historical data for each metric type
        for metric_type in MetricType:
            metrics = self.metrics_collector.get_metrics(metric_type, minutes=1440)  # Last 24 hours
            
            if len(metrics) >= 2:
                values = [m.value for m in metrics]
                current_usage = values[-1]
                
                forecast = await self.capacity_planner.forecast_capacity_needs(
                    resource_type=metric_type.value,
                    current_usage=current_usage,
                    historical_data=values
                )
                
                forecasts.append(forecast)
        
        return forecasts
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        # Get recent metrics for each type
        summary = {}
        
        for metric_type in MetricType:
            recent_metrics = self.metrics_collector.get_metrics(metric_type, minutes=60)
            
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                summary[metric_type.value] = {
                    "current": values[-1],
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "trend": "increasing" if values[-1] > values[0] else "decreasing"
                }
        
        return summary


# Global scalability monitor
scalability_monitor = ScalabilityMonitor()


def get_scalability_monitor() -> ScalabilityMonitor:
    """Get global scalability monitor instance"""
    return scalability_monitor


# Background task for monitoring
async def start_scalability_monitoring():
    """Start scalability monitoring in background"""
    monitor = get_scalability_monitor()
    await monitor.start_monitoring()


async def stop_scalability_monitoring():
    """Stop scalability monitoring"""
    monitor = get_scalability_monitor()
    await monitor.stop_monitoring()


# Integration with FastAPI
"""
@router.post("/monitoring/start")
async def start_monitoring():
    await start_scalability_monitoring()
    return {"status": "monitoring_started"}

@router.post("/monitoring/stop")
async def stop_monitoring():
    await stop_scalability_monitoring()
    return {"status": "monitoring_stopped"}

@router.get("/monitoring/alerts")
async def get_alerts(severity: Optional[str] = None):
    monitor = get_scalability_monitor()
    alert_severity = AlertSeverity(severity) if severity else None
    alerts = await monitor.get_current_alerts(alert_severity)
    return {"alerts": [asdict(alert) for alert in alerts]}

@router.get("/monitoring/capacity")
async def get_capacity_forecasts():
    monitor = get_scalability_monitor()
    forecasts = await monitor.get_capacity_forecasts()
    return {"forecasts": [asdict(forecast) for forecast in forecasts]}

@router.get("/monitoring/summary")
async def get_performance_summary():
    monitor = get_scalability_monitor()
    summary = await monitor.get_performance_summary()
    return summary
"""
