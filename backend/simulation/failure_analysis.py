"""
Traffic Spike Failure Analysis for GraftAI

Analyzes what fails first under sudden traffic spikes:
- Component failure sequencing
- Performance degradation patterns
- Resource exhaustion analysis
- Critical failure point identification
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
    DEGRADED = "degraded"      # Performance issues but functional
    PARTIAL = "partial"         # Some functionality broken
    CRITICAL = "critical"        # Major functionality broken
    CATASTROPHIC = "catastrophic" # System-wide failure


@dataclass
class ComponentFailure:
    """Component failure analysis"""
    component: ComponentType
    failure_type: str
    time_to_failure: float  # seconds from spike start
    severity: FailureSeverity
    symptoms: List[str]
    recovery_time: Optional[float] = None
    root_cause: str
    impact_on_users: str
    cascade_effects: List[str]


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
    consequences: List[str]
    recovery_actions: List[str]


class TrafficSpikeFailureAnalyzer:
    """Analyzes system failures during traffic spikes"""
    
    def __init__(self):
        self.component_failures: List[ComponentFailure] = []
        self.performance_degradations: List[PerformanceDegradation] = []
        self.resource_exhaustions: List[ResourceExhaustion] = []
        self.failure_timeline: List[Tuple[float, str]] = []
        
    def analyze_failure_sequence(self, simulation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the sequence of failures during traffic spike"""
        
        logger.info("Analyzing failure sequence from traffic spike simulation")
        
        # Extract failure points and resource usage
        failure_points = simulation_report.get("failure_points", [])
        resource_usage = simulation_report.get("resource_usage", {})
        bottlenecks = simulation_report.get("bottlenecks", [])
        
        # Analyze what fails first
        first_failures = self._identify_first_failures(failure_points)
        
        # Analyze performance degradation
        degradations = self._analyze_performance_degradation(bottlenecks, resource_usage)
        
        # Analyze resource exhaustion
        exhaustions = self._analyze_resource_exhaustion(resource_usage)
        
        # Identify cascade effects
        cascade_effects = self._identify_cascade_effects(first_failures, degradations, exhaustions)
        
        # Generate failure analysis report
        report = {
            "failure_sequence": {
                "first_to_fail": [asdict(f) for f in first_failures],
                "degradation_timeline": [asdict(d) for d in degradations],
                "resource_exhaustion": [asdict(e) for e in exhaustions],
                "cascade_effects": cascade_effects
            },
            "critical_failure_points": self._identify_critical_failure_points(first_failures),
            "recovery_analysis": self._analyze_recovery_patterns(first_failures),
            "user_impact_analysis": self._analyze_user_impact(first_failures, degradations),
            "recommendations": self._generate_failure_recommendations(first_failures, degradations, exhaustions)
        }
        
        return report
    
    def _identify_first_failures(self, failure_points: List[Dict]) -> List[ComponentFailure]:
        """Identify components that fail first"""
        first_failures = []
        
        # Sort failures by time to failure
        sorted_failures = sorted(failure_points, key=lambda f: f.get("time_to_failure", float('inf')))
        
        # Analyze first 3-5 failures
        for i, failure_data in enumerate(sorted_failures[:5]):
            component = self._map_failure_to_component(failure_data)
            
            failure = ComponentFailure(
                component=component,
                failure_type=failure_data.get("failure_type", "unknown"),
                time_to_failure=failure_data.get("time_to_failure", 0),
                severity=self._determine_failure_severity(failure_data),
                symptoms=failure_data.get("symptoms", []),
                root_cause=self._identify_root_cause(failure_data, i),
                impact_on_users=self._assess_user_impact(component, failure_data),
                cascade_effects=[]
            )
            
            first_failures.append(failure)
        
        return first_failures
    
    def _analyze_performance_degradation(self, bottlenecks: List[Dict], resource_usage: Dict) -> List[PerformanceDegradation]:
        """Analyze performance degradation patterns"""
        degradations = []
        
        # Analyze resource usage degradation
        for resource_type, usage_data in resource_usage.items():
            if isinstance(usage_data, dict) and "final" in usage_data and "avg" in usage_data:
                final_usage = usage_data["final"]
                baseline_usage = usage_data["avg"]
                
                if final_usage > baseline_usage * 1.5:  # 50% degradation
                    degradation = PerformanceDegradation(
                        component=self._map_resource_to_component(resource_type),
                        metric_name=f"{resource_type}_usage",
                        baseline_value=baseline_usage,
                        degraded_value=final_usage,
                        degradation_percentage=((final_usage - baseline_usage) / baseline_usage) * 100,
                        time_to_degradation=60,  # Estimated
                        user_impact=self._assess_degradation_impact(resource_type, final_usage)
                    )
                    degradations.append(degradation)
        
        # Analyze bottleneck degradation
        for bottleneck in bottlenecks:
            if bottleneck.get("peak_value", 0) > bottleneck.get("baseline_value", 0) * 2:
                degradation = PerformanceDegradation(
                    component=self._map_bottleneck_to_component(bottleneck),
                    metric_name=bottleneck.get("bottleneck_type", "unknown"),
                    baseline_value=bottleneck.get("baseline_value", 0),
                    degraded_value=bottleneck.get("peak_value", 0),
                    degradation_percentage=bottleneck.get("duration_above_threshold", 0),
                    time_to_degradation=bottleneck.get("time_to_peak", 0),
                    user_impact=bottleneck.get("impact_on_users", "Unknown impact")
                )
                degradations.append(degradation)
        
        return degradations
    
    def _analyze_resource_exhaustion(self, resource_usage: Dict) -> List[ResourceExhaustion]:
        """Analyze resource exhaustion patterns"""
        exhaustions = []
        
        # Define resource limits
        resource_limits = {
            "cpu": {"max": 100, "unit": "%"},
            "memory": {"max": 100, "unit": "%"},
            "network": {"max": 1000000000, "unit": "bytes"}  # 1GB
        }
        
        for resource_type, limits in resource_limits.items():
            if resource_type in resource_usage:
                usage_data = resource_usage[resource_type]
                max_usage = usage_data.get("max", 0)
                
                if max_usage >= limits["max"] * 0.95:  # 95% of capacity
                    exhaustion = ResourceExhaustion(
                        resource_type=f"{resource_type}_{limits['unit']}",
                        current_usage=max_usage,
                        maximum_capacity=limits["max"],
                        exhaustion_time=120,  # Estimated time to exhaustion
                        consequences=self._identify_exhaustion_consequences(resource_type),
                        recovery_actions=self._identify_recovery_actions(resource_type)
                    )
                    exhaustions.append(exhaustion)
        
        return exhaustions
    
    def _identify_cascade_effects(self, failures: List[ComponentFailure], 
                                degradations: List[PerformanceDegradation],
                                exhaustions: List[ResourceExhaustion]) -> List[str]:
        """Identify cascade effects between component failures"""
        cascade_effects = []
        
        # Database failure cascade
        db_failure = next((f for f in failures if f.component == ComponentType.DATABASE), None)
        if db_failure:
            cascade_effects.extend([
                "Calendar sync failures due to database unavailability",
                "Booking creation failures",
                "User authentication failures",
                "AI service data access failures"
            ])
        
        # Cache failure cascade
        cache_failure = next((f for f in failures if f.component == ComponentType.CACHE), None)
        if cache_failure:
            cascade_effects.extend([
                "Increased database load",
                "Slower API response times",
                "Higher external API usage",
                "Rate limiting triggers"
            ])
        
        # AI service failure cascade
        ai_failure = next((f for f in failures if f.component == ComponentType.AI_SERVICE), None)
        if ai_failure:
            cascade_effects.extend([
                "Booking automation failures",
                "Reduced user experience",
                "Increased manual workload",
                "Customer support tickets increase"
            ])
        
        return cascade_effects
    
    def _identify_critical_failure_points(self, failures: List[ComponentFailure]) -> List[str]:
        """Identify critical failure points that cause system-wide issues"""
        critical_points = []
        
        for failure in failures:
            if failure.severity in [FailureSeverity.CRITICAL, FailureSeverity.CATASTROPHIC]:
                critical_points.append(f"{failure.component.value}: {failure.failure_type}")
        
        # Add system-wide critical points
        critical_points.extend([
            "Database connection pool exhaustion",
            "Cache system failure",
            "API server memory exhaustion",
            "External API rate limiting"
        ])
        
        return critical_points
    
    def _analyze_recovery_patterns(self, failures: List[ComponentFailure]) -> Dict[str, Any]:
        """Analyze recovery patterns after failures"""
        recovery_analysis = {
            "auto_recovery_components": [],
            "manual_intervention_required": [],
            "recovery_times": {},
            "recovery_strategies": {}
        }
        
        for failure in failures:
            if failure.recovery_time and failure.recovery_time < 60:  # Auto recovery within 1 minute
                recovery_analysis["auto_recovery_components"].append(failure.component.value)
                recovery_analysis["recovery_times"][failure.component.value] = failure.recovery_time
            else:
                recovery_analysis["manual_intervention_required"].append(failure.component.value)
                recovery_analysis["recovery_strategies"][failure.component.value] = self._suggest_recovery_strategy(failure)
        
        return recovery_analysis
    
    def _analyze_user_impact(self, failures: List[ComponentFailure], 
                             degradations: List[PerformanceDegradation]) -> Dict[str, Any]:
        """Analyze impact on user experience"""
        impact_analysis = {
            "critical_functionality_lost": [],
            "degraded_functionality": [],
            "user_experience_impact": "minimal",
            "estimated_affected_users": 0
        }
        
        # Analyze critical functionality loss
        for failure in failures:
            if failure.severity in [FailureSeverity.CRITICAL, FailureSeverity.CATASTROPHIC]:
                impact_analysis["critical_functionality_lost"].append(failure.component.value)
        
        # Analyze degraded functionality
        for degradation in degradations:
            if degradation.degradation_percentage > 50:
                impact_analysis["degraded_functionality"].append(degradation.component.value)
        
        # Determine overall user experience impact
        if impact_analysis["critical_functionality_lost"]:
            impact_analysis["user_experience_impact"] = "severe"
        elif len(impact_analysis["degraded_functionality"]) > 3:
            impact_analysis["user_experience_impact"] = "significant"
        elif len(impact_analysis["degraded_functionality"]) > 0:
            impact_analysis["user_experience_impact"] = "moderate"
        
        return impact_analysis
    
    def _generate_failure_recommendations(self, failures: List[ComponentFailure],
                                     degradations: List[PerformanceDegradation],
                                     exhaustions: List[ResourceExhaustion]) -> List[str]:
        """Generate recommendations based on failure analysis"""
        recommendations = []
        
        # Database failure recommendations
        db_failures = [f for f in failures if f.component == ComponentType.DATABASE]
        if db_failures:
            recommendations.extend([
                "Implement database connection pooling with proper limits",
                "Add database read replicas for load distribution",
                "Implement circuit breaker for database failures",
                "Add database monitoring and alerting",
                "Consider database sharding for horizontal scaling"
            ])
        
        # Cache failure recommendations
        cache_failures = [f for f in failures if f.component == ComponentType.CACHE]
        if cache_failures:
            recommendations.extend([
                "Implement multi-tier caching (memory + Redis)",
                "Add cache fallback mechanisms",
                "Implement cache warming strategies",
                "Add cache monitoring and automatic eviction",
                "Consider CDN for static content"
            ])
        
        # API server failure recommendations
        api_failures = [f for f in failures if f.component == ComponentType.API_SERVER]
        if api_failures:
            recommendations.extend([
                "Implement horizontal scaling with load balancer",
                "Add API rate limiting",
                "Implement request queuing for overload protection",
                "Add API monitoring and circuit breakers",
                "Implement graceful degradation under load"
            ])
        
        # Resource exhaustion recommendations
        if exhaustions:
            recommendations.extend([
                "Implement resource monitoring and alerting",
                "Add auto-scaling based on resource usage",
                "Implement resource quotas and limits",
                "Add resource cleanup and garbage collection",
                "Consider container orchestration for resource management"
            ])
        
        # General recommendations
        recommendations.extend([
            "Implement comprehensive monitoring and alerting",
            "Add chaos engineering practices to test resilience",
            "Implement disaster recovery procedures",
            "Add performance testing to CI/CD pipeline",
            "Create incident response playbooks"
        ])
        
        return list(set(recommendations))
    
    def _map_failure_to_component(self, failure_data: Dict) -> ComponentType:
        """Map failure data to system component"""
        failure_type = failure_data.get("failure_type", "")
        component = failure_data.get("component", "").lower()
        
        if "database" in failure_type or "database" in component:
            return ComponentType.DATABASE
        elif "cache" in failure_type or "cache" in component:
            return ComponentType.CACHE
        elif "cpu" in failure_type or "api" in component:
            return ComponentType.API_SERVER
        elif "ai" in failure_type or "llm" in component:
            return ComponentType.AI_SERVICE
        elif "calendar" in failure_type:
            return ComponentType.CALENDAR_SYNC
        elif "payment" in failure_type:
            return ComponentType.PAYMENT_GATEWAY
        elif "notification" in failure_type:
            return ComponentType.NOTIFICATION_SERVICE
        elif "queue" in failure_type:
            return ComponentType.QUEUE_SYSTEM
        else:
            return ComponentType.API_SERVER  # Default
    
    def _map_resource_to_component(self, resource_type: str) -> ComponentType:
        """Map resource type to component"""
        if resource_type in ["cpu", "memory"]:
            return ComponentType.API_SERVER
        elif resource_type == "network":
            return ComponentType.API_SERVER
        else:
            return ComponentType.API_SERVER
    
    def _map_bottleneck_to_component(self, bottleneck: Dict) -> ComponentType:
        """Map bottleneck to component"""
        bottleneck_type = bottleneck.get("bottleneck_type", "")
        
        if "database" in bottleneck_type:
            return ComponentType.DATABASE
        elif "cache" in bottleneck_type:
            return ComponentType.CACHE
        elif "api" in bottleneck_type:
            return ComponentType.API_SERVER
        elif "ai" in bottleneck_type:
            return ComponentType.AI_SERVICE
        else:
            return ComponentType.API_SERVER
    
    def _determine_failure_severity(self, failure_data: Dict) -> FailureSeverity:
        """Determine failure severity based on failure data"""
        impact_severity = failure_data.get("impact_severity", "low")
        
        severity_mapping = {
            "low": FailureSeverity.DEGRADED,
            "medium": FailureSeverity.PARTIAL,
            "high": FailureSeverity.CRITICAL,
            "critical": FailureSeverity.CATASTROPHIC
        }
        
        return severity_mapping.get(impact_severity, FailureSeverity.DEGRADED)
    
    def _identify_root_cause(self, failure_data: Dict, failure_order: int) -> str:
        """Identify root cause of failure"""
        failure_type = failure_data.get("failure_type", "")
        
        # First failures are usually resource exhaustion
        if failure_order == 0:
            if "cpu" in failure_type:
                return "CPU exhaustion due to insufficient compute resources"
            elif "memory" in failure_type:
                return "Memory exhaustion due to high concurrent request processing"
            elif "database" in failure_type:
                return "Database connection pool exhaustion"
            elif "cache" in failure_type:
                return "Cache memory exhaustion or connection limits"
            else:
                return "Resource exhaustion under sudden load"
        
        # Later failures are often cascade effects
        else:
            return f"Cascade effect from previous failure: {failure_type}"
    
    def _assess_user_impact(self, component: ComponentType, failure_data: Dict) -> str:
        """Assess impact on users"""
        impact_mapping = {
            ComponentType.DATABASE: "Complete system failure - no data persistence",
            ComponentType.CACHE: "Performance degradation - slower response times",
            ComponentType.API_SERVER: "Service unavailable - no API access",
            ComponentType.AI_SERVICE: "Feature degradation - AI functionality unavailable",
            ComponentType.CALENDAR_SYNC: "Feature degradation - calendar sync failures",
            ComponentType.PAYMENT_GATEWAY: "Feature degradation - payment processing failures",
            ComponentType.NOTIFICATION_SERVICE: "Feature degradation - notification delivery failures",
            ComponentType.QUEUE_SYSTEM: "Processing delays - background job failures"
        }
        
        return impact_mapping.get(component, "Unknown impact")
    
    def _assess_degradation_impact(self, resource_type: str, usage_value: float) -> str:
        """Assess impact of resource degradation"""
        if resource_type == "cpu" and usage_value > 90:
            return "Severe performance degradation, request timeouts"
        elif resource_type == "memory" and usage_value > 85:
            return "Memory pressure, potential out-of-memory errors"
        elif resource_type == "network" and usage_value > 1000000:
            return "Network congestion, slow data transfer"
        else:
            return "Performance degradation"
    
    def _identify_exhaustion_consequences(self, resource_type: str) -> List[str]:
        """Identify consequences of resource exhaustion"""
        consequences_mapping = {
            "cpu": [
                "Request timeouts",
                "Increased response times",
                "System unresponsiveness",
                "Potential server crashes"
            ],
            "memory": [
                "Out-of-memory errors",
                "Process crashes",
                "Swap thrashing",
                "System instability"
            ],
            "network": [
                "Connection timeouts",
                "Slow data transfer",
                "Failed requests",
                "Service unavailability"
            ]
        }
        
        return consequences_mapping.get(resource_type, ["Unknown consequences"])
    
    def _identify_recovery_actions(self, resource_type: str) -> List[str]:
        """Identify recovery actions for resource exhaustion"""
        recovery_actions_mapping = {
            "cpu": [
                "Scale up CPU resources",
                "Implement request throttling",
                "Add load balancer with more instances",
                "Optimize CPU-intensive operations"
            ],
            "memory": [
                "Increase memory allocation",
                "Implement memory optimization",
                "Add memory caching",
                "Restart affected services"
            ],
            "network": [
                "Increase network bandwidth",
                "Implement request compression",
                "Add CDN for static content",
                "Optimize data transfer"
            ]
        }
        
        return recovery_actions_mapping.get(resource_type, ["Unknown recovery actions"])
    
    def _suggest_recovery_strategy(self, failure: ComponentFailure) -> str:
        """Suggest recovery strategy for component failure"""
        strategy_mapping = {
            ComponentType.DATABASE: "Failover to read replica, then restart primary",
            ComponentType.CACHE: "Switch to fallback cache, then restart cache service",
            ComponentType.API_SERVER: "Scale up instances, then implement rate limiting",
            ComponentType.AI_SERVICE: "Switch to backup AI provider, then restart service",
            ComponentType.CALENDAR_SYNC: "Queue sync operations, then restart sync service",
            ComponentType.PAYMENT_GATEWAY: "Switch to backup payment provider",
            ComponentType.NOTIFICATION_SERVICE: "Queue notifications, then restart service",
            ComponentType.QUEUE_SYSTEM: "Clear queue backlog, then restart queue workers"
        }
        
        return strategy_mapping.get(failure.component, "Manual intervention required")


# Global failure analyzer
failure_analyzer = TrafficSpikeFailureAnalyzer()


def analyze_traffic_spike_failures(simulation_report: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze failures from traffic spike simulation"""
    return failure_analyzer.analyze_failure_sequence(simulation_report)
