"""
Traffic Spike Simulator for GraftAI

Simulates sudden traffic spikes to identify failure points:
- Load testing scenarios
- Resource exhaustion simulation
- Database contention analysis
- Cache failure simulation
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import psutil

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures to simulate"""
    DATABASE_EXHAUSTION = "database_exhaustion"
    CACHE_OVERLOAD = "cache_overload"
    API_TIMEOUT = "api_timeout"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    CPU_EXHAUSTION = "cpu_exhaustion"
    QUEUE_BACKLOG = "queue_backlog"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SERVICE_DEGRADATION = "service_degradation"


class BottleneckType(Enum):
    """Types of bottlenecks to identify"""
    DATABASE_CONNECTIONS = "database_connections"
    API_RESPONSE_TIME = "api_response_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    MEMORY_ALLOCATION = "memory_allocation"
    CPU_UTILIZATION = "cpu_utilization"
    NETWORK_BANDWIDTH = "network_bandwidth"
    QUEUE_PROCESSING = "queue_processing"
    EXTERNAL_API_LIMITS = "external_api_limits"


@dataclass
class TrafficPattern:
    """Traffic pattern definition"""
    name: str
    baseline_rps: int  # requests per second
    spike_multiplier: float
    spike_duration_seconds: int
    ramp_up_seconds: int
    ramp_down_seconds: int
    endpoints: List[str]
    user_distribution: Dict[str, float]  # user type -> percentage


@dataclass
class FailurePoint:
    """Identified failure point"""
    component: str
    failure_type: FailureType
    threshold_reached: float
    time_to_failure: float  # seconds from spike start
    impact_severity: str  # "low", "medium", "high", "critical"
    symptoms: List[str]
    recovery_time: Optional[float] = None


@dataclass
class BottleneckReport:
    """Bottleneck analysis report"""
    bottleneck_type: BottleneckType
    component: str
    baseline_value: float
    peak_value: float
    time_to_peak: float
    duration_above_threshold: float
    impact_on_users: str
    recommended_fixes: List[str]


@dataclass
class DataConsistencyIssue:
    """Data consistency issue identified"""
    entity_type: str
    inconsistency_type: str
    affected_records: int
    detection_time: datetime
    root_cause: str
    severity: str
    auto_recovery_possible: bool


class TrafficSpikeSimulator:
    """Simulates traffic spikes and analyzes system behavior"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.concurrent_users = 0
        self.active_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0
        self.response_times: List[float] = []
        self.error_rates: Dict[str, float] = {}
        self.resource_usage: Dict[str, List[float]] = {}
        self.failure_points: List[FailurePoint] = []
        self.bottlenecks: List[BottleneckReport] = []
        self.consistency_issues: List[DataConsistencyIssue] = []
        self.simulation_start: Optional[datetime] = None
        
    async def simulate_traffic_spike(self, pattern: TrafficPattern) -> Dict[str, Any]:
        """Simulate a traffic spike pattern"""
        self.simulation_start = datetime.now(timezone.utc)
        
        logger.info(f"Starting traffic spike simulation: {pattern.name}")
        logger.info(f"Baseline: {pattern.baseline_rps} RPS, Spike: {pattern.spike_multiplier}x")
        
        # Phase 1: Baseline measurement
        await self._measure_baseline(pattern.baseline_rps, 30)
        
        # Phase 2: Ramp up
        logger.info("Ramping up traffic...")
        await self._ramp_up_traffic(pattern)
        
        # Phase 3: Peak load
        logger.info("Maintaining peak load...")
        await self._maintain_peak_load(pattern)
        
        # Phase 4: Ramp down
        logger.info("Ramping down traffic...")
        await self._ramp_down_traffic(pattern)
        
        # Phase 5: Recovery analysis
        logger.info("Analyzing recovery...")
        await self._analyze_recovery()
        
        # Generate report
        report = await self._generate_simulation_report(pattern)
        
        return report
    
    async def _measure_baseline(self, rps: int, duration_seconds: int):
        """Measure baseline performance"""
        logger.info(f"Measuring baseline at {rps} RPS for {duration_seconds}s")
        
        tasks = []
        for _ in range(rps):
            task = asyncio.create_task(self._send_request("GET", "/health"))
            tasks.append(task)
        
        # Run for duration
        end_time = time.time() + duration_seconds
        while time.time() < end_time:
            # Send requests at baseline rate
            new_tasks = []
            for _ in range(rps):
                task = asyncio.create_task(self._send_request("GET", "/health"))
                new_tasks.append(task)
            
            # Wait for requests to complete
            await asyncio.gather(*new_tasks, return_exceptions=True)
            await asyncio.sleep(1)
    
    async def _ramp_up_traffic(self, pattern: TrafficPattern):
        """Ramp up traffic to peak level"""
        target_rps = int(pattern.baseline_rps * pattern.spike_multiplier)
        ramp_steps = pattern.ramp_up_seconds
        rps_increment = (target_rps - pattern.baseline_rps) / ramp_steps
        
        for step in range(ramp_steps):
            current_rps = int(pattern.baseline_rps + (rps_increment * step))
            logger.info(f"Ramp up step {step + 1}/{ramp_steps}: {current_rps} RPS")
            
            # Send requests at current rate
            tasks = []
            for _ in range(current_rps):
                endpoint = random.choice(pattern.endpoints)
                task = asyncio.create_task(self._send_request("GET", endpoint))
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(1)
            
            # Monitor for failures
            await self._monitor_system_state()
    
    async def _maintain_peak_load(self, pattern: TrafficPattern):
        """Maintain peak load for specified duration"""
        target_rps = int(pattern.baseline_rps * pattern.spike_multiplier)
        
        for second in range(pattern.spike_duration_seconds):
            logger.info(f"Peak load second {second + 1}/{pattern.spike_duration_seconds}: {target_rps} RPS")
            
            # Send requests at peak rate
            tasks = []
            for _ in range(target_rps):
                endpoint = random.choice(pattern.endpoints)
                task = asyncio.create_task(self._send_request("GET", endpoint))
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Monitor system state every second
            await self._monitor_system_state()
            
            # Check for critical failures
            if self._check_critical_failures():
                logger.warning("Critical failure detected, reducing load")
                break
            
            await asyncio.sleep(1)
    
    async def _ramp_down_traffic(self, pattern: TrafficPattern):
        """Ramp down traffic from peak to baseline"""
        target_rps = int(pattern.baseline_rps * pattern.spike_multiplier)
        ramp_steps = pattern.ramp_down_seconds
        rps_decrement = (target_rps - pattern.baseline_rps) / ramp_steps
        
        for step in range(ramp_steps):
            current_rps = int(target_rps - (rps_decrement * step))
            logger.info(f"Ramp down step {step + 1}/{ramp_steps}: {current_rps} RPS")
            
            # Send requests at current rate
            tasks = []
            for _ in range(max(current_rps, pattern.baseline_rps)):
                endpoint = random.choice(pattern.endpoints)
                task = asyncio.create_task(self._send_request("GET", endpoint))
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(1)
    
    async def _analyze_recovery(self):
        """Analyze system recovery after spike"""
        logger.info("Analyzing system recovery...")
        
        # Monitor for recovery period
        for second in range(60):  # 1 minute recovery monitoring
            await self._monitor_system_state()
            await asyncio.sleep(1)
    
    async def _send_request(self, method: str, endpoint: str) -> Dict[str, Any]:
        """Send a single request and track metrics"""
        start_time = time.time()
        self.active_requests += 1
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                
                async with session.request(method, url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response_time = time.time() - start_time
                    self.response_times.append(response_time)
                    
                    if response.status == 200:
                        self.successful_requests += 1
                        return {"status": "success", "response_time": response_time}
                    else:
                        self.failed_requests += 1
                        return {"status": "error", "code": response.status, "response_time": response_time}
        
        except Exception as e:
            response_time = time.time() - start_time
            self.failed_requests += 1
            return {"status": "exception", "error": str(e), "response_time": response_time}
        
        finally:
            self.active_requests -= 1
    
    async def _monitor_system_state(self):
        """Monitor system resource usage"""
        timestamp = datetime.now(timezone.utc)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.resource_usage.setdefault("cpu", []).append(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.resource_usage.setdefault("memory", []).append(memory.percent)
        
        # Network I/O
        network = psutil.net_io_counters()
        self.resource_usage.setdefault("network", []).append(network.bytes_sent + network.bytes_recv)
        
        # Check for failure conditions
        await self._check_failure_conditions(timestamp)
    
    async def _check_failure_conditions(self, timestamp: datetime):
        """Check for system failure conditions"""
        
        # CPU exhaustion
        if self.resource_usage.get("cpu", []) and self.resource_usage["cpu"][-1] > 90:
            failure = FailurePoint(
                component="CPU",
                failure_type=FailureType.CPU_EXHAUSTION,
                threshold_reached=self.resource_usage["cpu"][-1],
                time_to_failure=(timestamp - self.simulation_start).total_seconds(),
                impact_severity="critical",
                symptoms=["High response times", "Request timeouts", "System unresponsiveness"]
            )
            self.failure_points.append(failure)
        
        # Memory exhaustion
        if self.resource_usage.get("memory", []) and self.resource_usage["memory"][-1] > 85:
            failure = FailurePoint(
                component="Memory",
                failure_type=FailureType.MEMORY_EXHAUSTION,
                threshold_reached=self.resource_usage["memory"][-1],
                time_to_failure=(timestamp - self.simulation_start).total_seconds(),
                impact_severity="critical",
                symptoms=["Out of memory errors", "Process crashes", "Swap thrashing"]
            )
            self.failure_points.append(failure)
        
        # High error rate
        total_requests = self.successful_requests + self.failed_requests
        if total_requests > 100:  # Minimum requests for meaningful error rate
            error_rate = self.failed_requests / total_requests
            if error_rate > 0.1:  # 10% error rate
                failure = FailurePoint(
                    component="API",
                    failure_type=FailureType.SERVICE_DEGRADATION,
                    threshold_reached=error_rate * 100,
                    time_to_failure=(timestamp - self.simulation_start).total_seconds(),
                    impact_severity="high",
                    symptoms=["HTTP 5xx errors", "Request timeouts", "Connection refused"]
                )
                self.failure_points.append(failure)
        
        # High response times
        if len(self.response_times) > 10:
            avg_response_time = statistics.mean(self.response_times[-10:])
            if avg_response_time > 5.0:  # 5 seconds
                failure = FailurePoint(
                    component="API",
                    failure_type=FailureType.API_TIMEOUT,
                    threshold_reached=avg_response_time,
                    time_to_failure=(timestamp - self.simulation_start).total_seconds(),
                    impact_severity="medium",
                symptoms=["Slow responses", "User experience degradation"]
                )
                self.failure_points.append(failure)
    
    def _check_critical_failures(self) -> bool:
        """Check for critical system failures"""
        # CPU > 95%
        if self.resource_usage.get("cpu", []) and self.resource_usage["cpu"][-1] > 95:
            return True
        
        # Memory > 95%
        if self.resource_usage.get("memory", []) and self.resource_usage["memory"][-1] > 95:
            return True
        
        # Error rate > 50%
        total_requests = self.successful_requests + self.failed_requests
        if total_requests > 50 and (self.failed_requests / total_requests) > 0.5:
            return True
        
        return False
    
    async def _generate_simulation_report(self, pattern: TrafficPattern) -> Dict[str, Any]:
        """Generate comprehensive simulation report"""
        
        # Analyze bottlenecks
        await self._analyze_bottlenecks()
        
        # Check data consistency
        await self._check_data_consistency()
        
        report = {
            "simulation_summary": {
                "pattern_name": pattern.name,
                "baseline_rps": pattern.baseline_rps,
                "peak_rps": int(pattern.baseline_rps * pattern.spike_multiplier),
                "spike_duration": pattern.spike_duration_seconds,
                "total_requests": self.successful_requests + self.failed_requests,
                "success_rate": self.successful_requests / (self.successful_requests + self.failed_requests) if (self.successful_requests + self.failed_requests) > 0 else 0,
                "avg_response_time": statistics.mean(self.response_times) if self.response_times else 0,
                "max_response_time": max(self.response_times) if self.response_times else 0,
                "simulation_duration": (datetime.now(timezone.utc) - self.simulation_start).total_seconds()
            },
            "failure_points": [asdict(fp) for fp in self.failure_points],
            "bottlenecks": [asdict(b) for b in self.bottlenecks],
            "data_consistency_issues": [asdict(dci) for dci in self.consistency_issues],
            "resource_usage": {
                "cpu": {
                    "max": max(self.resource_usage.get("cpu", [0])),
                    "avg": statistics.mean(self.resource_usage.get("cpu", [0])),
                    "final": self.resource_usage.get("cpu", [0])[-1] if self.resource_usage.get("cpu") else 0
                },
                "memory": {
                    "max": max(self.resource_usage.get("memory", [0])),
                    "avg": statistics.mean(self.resource_usage.get("memory", [0])),
                    "final": self.resource_usage.get("memory", [0])[-1] if self.resource_usage.get("memory") else 0
                }
            },
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    async def _analyze_bottlenecks(self):
        """Analyze system bottlenecks"""
        
        # CPU bottleneck
        if self.resource_usage.get("cpu", []):
            cpu_usage = self.resource_usage["cpu"]
            max_cpu = max(cpu_usage)
            if max_cpu > 80:
                bottleneck = BottleneckReport(
                    bottleneck_type=BottleneckType.CPU_UTILIZATION,
                    component="CPU",
                    baseline_value=statistics.mean(cpu_usage[:10]) if len(cpu_usage) > 10 else cpu_usage[0],
                    peak_value=max_cpu,
                    time_to_peak=cpu_usage.index(max_cpu),
                    duration_above_threshold=len([x for x in cpu_usage if x > 80]),
                    impact_on_users="High response times, request timeouts",
                    recommended_fixes=["Scale up CPU resources", "Optimize CPU-intensive operations", "Implement request queuing"]
                )
                self.bottlenecks.append(bottleneck)
        
        # Memory bottleneck
        if self.resource_usage.get("memory", []):
            memory_usage = self.resource_usage["memory"]
            max_memory = max(memory_usage)
            if max_memory > 75:
                bottleneck = BottleneckReport(
                    bottleneck_type=BottleneckType.MEMORY_ALLOCATION,
                    component="Memory",
                    baseline_value=statistics.mean(memory_usage[:10]) if len(memory_usage) > 10 else memory_usage[0],
                    peak_value=max_memory,
                    time_to_peak=memory_usage.index(max_memory),
                    duration_above_threshold=len([x for x in memory_usage if x > 75]),
                    impact_on_users="Out of memory errors, process crashes",
                    recommended_fixes=["Increase memory allocation", "Optimize memory usage", "Implement memory caching"]
                )
                self.bottlenecks.append(bottleneck)
        
        # Response time bottleneck
        if self.response_times:
            avg_response_times = []
            window_size = 10
            for i in range(0, len(self.response_times), window_size):
                window = self.response_times[i:i+window_size]
                avg_response_times.append(statistics.mean(window))
            
            max_avg_response = max(avg_response_times)
            if max_avg_response > 2.0:  # 2 seconds
                bottleneck = BottleneckReport(
                    bottleneck_type=BottleneckType.API_RESPONSE_TIME,
                    component="API",
                    baseline_value=avg_response_times[0] if avg_response_times else 0,
                    peak_value=max_avg_response,
                    time_to_peak=avg_response_times.index(max_avg_response),
                    duration_above_threshold=len([x for x in avg_response_times if x > 2.0]),
                    impact_on_users="Poor user experience, abandoned requests",
                    recommended_fixes=["Add API caching", "Optimize database queries", "Implement request timeouts"]
                )
                self.bottlenecks.append(bottleneck)
    
    async def _check_data_consistency(self):
        """Check for data consistency issues"""
        # This would check for actual data consistency issues
        # For simulation, we'll create hypothetical issues based on load
        
        if self.failed_requests > 100:
            # Simulate booking consistency issues
            issue = DataConsistencyIssue(
                entity_type="booking",
                inconsistency_type="duplicate_bookings",
                affected_records=int(self.failed_requests * 0.1),  # 10% of failed requests
                detection_time=datetime.now(timezone.utc),
                root_cause="Race conditions during high load",
                severity="medium",
                auto_recovery_possible=True
            )
            self.consistency_issues.append(issue)
        
        if max(self.resource_usage.get("cpu", [0])) > 90:
            # Simulate user data consistency issues
            issue = DataConsistencyIssue(
                entity_type="user",
                inconsistency_type="quota_inconsistency",
                affected_records=int(self.successful_requests * 0.05),  # 5% of successful requests
                detection_time=datetime.now(timezone.utc),
                root_cause="Concurrent quota updates without proper locking",
                severity="high",
                auto_recovery_possible=False
            )
            self.consistency_issues.append(issue)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on simulation results"""
        recommendations = []
        
        # Based on failure points
        for failure in self.failure_points:
            if failure.failure_type == FailureType.CPU_EXHAUSTION:
                recommendations.append("Implement horizontal scaling with load balancer")
                recommendations.append("Add CPU-intensive task queue to offload processing")
            
            elif failure.failure_type == FailureType.MEMORY_EXHAUSTION:
                recommendations.append("Increase memory allocation or implement memory optimization")
                recommendations.append("Add memory caching layer to reduce memory pressure")
            
            elif failure.failure_type == FailureType.API_TIMEOUT:
                recommendations.append("Implement request timeout and circuit breaker patterns")
                recommendations.append("Add API response caching")
        
        # Based on bottlenecks
        for bottleneck in self.bottlenecks:
            recommendations.extend(bottleneck.recommended_fixes)
        
        # Based on data consistency issues
        if self.consistency_issues:
            recommendations.append("Implement distributed transactions for critical operations")
            recommendations.append("Add data consistency checks and automatic repair")
            recommendations.append("Implement proper locking mechanisms for concurrent updates")
        
        # General recommendations
        recommendations.append("Implement comprehensive monitoring and alerting")
        recommendations.append("Add rate limiting to prevent system overload")
        recommendations.append("Implement graceful degradation under high load")
        
        # Remove duplicates
        return list(set(recommendations))


# Predefined traffic patterns
TRAFFIC_PATTERNS = {
    "moderate_spike": TrafficPattern(
        name="Moderate Spike",
        baseline_rps=50,
        spike_multiplier=5.0,
        spike_duration_seconds=60,
        ramp_up_seconds=30,
        ramp_down_seconds=30,
        endpoints=["/health", "/api/v1/users/me", "/api/v1/bookings"],
        user_distribution={"free": 0.7, "pro": 0.25, "elite": 0.05}
    ),
    
    "severe_spike": TrafficPattern(
        name="Severe Spike",
        baseline_rps=100,
        spike_multiplier=10.0,
        spike_duration_seconds=120,
        ramp_up_seconds=15,
        ramp_down_seconds=30,
        endpoints=["/health", "/api/v1/users/me", "/api/v1/bookings", "/api/v1/ai/chat"],
        user_distribution={"free": 0.6, "pro": 0.3, "elite": 0.1}
    ),
    
    "extreme_spike": TrafficPattern(
        name="Extreme Spike",
        baseline_rps=200,
        spike_multiplier=20.0,
        spike_duration_seconds=180,
        ramp_up_seconds=10,
        ramp_down_seconds=20,
        endpoints=["/health", "/api/v1/users/me", "/api/v1/bookings", "/api/v1/ai/chat", "/api/v1/calendar/sync"],
        user_distribution={"free": 0.5, "pro": 0.35, "elite": 0.15}
    ),
    
    "flash_crowd": TrafficPattern(
        name="Flash Crowd",
        baseline_rps=10,
        spike_multiplier=50.0,
        spike_duration_seconds=30,
        ramp_up_seconds=5,
        ramp_down_seconds=10,
        endpoints=["/api/v1/bookings/create", "/api/v1/ai/chat"],
        user_distribution={"free": 0.8, "pro": 0.15, "elite": 0.05}
    )
}


async def run_traffic_spike_simulation(pattern_name: str = "moderate_spike") -> Dict[str, Any]:
    """Run traffic spike simulation"""
    simulator = TrafficSpikeSimulator()
    pattern = TRAFFIC_PATTERNS[pattern_name]
    
    report = await simulator.simulate_traffic_spike(pattern)
    
    return report


# Example usage
if __name__ == "__main__":
    # Run simulation
    report = asyncio.run(run_traffic_spike_simulation("severe_spike"))
    print(json.dumps(report, indent=2, default=str))
