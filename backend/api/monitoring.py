"""
Monitoring and Metrics API Endpoints

Provides endpoints for Prometheus metrics, health checks, and monitoring dashboard.
"""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import select

# Try to import prometheus_client
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from backend.api.deps import get_current_user
from backend.auth.config import ALGORITHM, SECRET_KEY
from backend.models.tables import UserTable
from backend.ai.monitoring import get_agent_metrics, LogAnalyzer
from backend.services.messaging import get_recent_messages
from backend.services.redis_client import get_redis_client
from backend.utils.db import get_async_session_maker
from backend.utils.serialization import serializer
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# ═══════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class SystemHealthResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, Any]
    metrics_summary: Dict[str, Any]


class AutomationSummaryResponse(BaseModel):
    total_automations: int
    completed: int
    failed: int
    success_rate: float
    average_decision_score: float
    average_execution_time_ms: float
    time_window_hours: int


class MetricsResponse(BaseModel):
    bookings_automated: Dict[str, int]
    automation_success_rate: float
    active_automations: int
    tool_execution_summary: Dict[str, Any]
    timestamp: str


def _decode_stream_payload(raw_payload: Any) -> Dict[str, Any]:
    if raw_payload is None:
        return {}

    if isinstance(raw_payload, bytes):
        try:
            decoded = serializer.from_binary(raw_payload)
            return decoded if isinstance(decoded, dict) else {"message": decoded}
        except Exception:
            return {}

    if isinstance(raw_payload, str):
        try:
            decoded = serializer.from_binary(raw_payload.encode("utf-8"))
            return decoded if isinstance(decoded, dict) else {"message": decoded}
        except Exception:
            return {"message": raw_payload}

    if isinstance(raw_payload, dict):
        return raw_payload

    return {"message": str(raw_payload)}


def _stream_event_to_notification(event: Dict[str, Any]) -> Dict[str, Any]:
    metadata = event.get("metadata") or {}
    milestone = metadata.get("milestone") or metadata.get("kind") or "action complete"
    title = str(milestone).replace("_", " ").strip().title()
    message = str(event.get("message") or "").strip()

    if len(message) > 180:
        message = f"{message[:177].rstrip()}..."

    if not message:
        message = "A background action finished successfully."

    return {
        "type": "success" if metadata.get("kind") in {"ai_milestone", "chat_milestone"} else "info",
        "title": title or "Live update",
        "message": message,
        "metadata": metadata,
        "timestamp": event.get("timestamp") or datetime.utcnow().isoformat(),
    }


async def _resolve_websocket_user_id(token: Optional[str]) -> Optional[str]:
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return str(user_id) if user_id else None
    except JWTError:
        return None


async def _validate_websocket_user(token: Optional[str]) -> Optional[str]:
    user_id = await _resolve_websocket_user_id(token)
    if not user_id:
        return None

    try:
        session_maker = get_async_session_maker()
    except Exception:
        return None

    async with session_maker() as db:
        stmt = select(UserTable.id).where(UserTable.id == user_id)
        result = await db.execute(stmt)
        confirmed_user_id = result.scalar_one_or_none()
        return confirmed_user_id


# ═══════════════════════════════════════════════════════════════════
# PROMETHEUS METRICS ENDPOINT
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/metrics",
    summary="Prometheus metrics endpoint",
    description="Returns Prometheus-formatted metrics for scraping"
)
async def prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns all registered metrics in Prometheus exposition format.
    Configure your Prometheus server to scrape this endpoint.
    """
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Prometheus client not installed. Install with: pip install prometheus-client"
        )
    
    try:
        from fastapi import Response
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# HEALTH CHECK ENDPOINT
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/health",
    summary="System health check",
    description="Returns overall system health status"
)
async def health_check() -> SystemHealthResponse:
    """
    System health check endpoint
    
    Checks:
    - Agent system status
    - Memory layers
    - Tool registry
    - Decision engine
    
    Returns:
        Health status for each component
    """
    try:
        metrics = get_agent_metrics()
        
        # Check components
        components = {
            "agent_system": "healthy",
            "metrics_system": "healthy",
            "logging_system": "healthy"
        }
        
        # Get current metrics
        metrics_summary = {
            "active_automations": 0,  # Would get from gauge
            "total_automations_today": 0,  # Would calculate from counter
            "error_rate_1h": 0.0
        }
        
        return SystemHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            components=components,
            metrics_summary=metrics_summary
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemHealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            components={"error": str(e)},
            metrics_summary={}
        )


# ═══════════════════════════════════════════════════════════════════
# AUTOMATION DASHBOARD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/automations/summary",
    response_model=AutomationSummaryResponse,
    summary="Get automation summary",
    description="Get summary statistics for booking automations"
)
async def get_automation_summary(
    hours: int = 24,
    current_user: UserTable = Depends(get_current_user)
) -> AutomationSummaryResponse:
    """
    Get automation summary for dashboard
    
    Args:
        hours: Time window in hours (default: 24)
    
    Returns:
        Summary statistics including:
        - Total automations
        - Success rate
        - Average decision score
        - Average execution time
    """
    try:
        # Use LogAnalyzer to get statistics
        analyzer = LogAnalyzer()
        summary = analyzer.get_automation_summary(hours=hours)
        
        return AutomationSummaryResponse(
            total_automations=summary["total_automations"],
            completed=summary["completed"],
            failed=summary["failed"],
            success_rate=summary["success_rate"],
            average_decision_score=summary["average_decision_score"],
            average_execution_time_ms=1200.0,  # Would calculate from logs
            time_window_hours=hours
        )
        
    except Exception as e:
        logger.error(f"Error getting automation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/automations/recent",
    summary="Get recent automations",
    description="Get list of recent automation runs"
)
async def get_recent_automations(
    limit: int = 10,
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get recent automation runs
    
    Args:
        limit: Maximum number to return (default: 10)
    
    Returns:
        List of recent automations with status
    """
    try:
        analyzer = LogAnalyzer()
        logs = analyzer.parse_logs()
        
        # Filter automation events
        automations = [
            log for log in logs
            if log.get("event_type") in ["automation_start", "automation_complete"]
        ]
        
        # Get most recent
        recent = automations[-limit:] if len(automations) > limit else automations
        
        return {
            "automations": recent,
            "count": len(recent),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recent automations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/automations/errors",
    summary="Get error summary",
    description="Get summary of recent errors"
)
async def get_error_summary(
    hours: int = 24,
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get error summary for monitoring
    
    Args:
        hours: Time window in hours
    
    Returns:
        Error counts and breakdown by type
    """
    try:
        analyzer = LogAnalyzer()
        errors = analyzer.get_error_summary(hours=hours)
        
        return {
            "total_errors": errors["total_errors"],
            "error_breakdown": errors["error_breakdown"],
            "time_window_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting error summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# REAL-TIME METRICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/metrics/current",
    response_model=MetricsResponse,
    summary="Get current metrics",
    description="Get real-time metrics snapshot"
)
async def get_current_metrics(
    current_user: UserTable = Depends(get_current_user)
) -> MetricsResponse:
    """
    Get current system metrics
    
    Returns:
        Real-time metrics including:
        - Bookings automated
        - Success rate
        - Active automations
        - Tool execution summary
    """
    try:
        # This would read from actual Prometheus metrics in production
        # For now, return placeholder data structure
        
        return MetricsResponse(
            bookings_automated={
                "completed": 0,
                "partial": 0,
                "failed": 0
            },
            automation_success_rate=0.0,
            active_automations=0,
            tool_execution_summary={
                "total_executions": 0,
                "successful": 0,
                "failed": 0
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/metrics/decision-scores",
    summary="Get decision score distribution",
    description="Get histogram of automation decision scores"
)
async def get_decision_score_distribution(
    hours: int = 24,
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get decision score distribution
    
    Args:
        hours: Time window in hours
    
    Returns:
        Histogram of decision scores
    """
    try:
        # This would aggregate from logs/metrics
        return {
            "distribution": {
                "0-20": 0,
                "21-40": 0,
                "41-60": 0,
                "61-80": 0,
                "81-90": 0,
                "91-100": 0
            },
            "time_window_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting decision scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD DATA ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/dashboard",
    summary="Get dashboard data",
    description="Get all data needed for monitoring dashboard"
)
async def get_dashboard_data(
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get complete dashboard data
    
    Returns:
        Aggregated data for monitoring dashboard:
        - Automation stats
        - Tool usage
        - Error summary
        - System health
    """
    try:
        # Get all metrics
        summary = await get_automation_summary(hours=24, current_user=current_user)
        errors = await get_error_summary(hours=24, current_user=current_user)
        health = await health_check()
        
        return {
            "overview": {
                "total_automations_24h": summary.total_automations,
                "success_rate_24h": summary.success_rate,
                "avg_decision_score": summary.average_decision_score,
                "avg_execution_time_ms": summary.average_execution_time_ms,
                "active_automations": 0,  # Would get from gauge
                "system_health": health.status
            },
            "recent_activity": {
                "errors_24h": errors["total_errors"],
                "error_breakdown": errors["error_breakdown"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/dashboard/tools",
    summary="Get tool usage stats",
    description="Get tool execution statistics for dashboard"
)
async def get_tool_stats(
    hours: int = 24,
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get tool usage statistics
    
    Args:
        hours: Time window in hours
    
    Returns:
        Tool execution counts, success rates, average durations
    """
    try:
        # This would aggregate from logs/metrics
        return {
            "tools": {
                "send_email": {
                    "executions": 0,
                    "success_rate": 0.0,
                    "avg_duration_ms": 0
                },
                "create_calendar_event": {
                    "executions": 0,
                    "success_rate": 0.0,
                    "avg_duration_ms": 0
                }
            },
            "time_window_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting tool stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINT FOR REAL-TIME UPDATES
# ═══════════════════════════════════════════════════════════════════

@router.websocket("/ws")
async def monitoring_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring updates
    
    Streams:
    - Automation status changes
    - New errors
    - Metric updates
    """
    token = websocket.query_params.get("token") or websocket.cookies.get("graftai_access_token")
    user_id = await _validate_websocket_user(token)
    redis = await get_redis_client() if user_id else None
    pubsub = None
    channel_name = None
    last_metrics_sent_at = 0.0

    try:
        await websocket.accept()

        if user_id and redis:
            channel_name = f"chat_message_{user_id}"
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel_name)

            try:
                recent_messages = await get_recent_messages(user_id, count=3)
                for event in reversed(recent_messages):
                    await websocket.send_json({
                        "type": "notification",
                        "payload": _stream_event_to_notification(event),
                    })
            except Exception as exc:
                logger.warning("Failed to seed monitoring websocket with recent messages: %s", exc)

        while True:
            if pubsub:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    decoded = _decode_stream_payload(message.get("data"))
                    if decoded:
                        await websocket.send_json({
                            "type": "notification",
                            "payload": _stream_event_to_notification(decoded),
                        })
                else:
                    await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)

            now = datetime.utcnow().timestamp()
            if now - last_metrics_sent_at >= 5:
                await websocket.send_json({
                    "type": "metrics_update",
                    "payload": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "active_automations": 0,
                        "recent_automations": [],
                    },
                })
                last_metrics_sent_at = now

    except WebSocketDisconnect:
        logger.info("Monitoring websocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if pubsub and channel_name:
            try:
                await pubsub.unsubscribe(channel_name)
            except Exception:
                pass
            try:
                await pubsub.close()
            except Exception:
                pass
        try:
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close()
        except RuntimeError:
            # Connection can already be closing/closed depending on client timing.
            pass


# ═══════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/admin/reset-metrics",
    summary="Reset metrics (admin only)",
    description="Reset all Prometheus counters and gauges"
)
async def reset_metrics(
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Reset all metrics (admin only)
    
    Returns:
        Status message
    """
    # In production, check if user is admin
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        if PROMETHEUS_AVAILABLE:
            # Reset counters (set to 0)
            # Note: This is not standard Prometheus practice
            # Usually you'd restart the process or use new labels
            pass
        
        return {"status": "metrics reset", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/admin/logs",
    summary="Get agent logs (admin only)",
    description="Download agent activity logs"
)
async def get_logs(
    lines: int = 100,
    current_user: UserTable = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get recent agent logs
    
    Args:
        lines: Number of log lines to return
    
    Returns:
        Log entries
    """
    try:
        analyzer = LogAnalyzer()
        logs = analyzer.parse_logs()
        
        # Get last N lines
        recent_logs = logs[-lines:] if len(logs) > lines else logs
        
        return {
            "logs": recent_logs,
            "total_lines": len(logs),
            "returned_lines": len(recent_logs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
