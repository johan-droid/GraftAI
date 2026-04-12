"""
Monitoring and Observability for GraftAI Agent System

Provides Prometheus metrics and structured logging for the AI components.
"""

from .metrics import (
    AgentMetrics,
    get_agent_metrics,
    bookings_automated,
    agent_decision_latency,
    automation_success_rate,
    tool_executions,
    tool_duration,
    agent_executions,
    agent_duration,
    memory_operations,
    llm_tokens_used,
    llm_api_calls
)

from .logging_config import (
    AgentLogger,
    get_agent_logger,
    log_agent_decision,
    log_tool_execution,
    log_memory_operation,
    LogAnalyzer,
)

__all__ = [
    # Metrics
    "AgentMetrics",
    "get_agent_metrics",
    "bookings_automated",
    "agent_decision_latency",
    "automation_success_rate",
    "tool_executions",
    "tool_duration",
    "agent_executions",
    "agent_duration",
    "memory_operations",
    "llm_tokens_used",
    "llm_api_calls",
    # Logging
    "AgentLogger",
    "get_agent_logger",
    "log_agent_decision",
    "log_tool_execution",
    "log_memory_operation",
    "LogAnalyzer",
]
