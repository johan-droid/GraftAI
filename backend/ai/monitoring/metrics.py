"""
Prometheus Metrics for GraftAI Agent System

Provides comprehensive metrics for monitoring agent performance,
decision quality, and system health.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
import time

# Try to import prometheus_client, provide fallback if not available
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry

    PROMETHEUS_AVAILABLE = True
    SHARED_REGISTRY = CollectorRegistry()
except ImportError:
    PROMETHEUS_AVAILABLE = False
    SHARED_REGISTRY = None

    # Create dummy classes for when prometheus is not installed
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def time(self):
            return self

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def dec(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class Info:
        def __init__(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

    class CollectorRegistry:
        pass


from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════
# PROMETHEUS METRICS DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

# Booking Automation Metrics
bookings_automated = Counter(
    "bookings_automated_total",
    "Total bookings automated by agent",
    ["status", "risk_level", "vip_level"],
    registry=SHARED_REGISTRY if PROMETHEUS_AVAILABLE else None,
)

agent_decision_latency = Histogram(
    "agent_decision_latency_seconds",
    "Time to make automation decision",
    ["decision_type"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=SHARED_REGISTRY if PROMETHEUS_AVAILABLE else None,
)

automation_execution_time = Histogram(
    "automation_execution_time_seconds",
    "Total automation execution time",
    ["scenario_type"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=SHARED_REGISTRY if PROMETHEUS_AVAILABLE else None,
)

automation_success_rate = Gauge(
    "automation_success_rate",
    "Percentage of successful automations",
    ["time_window"],
    registry=SHARED_REGISTRY if PROMETHEUS_AVAILABLE else None,
)

automation_decision_score = Histogram(
    "automation_decision_score",
    "Quality score of automation decisions (0-100)",
    buckets=[20, 40, 60, 80, 90, 95, 100],
    registry=SHARED_REGISTRY if PROMETHEUS_AVAILABLE else None,
)

# Tool Execution Metrics
tool_executions = Counter(
    "tool_executions_total",
    "Total tool executions",
    ["tool_name", "status", "category"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

tool_duration = Histogram(
    "tool_duration_seconds",
    "Tool execution duration",
    ["tool_name", "category"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

tool_retry_count = Counter(
    "tool_retry_count_total",
    "Number of tool retries",
    ["tool_name"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

# Agent Execution Metrics
agent_executions = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_type", "status", "phase"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

agent_duration = Histogram(
    "agent_duration_seconds",
    "Agent execution duration",
    ["agent_type", "phase"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

agent_phase_duration = Histogram(
    "agent_phase_duration_seconds",
    "Duration of each agent phase",
    ["agent_type", "phase"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

# Memory Metrics
memory_operations = Counter(
    "memory_operations_total",
    "Memory operations",
    ["layer", "operation"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

memory_latency = Histogram(
    "memory_latency_seconds",
    "Memory operation latency",
    ["layer", "operation"],
    buckets=[0.001, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

memory_size = Gauge(
    "memory_size_bytes",
    "Memory size in bytes",
    ["layer"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

# LLM Metrics
llm_tokens_used = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens used",
    ["model", "operation"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

llm_api_calls = Counter(
    "llm_api_calls_total",
    "Total LLM API calls",
    ["model", "status"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

llm_latency = Histogram(
    "llm_latency_seconds",
    "LLM API call latency",
    ["model", "operation"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

llm_cost = Counter(
    "llm_cost_dollars",
    "Estimated LLM cost in dollars",
    ["model"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

# System Metrics
active_automations = Gauge(
    "active_automations",
    "Number of currently running automations",
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

automation_queue_size = Gauge(
    "automation_queue_size",
    "Number of automations waiting in queue",
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

agent_errors = Counter(
    "agent_errors_total",
    "Total agent errors",
    ["error_type", "component"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

# Business Metrics
booking_value_automated = Counter(
    "booking_value_automated_dollars",
    "Total value of automated bookings",
    ["risk_level"],
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

attendee_satisfaction = Gauge(
    "attendee_satisfaction_score",
    "Average attendee satisfaction (0-10)",
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

no_show_rate = Gauge(
    "no_show_rate",
    "Percentage of no-shows after automation",
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

# Build Info
agent_build_info = Info(
    "agent_build",
    "Agent build information",
    registry=CollectorRegistry() if PROMETHEUS_AVAILABLE else None,
)

# Initialize build info
if PROMETHEUS_AVAILABLE:
    agent_build_info.info(
        {
            "version": "1.0.0",
            "build_date": datetime.now(timezone.utc).isoformat(),
            "python_version": "3.10+",
            "framework": "GraftAI",
        }
    )


# ═══════════════════════════════════════════════════════════════════
# AGENT METRICS CLASS
# ═══════════════════════════════════════════════════════════════════


class AgentMetrics:
    """
    Centralized metrics collection for the agent system

    Provides convenient methods for recording metrics across
    all agent components.
    """

    def __init__(self):
        self._automation_start_times: Dict[str, float] = {}
        self._agent_start_times: Dict[str, float] = {}
        self._tool_start_times: Dict[str, float] = {}
        self._memory_start_times: Dict[str, float] = {}
        self._llm_start_times: Dict[str, Tuple[str, str, float]] = {}

    # ═══════════════════════════════════════════════════════════════
    # BOOKING AUTOMATION METRICS
    # ═══════════════════════════════════════════════════════════════

    def record_automation_start(self, booking_id: str):
        """Record the start of an automation"""
        self._automation_start_times[booking_id] = time.time()
        active_automations.inc()

    def record_automation_complete(
        self,
        booking_id: str,
        status: str,
        risk_level: str,
        vip_level: str,
        decision_score: int,
        booking_value: float = 0,
    ):
        """Record automation completion"""
        # Record duration
        start_time = self._automation_start_times.pop(booking_id, None)
        if start_time:
            duration = time.time() - start_time
            automation_execution_time.labels(scenario_type=risk_level).observe(duration)

        # Record counters
        bookings_automated.labels(
            status=status, risk_level=risk_level, vip_level=vip_level
        ).inc()

        # Record decision score
        automation_decision_score.observe(decision_score)

        # Record value
        if booking_value > 0:
            booking_value_automated.labels(risk_level=risk_level).inc(booking_value)

        # Update active count
        active_automations.dec()

        logger.info(
            f"Automation complete: booking={booking_id}, "
            f"status={status}, score={decision_score}, "
            f"risk={risk_level}, vip={vip_level}"
        )

    def record_decision_latency(self, decision_type: str, latency_seconds: float):
        """Record decision-making latency"""
        agent_decision_latency.labels(decision_type=decision_type).observe(
            latency_seconds
        )

    def update_success_rate(self, time_window: str, rate: float):
        """Update success rate gauge"""
        automation_success_rate.labels(time_window=time_window).set(rate)

    # ═══════════════════════════════════════════════════════════════
    # TOOL EXECUTION METRICS
    # ═══════════════════════════════════════════════════════════════

    def record_tool_start(self, tool_name: str) -> str:
        """Record start of tool execution, returns tracking ID"""
        tracking_id = f"{tool_name}_{time.time()}"
        self._tool_start_times[tracking_id] = time.time()
        return tracking_id

    def record_tool_complete(
        self,
        tracking_id: str,
        tool_name: str,
        category: str,
        success: bool,
        retry_count: int = 0,
    ):
        """Record tool execution completion"""
        # Record duration
        start_time = self._tool_start_times.pop(tracking_id, None)
        if start_time:
            duration = time.time() - start_time
            tool_duration.labels(tool_name=tool_name, category=category).observe(
                duration
            )

        # Record execution
        status = "success" if success else "failure"
        tool_executions.labels(
            tool_name=tool_name, status=status, category=category
        ).inc()

        # Record retries
        if retry_count > 0:
            tool_retry_count.labels(tool_name=tool_name).inc(retry_count)

    # ═══════════════════════════════════════════════════════════════
    # AGENT EXECUTION METRICS
    # ═══════════════════════════════════════════════════════════════

    def record_agent_start(self, agent_type: str, phase: str) -> str:
        """Record start of agent execution, returns tracking ID"""
        tracking_id = f"{agent_type}_{phase}_{time.time()}"
        self._agent_start_times[tracking_id] = time.time()
        return tracking_id

    def record_agent_complete(
        self, tracking_id: str, agent_type: str, phase: str, status: str
    ):
        """Record agent execution completion"""
        # Record duration
        start_time = self._agent_start_times.pop(tracking_id, None)
        if start_time:
            duration = time.time() - start_time
            agent_duration.labels(agent_type=agent_type, phase=phase).observe(duration)
            agent_phase_duration.labels(agent_type=agent_type, phase=phase).observe(
                duration
            )

        # Record execution
        agent_executions.labels(agent_type=agent_type, status=status, phase=phase).inc()

    # ═══════════════════════════════════════════════════════════════
    # MEMORY METRICS
    # ═══════════════════════════════════════════════════════════════

    def record_memory_start(self, layer: str, operation: str) -> str:
        """Record start of memory operation"""
        tracking_id = f"{layer}_{operation}_{time.time()}"
        self._memory_start_times[tracking_id] = time.time()
        return tracking_id

    def record_memory_complete(self, tracking_id: str, layer: str, operation: str):
        """Record memory operation completion"""
        # Record operation
        memory_operations.labels(layer=layer, operation=operation).inc()

        # Record latency
        start_time = self._memory_start_times.pop(tracking_id, None)
        if start_time:
            latency = time.time() - start_time
            memory_latency.labels(layer=layer, operation=operation).observe(latency)

    def update_memory_size(self, layer: str, size_bytes: int):
        """Update memory size gauge"""
        memory_size.labels(layer=layer).set(size_bytes)

    # ═══════════════════════════════════════════════════════════════
    # LLM METRICS
    # ═══════════════════════════════════════════════════════════════

    def record_llm_start(self, model: str, operation: str) -> str:
        """Record start of LLM API call"""
        tracking_id = f"{model}_{operation}_{time.time()}"
        self._llm_start_times[tracking_id] = (model, operation, time.time())
        return tracking_id

    def record_llm_complete(
        self,
        tracking_id: str,
        tokens_used: int = 0,
        status: str = "success",
        cost: float = 0,
    ):
        """Record LLM API call completion"""
        info = self._llm_start_times.pop(tracking_id, None)
        if info:
            model, operation, start_time = info

            # Record latency
            latency = time.time() - start_time
            llm_latency.labels(model=model, operation=operation).observe(latency)

            # Record tokens
            if tokens_used > 0:
                llm_tokens_used.labels(model=model, operation=operation).inc(
                    tokens_used
                )

            # Record API call
            llm_api_calls.labels(model=model, status=status).inc()

            # Record cost
            if cost > 0:
                llm_cost.labels(model=model).inc(cost)

    # ═══════════════════════════════════════════════════════════════
    # ERROR METRICS
    # ═══════════════════════════════════════════════════════════════

    def record_error(self, error_type: str, component: str):
        """Record an error"""
        agent_errors.labels(error_type=error_type, component=component).inc()
        logger.error(f"Agent error: type={error_type}, component={component}")

    # ═══════════════════════════════════════════════════════════════
    # BUSINESS METRICS
    # ═══════════════════════════════════════════════════════════════

    def update_satisfaction_score(self, score: float):
        """Update attendee satisfaction gauge (0-10)"""
        attendee_satisfaction.set(score)

    def update_no_show_rate(self, rate: float):
        """Update no-show rate percentage"""
        no_show_rate.set(rate)

    # ═══════════════════════════════════════════════════════════════
    # QUEUE METRICS
    # ═══════════════════════════════════════════════════════════════

    def update_queue_size(self, size: int):
        """Update queue size gauge"""
        automation_queue_size.set(size)


# ═══════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════

_agent_metrics: Optional[AgentMetrics] = None


def get_agent_metrics() -> AgentMetrics:
    """Get or create the global agent metrics instance"""
    global _agent_metrics
    if _agent_metrics is None:
        _agent_metrics = AgentMetrics()
    return _agent_metrics


# ═══════════════════════════════════════════════════════════════════
# CONTEXT MANAGERS FOR CONVENIENCE
# ═══════════════════════════════════════════════════════════════════

from contextlib import contextmanager


@contextmanager
def measure_decision_latency(decision_type: str):
    """Context manager to measure decision latency"""
    metrics = get_agent_metrics()
    start = time.time()
    try:
        yield
    finally:
        latency = time.time() - start
        metrics.record_decision_latency(decision_type, latency)


@contextmanager
def measure_tool_execution(tool_name: str, category: str):
    """Context manager to measure tool execution"""
    metrics = get_agent_metrics()
    tracking_id = metrics.record_tool_start(tool_name)
    success = True
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        metrics.record_tool_complete(tracking_id, tool_name, category, success)


@contextmanager
def measure_agent_phase(agent_type: str, phase: str):
    """Context manager to measure agent phase execution"""
    metrics = get_agent_metrics()
    tracking_id = metrics.record_agent_start(agent_type, phase)
    status = "success"
    try:
        yield
    except Exception:
        status = "failure"
        raise
    finally:
        metrics.record_agent_complete(tracking_id, agent_type, phase, status)


@contextmanager
def measure_memory_operation(layer: str, operation: str):
    """Context manager to measure memory operation"""
    metrics = get_agent_metrics()
    tracking_id = metrics.record_memory_start(layer, operation)
    try:
        yield
    finally:
        metrics.record_memory_complete(tracking_id, layer, operation)


@contextmanager
def measure_llm_call(model: str, operation: str):
    """Context manager to measure LLM API call"""
    metrics = get_agent_metrics()
    tracking_id = metrics.record_llm_start(model, operation)
    status = "success"
    try:
        yield
    except Exception:
        status = "failure"
        raise
    finally:
        metrics.record_llm_complete(tracking_id, status=status)


# ═══════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════


async def example_metrics_usage():
    """Example of using metrics in code"""

    metrics = get_agent_metrics()

    # Record automation
    booking_id = "booking_123"
    metrics.record_automation_start(booking_id)

    # Simulate work
    import asyncio

    await asyncio.sleep(1)

    # Record completion
    metrics.record_automation_complete(
        booking_id=booking_id,
        status="completed",
        risk_level="medium",
        vip_level="standard",
        decision_score=85,
    )

    # Record decision latency
    with measure_decision_latency("risk_analysis"):
        # Risk analysis code here
        pass

    # Record tool execution
    with measure_tool_execution("send_email", "communication"):
        # Send email code here
        pass

    # Record memory operation
    with measure_memory_operation("medium_term", "store"):
        # Store in memory code here
        pass


if __name__ == "__main__":
    # Test metrics
    print("Testing AgentMetrics...")

    metrics = get_agent_metrics()

    # Record some metrics
    metrics.record_automation_start("test_booking")
    metrics.record_automation_complete(
        "test_booking", "completed", "low", "standard", 90
    )

    print("✅ Metrics module working")
