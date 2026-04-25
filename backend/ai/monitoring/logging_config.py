"""
Structured Logging for GraftAI Agent System

Provides comprehensive logging for agent activities, decisions,
and operations with structured JSON format for easy parsing.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from backend.utils.logger import get_logger


def _mask_email(email: str) -> str:
    if not isinstance(email, str) or "@" not in email:
        return "unknown"
    local, domain = email.split("@", 1)
    masked_local = f"{local[:1]}***" if local else "***"
    return f"{masked_local}@{domain}"


# Base logger
base_logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════
# AGENT LOGGER CLASS
# ═══════════════════════════════════════════════════════════════════


class AgentLogger:
    """
    Structured logger for agent activities

    Logs in JSON format for easy parsing and analysis.
    Supports multiple handlers (file, console, external).
    """

    def __init__(
        self,
        name: str = "agent",
        log_file: str = "logs/agent_activity.log",
        level: int = logging.INFO,
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers
        self.logger.handlers = []

        # Create log directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # File handler with JSON formatter
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(self._create_json_formatter())
        self.logger.addHandler(file_handler)

        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(self._create_console_formatter())
        self.logger.addHandler(console_handler)

        base_logger.info(f"AgentLogger initialized: {name} -> {log_file}")

    def _create_json_formatter(self) -> logging.Formatter:
        """Create JSON formatter for structured logging"""

        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }

                # Add extra fields if present
                if hasattr(record, "agent_data"):
                    log_data.update(record.agent_data)

                return json.dumps(log_data, default=str)

        return JsonFormatter()

    def _create_console_formatter(self) -> logging.Formatter:
        """Create console formatter for readable output"""
        return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log with optional structured data"""
        if extra:
            # Create custom record with extra data
            record = self.logger.makeRecord(
                self.name, level, "(unknown file)", 0, message, (), None
            )
            record.agent_data = extra
            self.logger.handle(record)
        else:
            self.logger.log(level, message)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info level"""
        self.log(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning level"""
        self.log(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error level"""
        self.log(logging.ERROR, message, extra)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug level"""
        self.log(logging.DEBUG, message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical level"""
        self.log(logging.CRITICAL, message, extra)


# ═══════════════════════════════════════════════════════════════════
# SPECIALIZED LOGGING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

_agent_logger: Optional[AgentLogger] = None


def get_agent_logger() -> AgentLogger:
    """Get or create the global agent logger"""
    global _agent_logger
    if _agent_logger is None:
        _agent_logger = AgentLogger()
    return _agent_logger


def log_agent_decision(
    booking_id: str,
    decision: str,
    confidence: float,
    reasoning: str,
    risk_level: str,
    actions: list,
    latency_ms: float,
):
    """
    Log an agent decision with full context

    Args:
        booking_id: Booking ID
        decision: Decision type
        confidence: Confidence score (0-1)
        reasoning: Reasoning text
        risk_level: Risk assessment
        actions: List of actions decided
        latency_ms: Decision latency in milliseconds
    """
    logger = get_agent_logger()

    logger.info(
        f"Agent decision for booking {booking_id}: {decision}",
        extra={
            "event_type": "agent_decision",
            "booking_id": booking_id,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning[:200],  # Truncate
            "risk_level": risk_level,
            "actions_count": len(actions),
            "actions": [a.get("tool_name", str(a)) for a in actions],
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def log_tool_execution(
    tool_name: str,
    booking_id: str,
    success: bool,
    duration_ms: float,
    result: Optional[Dict] = None,
    error: Optional[str] = None,
):
    """
    Log a tool execution

    Args:
        tool_name: Name of tool executed
        booking_id: Associated booking
        success: Whether execution succeeded
        duration_ms: Execution duration
        result: Execution result
        error: Error message if failed
    """
    logger = get_agent_logger()

    extra = {
        "event_type": "tool_execution",
        "tool_name": tool_name,
        "booking_id": booking_id,
        "success": success,
        "duration_ms": duration_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if result:
        extra["result"] = result

    if error:
        extra["error"] = error

    status = "success" if success else "failure"
    logger.info(
        f"Tool {tool_name} {status} for booking {booking_id}: {duration_ms:.0f}ms",
        extra=extra,
    )


def log_memory_operation(
    operation: str, layer: str, key: str, duration_ms: float, success: bool = True
):
    """
    Log a memory operation

    Args:
        operation: Operation type (store, retrieve, update, delete)
        layer: Memory layer (short_term, medium_term, long_term)
        key: Memory key
        duration_ms: Operation duration
        success: Whether operation succeeded
    """
    logger = get_agent_logger()

    logger.debug(
        f"Memory {operation} in {layer}: {key} ({duration_ms:.1f}ms)",
        extra={
            "event_type": "memory_operation",
            "operation": operation,
            "layer": layer,
            "key": key,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def log_automation_start(
    booking_id: str, attendee_email: str, booking_type: str, estimated_value: float = 0
):
    """
    Log automation start

    Args:
        booking_id: Booking ID
        attendee_email: Attendee email
        booking_type: Type of booking
        estimated_value: Estimated business value
    """
    logger = get_agent_logger()

    logger.info(
        f"Automation started for booking {booking_id}",
        extra={
            "event_type": "automation_start",
            "booking_id": booking_id,
            "attendee_id": _mask_email(attendee_email),
            "booking_type": booking_type,
            "estimated_value": estimated_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def log_automation_complete(
    booking_id: str,
    status: str,
    decision_score: int,
    risk_assessment: str,
    actions_executed: int,
    execution_time_ms: float,
    error: Optional[str] = None,
):
    """
    Log automation completion

    Args:
        booking_id: Booking ID
        status: Completion status
        decision_score: Quality score (0-100)
        risk_assessment: Risk level
        actions_executed: Number of actions executed
        execution_time_ms: Total execution time
        error: Error message if failed
    """
    logger = get_agent_logger()

    extra = {
        "event_type": "automation_complete",
        "booking_id": booking_id,
        "status": status,
        "decision_score": decision_score,
        "risk_assessment": risk_assessment,
        "actions_executed": actions_executed,
        "execution_time_ms": execution_time_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if error:
        extra["error"] = error

    logger.info(
        f"Automation {status} for booking {booking_id}: "
        f"score={decision_score}, risk={risk_assessment}, "
        f"actions={actions_executed}, time={execution_time_ms:.0f}ms",
        extra=extra,
    )


def log_phase_execution(
    booking_id: str, phase: str, duration_ms: float, success: bool = True
):
    """
    Log agent phase execution

    Args:
        booking_id: Booking ID
        phase: Phase name (perception, cognition, action, reflection)
        duration_ms: Phase duration
        success: Whether phase completed successfully
    """
    logger = get_agent_logger()

    logger.debug(
        f"Phase {phase} completed for booking {booking_id}: {duration_ms:.0f}ms",
        extra={
            "event_type": "phase_execution",
            "booking_id": booking_id,
            "phase": phase,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def log_llm_call(
    model: str,
    operation: str,
    tokens_used: int,
    latency_ms: float,
    status: str = "success",
):
    """
    Log LLM API call

    Args:
        model: LLM model name
        operation: Operation type
        tokens_used: Number of tokens used
        latency_ms: API call latency
        status: Call status
    """
    logger = get_agent_logger()

    logger.debug(
        f"LLM call to {model} for {operation}: {tokens_used} tokens, {latency_ms:.0f}ms",
        extra={
            "event_type": "llm_call",
            "model": model,
            "operation": operation,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def log_error(
    error_type: str,
    component: str,
    message: str,
    booking_id: Optional[str] = None,
    exception: Optional[Exception] = None,
):
    """
    Log an error

    Args:
        error_type: Type of error
        component: Component where error occurred
        message: Error message
        booking_id: Associated booking (if any)
        exception: Exception object
    """
    logger = get_agent_logger()

    extra = {
        "event_type": "error",
        "error_type": error_type,
        "component": component,
        "booking_id": booking_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if exception:
        extra["exception"] = str(exception)
        extra["exception_type"] = type(exception).__name__

    logger.error(f"Error in {component}: {message}", extra=extra)


# ═══════════════════════════════════════════════════════════════════
# LOG ANALYSIS UTILITIES
# ═══════════════════════════════════════════════════════════════════


class LogAnalyzer:
    """Analyze agent logs for insights"""

    def __init__(self, log_file: str = "logs/agent_activity.log"):
        self.log_file = log_file

    def parse_logs(self) -> list[Dict[str, Any]]:
        """Parse JSON logs into list of dicts"""
        logs = []

        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue  # Skip non-JSON lines
        except FileNotFoundError:
            base_logger.warning(f"Log file not found: {self.log_file}")

        return logs

    def get_automation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of automations in time window"""
        logs = self.parse_logs()

        # Filter by time and event type
        cutoff = datetime.now(timezone.utc) - __import__("datetime").timedelta(hours=hours)

        automations = [
            log
            for log in logs
            if log.get("event_type") in ["automation_start", "automation_complete"]
            and datetime.fromisoformat(log.get("timestamp", "1970-01-01")) > cutoff
        ]

        # Calculate metrics
        total = len(
            [a for a in automations if a.get("event_type") == "automation_start"]
        )
        completed = len([a for a in automations if a.get("status") == "completed"])
        failed = len([a for a in automations if a.get("status") == "failed"])

        avg_score = 0
        scores = [
            a.get("decision_score") for a in automations if a.get("decision_score")
        ]
        if scores:
            avg_score = sum(scores) / len(scores)

        return {
            "total_automations": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "average_decision_score": avg_score,
            "time_window_hours": hours,
        }

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of errors in time window"""
        logs = self.parse_logs()

        cutoff = datetime.now(timezone.utc) - __import__("datetime").timedelta(hours=hours)

        errors = [
            log
            for log in logs
            if log.get("event_type") == "error"
            and datetime.fromisoformat(log.get("timestamp", "1970-01-01")) > cutoff
        ]

        # Group by error type
        error_counts = {}
        for error in errors:
            error_type = error.get("error_type", "unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return {
            "total_errors": len(errors),
            "error_breakdown": error_counts,
            "time_window_hours": hours,
        }


# ═══════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test logging
    print("Testing AgentLogger...")

    logger = get_agent_logger()

    # Log various events
    log_automation_start(
        booking_id="booking_123",
        attendee_email="user@example.com",
        booking_type="consultation",
        estimated_value=500,
    )

    log_agent_decision(
        booking_id="booking_123",
        decision="high_risk_booking",
        confidence=0.85,
        reasoning="Attendee has 50% no-show rate",
        risk_level="high",
        actions=[{"tool_name": "send_email"}, {"tool_name": "send_sms"}],
        latency_ms=250,
    )

    log_tool_execution(
        tool_name="send_email",
        booking_id="booking_123",
        success=True,
        duration_ms=150,
        result={"email_id": "msg_12345"},
    )

    log_phase_execution(
        booking_id="booking_123", phase="cognition", duration_ms=300, success=True
    )

    log_automation_complete(
        booking_id="booking_123",
        status="completed",
        decision_score=85,
        risk_assessment="high",
        actions_executed=3,
        execution_time_ms=1200,
    )

    print("✅ Logging module working")
    print("Check logs/agent_activity.log for output")
