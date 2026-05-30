"""
Traffic Spike Failure Analysis for GraftAI

Analyzes what fails first under sudden traffic spikes:
- Component failure sequencing
- Performance degradation patterns
- Resource exhaustion analysis
- Critical failure point identification
"""
import logging
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """System components to analyze"""
    DATABASE = "database"
    CACHE = "cache"
    API_SERVER = "api_server"
    AI_SERVICE = "ai_service"
    CALENDAR_SYNC = "calendar_sync"
    PAYMENT_GATEWAY = "payment_gateway"
    NOTIFICATION_SERVICE = "notification_service"
    QUEUE_SYSTEM = "queue_system"

class FailureSeverity(Enum):
    """Failure severity levels"""
    DEGRADED = "degraded"
    PARTIAL = "partial"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"

@dataclass
class ComponentFailure:
    """Component failure analysis"""
    component: ComponentType
    failure_type: str
    time_to_failure: float
    severity: FailureSeverity
    symptoms: list[str]
    recovery_time: float | None = None
    root_cause: str
    impact_on_users: str
    cascade_effects: list[str]

@dataclass
class PerformanceDegradation:
    """Performance degradation analysis"""
    component: ComponentType
    metric_name: str
    baseline_value: float
    degraded_value: float
    degradation_percentage: float
    time_to_degradation: float
    user_impact: str

@dataclass
class ResourceExhaustion:
    """Resource exhaustion analysis"""
    resource_type: str
    current_usage: float
    maximum_capacity: float
    exhaustion_time: float
    consequences: list[str]
    recovery_actions: list[str]

class TrafficSpikeFailureAnalyzer:
    """Analyzes system failures during traffic spikes"""

    def __init__(self):
        self.component_failures: list[ComponentFailure] = []
        self.performance_degradations: list[PerformanceDegradation] = []
        self.resource_exhaustions: list[ResourceExhaustion] = []
        self.failure_timeline: list[tuple[float, str]] = []

    def analyze_failure_sequence(self, simulation_report: dict[str, Any]) -> dict[str, Any]:
        """Analyze the sequence of failures during traffic spike"""
        logger.info("Analyzing failure sequence from traffic spike simulation")
        failure_points = simulation_report.get("failure_points", [])
        resource_usage = simulation_report.get("resource_usage", {})
        bottlenecks = simulation_report.get("bottlenecks", [])
        first_failures = self._identify_first_failures(failure_points)
        degradations = self._analyze_performance_degradation(bottlenecks, resource_usage)
        exhaustions = self._analyze_resource_exhaustion(resource_usage)
        cascade_effects = self._identify_cascade_effects(first_failures, degradations, exhaustions)
        return {"failure_sequence": {"first_to_fail": [asdict(f) for f in first_failures], "degradation_timeline": [asdict(d) for d in degradations], "resource_exhaustion": [asdict(e) for e in exhaustions], "cascade_effects": cascade_effects}, "critical_failure_points": self._identify_critical_failure_points(first_failures), "recovery_analysis": self._analyze_recovery_patterns(first_failures), "user_impact_analysis": self._analyze_user_impact(first_failures, degradations), "recommendations": self._generate_failure_recommendations(first_failures, degradations, exhaustions)}

    def _identify_first_failures(self, failure_points: list[dict]) -> list[ComponentFailure]:
        """Identify components that fail first"""
        first_failures = []
        sorted_failures = sorted(failure_points, key=lambda f: f.get("time_to_failure", float("inf")))
        for i, failure_data in enumerate(sorted_failures[:5]):
            component = self._map_failure_to_component(failure_data)
            failure = ComponentFailure(component=component, failure_type=failure_data.get("failure_type", "unknown"), time_to_failure=failure_data.get("time_to_failure", 0), severity=self._determine_failure_severity(failure_data), symptoms=failure_data.get("symptoms", []), root_cause=self._identify_root_cause(failure_data, i), impact_on_users=self._assess_user_impact(component, failure_data), cascade_effects=[])
            first_failures.append(failure)
        return first_failures

    def _analyze_performance_degradation(self, bottlenecks: list[dict], resource_usage: dict) -> list[PerformanceDegradation]:
        """Analyze performance degradation patterns"""
        degradations = []
        for resource_type, usage_data in resource_usage.items():
            if isinstance(usage_data, dict) and "final" in usage_data and ("avg" in usage_data):
                final_usage = usage_data["final"]
                baseline_usage = usage_data["avg"]
                if final_usage > baseline_usage * 1.5:
                    degradation = PerformanceDegradation(component=self._map_resource_to_component(resource_type), metric_name=f"{resource_type}_usage", baseline_value=baseline_usage, degraded_value=final_usage, degradation_percentage=(final_usage - baseline_usage) / baseline_usage * 100, time_to_degradation=60, user_impact=self._assess_degradation_impact(resource_type, final_usage))
                    degradations.append(degradation)
        for bottleneck in bottlenecks:
            if bottleneck.get("peak_value", 0) > bottleneck.get("baseline_value", 0) * 2:
                degradation = PerformanceDegradation(component=self._map_bottleneck_to_component(bottleneck), metric_name=bottleneck.get("bottleneck_type", "unknown"), baseline_value=bottleneck.get("baseline_value", 0), degraded_value=bottleneck.get("peak_value", 0), degradation_percentage=bottleneck.get("duration_above_threshold", 0), time_to_degradation=bottleneck.get("time_to_peak", 0), user_impact=bottleneck.get("impact_on_users", "Unknown impact"))
                degradations.append(degradation)
        return degradations

    def _analyze_resource_exhaustion(self, resource_usage: dict) -> list[ResourceExhaustion]:
        """Analyze resource exhaustion patterns"""
        exhaustions = []
        resource_limits = {"cpu": {"max": 100, "unit": "%"}, "memory": {"max": 100, "unit": "%"}, "network": {"max": 1000000000, "unit": "bytes"}}
        for resource_type, limits in resource_limits.items():
            if resource_type in resource_usage:
                usage_data = resource_usage[resource_type]
                max_usage = usage_data.get("max", 0)
                if max_usage >= limits["max"] * 0.95:
                    exhaustion = ResourceExhaustion(resource_type=f"{resource_type}_{limits['unit']}", current_usage=max_usage, maximum_capacity=limits["max"], exhaustion_time=120, consequences=self._identify_exhaustion_consequences(resource_type), recovery_actions=self._identify_recovery_actions(resource_type))
                    exhaustions.append(exhaustion)
        return exhaustions

    def _identify_cascade_effects(self, failures: list[ComponentFailure], degradations: list[PerformanceDegradation], exhaustions: list[ResourceExhaustion]) -> list[str]:
        """Identify cascade effects between component failures"""
        cascade_effects = []
        db_failure = next((f for f in failures if f.component == ComponentType.DATABASE), None)
        if db_failure:
            cascade_effects.extend(["Calendar sync failures due to database unavailability", "Booking creation failures", "User authentication failures", "AI service data access failures"])
        cache_failure = next((f for f in failures if f.component == ComponentType.CACHE), None)
        if cache_failure:
            cascade_effects.extend(["Increased database load", "Slower API response times", "Higher external API usage", "Rate limiting triggers"])
        ai_failure = next((f for f in failures if f.component == ComponentType.AI_SERVICE), None)
        if ai_failure:
            cascade_effects.extend(["Booking automation failures", "Reduced user experience", "Increased manual workload", "Customer support tickets increase"])
        return cascade_effects

    def _identify_critical_failure_points(self, failures: list[ComponentFailure]) -> list[str]:
        """Identify critical failure points that cause system-wide issues"""
        critical_points = []
        for failure in failures:
            if failure.severity in [FailureSeverity.CRITICAL, FailureSeverity.CATASTROPHIC]:
                critical_points.append(f"{failure.component.value}: {failure.failure_type}")
        critical_points.extend(["Database connection pool exhaustion", "Cache system failure", "API server memory exhaustion", "External API rate limiting"])
        return critical_points

    def _analyze_recovery_patterns(self, failures: list[ComponentFailure]) -> dict[str, Any]:
        """Analyze recovery patterns after failures"""
        recovery_analysis = {"auto_recovery_components": [], "manual_intervention_required": [], "recovery_times": {}, "recovery_strategies": {}}
        for failure in failures:
            if failure.recovery_time and failure.recovery_time < 60:
                recovery_analysis["auto_recovery_components"].append(failure.component.value)
                recovery_analysis["recovery_times"][failure.component.value] = failure.recovery_time
            else:
                recovery_analysis["manual_intervention_required"].append(failure.component.value)
                recovery_analysis["recovery_strategies"][failure.component.value] = self._suggest_recovery_strategy(failure)
        return recovery_analysis

    def _analyze_user_impact(self, failures: list[ComponentFailure], degradations: list[PerformanceDegradation]) -> dict[str, Any]:
        """Analyze impact on user experience"""
        impact_analysis = {"critical_functionality_lost": [], "degraded_functionality": [], "user_experience_impact": "minimal", "estimated_affected_users": 0}
        for failure in failures:
            if failure.severity in [FailureSeverity.CRITICAL, FailureSeverity.CATASTROPHIC]:
                impact_analysis["critical_functionality_lost"].append(failure.component.value)
        for degradation in degradations:
            if degradation.degradation_percentage > 50:
                impact_analysis["degraded_functionality"].append(degradation.component.value)
        if impact_analysis["critical_functionality_lost"]:
            impact_analysis["user_experience_impact"] = "severe"
        elif len(impact_analysis["degraded_functionality"]) > 3:
            impact_analysis["user_experience_impact"] = "significant"
        elif len(impact_analysis["degraded_functionality"]) > 0:
            impact_analysis["user_experience_impact"] = "moderate"
        return impact_analysis

    def _generate_failure_recommendations(self, failures: list[ComponentFailure], degradations: list[PerformanceDegradation], exhaustions: list[ResourceExhaustion]) -> list[str]:
        """Generate recommendations based on failure analysis"""
        recommendations = []
        db_failures = [f for f in failures if f.component == ComponentType.DATABASE]
        if db_failures:
            recommendations.extend(["Implement database connection pooling with proper limits", "Add database read replicas for load distribution", "Implement circuit breaker for database failures", "Add database monitoring and alerting", "Consider database sharding for horizontal scaling"])
        cache_failures = [f for f in failures if f.component == ComponentType.CACHE]
        if cache_failures:
            recommendations.extend(["Implement multi-tier caching (memory + Redis)", "Add cache fallback mechanisms", "Implement cache warming strategies", "Add cache monitoring and automatic eviction", "Consider CDN for static content"])
        api_failures = [f for f in failures if f.component == ComponentType.API_SERVER]
        if api_failures:
            recommendations.extend(["Implement horizontal scaling with load balancer", "Add API rate limiting", "Implement request queuing for overload protection", "Add API monitoring and circuit breakers", "Implement graceful degradation under load"])
        if exhaustions:
            recommendations.extend(["Implement resource monitoring and alerting", "Add auto-scaling based on resource usage", "Implement resource quotas and limits", "Add resource cleanup and garbage collection", "Consider container orchestration for resource management"])
        recommendations.extend(["Implement comprehensive monitoring and alerting", "Add chaos engineering practices to test resilience", "Implement disaster recovery procedures", "Add performance testing to CI/CD pipeline", "Create incident response playbooks"])
        return list(set(recommendations))

    def _map_failure_to_component(self, failure_data: dict) -> ComponentType:
        """Map failure data to system component"""
        failure_type = failure_data.get("failure_type", "")
        component = failure_data.get("component", "").lower()
        if "database" in failure_type or "database" in component:
            return ComponentType.DATABASE
        if "cache" in failure_type or "cache" in component:
            return ComponentType.CACHE
        if "cpu" in failure_type or "api" in component:
            return ComponentType.API_SERVER
        if "ai" in failure_type or "llm" in component:
            return ComponentType.AI_SERVICE
        if "calendar" in failure_type:
            return ComponentType.CALENDAR_SYNC
        if "payment" in failure_type:
            return ComponentType.PAYMENT_GATEWAY
        if "notification" in failure_type:
            return ComponentType.NOTIFICATION_SERVICE
        if "queue" in failure_type:
            return ComponentType.QUEUE_SYSTEM
        return ComponentType.API_SERVER

    def _map_resource_to_component(self, resource_type: str) -> ComponentType:
        """Map resource type to component"""
        if resource_type in ["cpu", "memory"] or resource_type == "network":
            return ComponentType.API_SERVER
        return ComponentType.API_SERVER

    def _map_bottleneck_to_component(self, bottleneck: dict) -> ComponentType:
        """Map bottleneck to component"""
        bottleneck_type = bottleneck.get("bottleneck_type", "")
        if "database" in bottleneck_type:
            return ComponentType.DATABASE
        if "cache" in bottleneck_type:
            return ComponentType.CACHE
        if "api" in bottleneck_type:
            return ComponentType.API_SERVER
        if "ai" in bottleneck_type:
            return ComponentType.AI_SERVICE
        return ComponentType.API_SERVER

    def _determine_failure_severity(self, failure_data: dict) -> FailureSeverity:
        """Determine failure severity based on failure data"""
        impact_severity = failure_data.get("impact_severity", "low")
        severity_mapping = {"low": FailureSeverity.DEGRADED, "medium": FailureSeverity.PARTIAL, "high": FailureSeverity.CRITICAL, "critical": FailureSeverity.CATASTROPHIC}
        return severity_mapping.get(impact_severity, FailureSeverity.DEGRADED)

    def _identify_root_cause(self, failure_data: dict, failure_order: int) -> str:
        """Identify root cause of failure"""
        failure_type = failure_data.get("failure_type", "")
        if failure_order == 0:
            if "cpu" in failure_type:
                return "CPU exhaustion due to insufficient compute resources"
            if "memory" in failure_type:
                return "Memory exhaustion due to high concurrent request processing"
            if "database" in failure_type:
                return "Database connection pool exhaustion"
            if "cache" in failure_type:
                return "Cache memory exhaustion or connection limits"
            return "Resource exhaustion under sudden load"
        return f"Cascade effect from previous failure: {failure_type}"

    def _assess_user_impact(self, component: ComponentType, failure_data: dict) -> str:
        """Assess impact on users"""
        impact_mapping = {ComponentType.DATABASE: "Complete system failure - no data persistence", ComponentType.CACHE: "Performance degradation - slower response times", ComponentType.API_SERVER: "Service unavailable - no API access", ComponentType.AI_SERVICE: "Feature degradation - AI functionality unavailable", ComponentType.CALENDAR_SYNC: "Feature degradation - calendar sync failures", ComponentType.PAYMENT_GATEWAY: "Feature degradation - payment processing failures", ComponentType.NOTIFICATION_SERVICE: "Feature degradation - notification delivery failures", ComponentType.QUEUE_SYSTEM: "Processing delays - background job failures"}
        return impact_mapping.get(component, "Unknown impact")

    def _assess_degradation_impact(self, resource_type: str, usage_value: float) -> str:
        """Assess impact of resource degradation"""
        if resource_type == "cpu" and usage_value > 90:
            return "Severe performance degradation, request timeouts"
        if resource_type == "memory" and usage_value > 85:
            return "Memory pressure, potential out-of-memory errors"
        if resource_type == "network" and usage_value > 1000000:
            return "Network congestion, slow data transfer"
        return "Performance degradation"

    def _identify_exhaustion_consequences(self, resource_type: str) -> list[str]:
        """Identify consequences of resource exhaustion"""
        consequences_mapping = {"cpu": ["Request timeouts", "Increased response times", "System unresponsiveness", "Potential server crashes"], "memory": ["Out-of-memory errors", "Process crashes", "Swap thrashing", "System instability"], "network": ["Connection timeouts", "Slow data transfer", "Failed requests", "Service unavailability"]}
        return consequences_mapping.get(resource_type, ["Unknown consequences"])

    def _identify_recovery_actions(self, resource_type: str) -> list[str]:
        """Identify recovery actions for resource exhaustion"""
        recovery_actions_mapping = {"cpu": ["Scale up CPU resources", "Implement request throttling", "Add load balancer with more instances", "Optimize CPU-intensive operations"], "memory": ["Increase memory allocation", "Implement memory optimization", "Add memory caching", "Restart affected services"], "network": ["Increase network bandwidth", "Implement request compression", "Add CDN for static content", "Optimize data transfer"]}
        return recovery_actions_mapping.get(resource_type, ["Unknown recovery actions"])

    def _suggest_recovery_strategy(self, failure: ComponentFailure) -> str:
        """Suggest recovery strategy for component failure"""
        strategy_mapping = {ComponentType.DATABASE: "Failover to read replica, then restart primary", ComponentType.CACHE: "Switch to fallback cache, then restart cache service", ComponentType.API_SERVER: "Scale up instances, then implement rate limiting", ComponentType.AI_SERVICE: "Switch to backup AI provider, then restart service", ComponentType.CALENDAR_SYNC: "Queue sync operations, then restart sync service", ComponentType.PAYMENT_GATEWAY: "Switch to backup payment provider", ComponentType.NOTIFICATION_SERVICE: "Queue notifications, then restart service", ComponentType.QUEUE_SYSTEM: "Clear queue backlog, then restart queue workers"}
        return strategy_mapping.get(failure.component, "Manual intervention required")
failure_analyzer = TrafficSpikeFailureAnalyzer()

def analyze_traffic_spike_failures(simulation_report: dict[str, Any]) -> dict[str, Any]:
    """Analyze failures from traffic spike simulation"""
    return failure_analyzer.analyze_failure_sequence(simulation_report)
