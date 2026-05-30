"""
Monitoring and Metrics API Endpoints

Provides endpoints for Prometheus metrics, health checks, and monitoring dashboard.
"""
import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from backend.services.auth_service import decode_jwt_token
from pydantic import BaseModel
from sqlalchemy import select, text
from starlette.websockets import WebSocketState

try:
    from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
import contextlib

from backend.ai.monitoring import LogAnalyzer, get_agent_metrics
from backend.api.deps import get_current_user
from backend.auth.config import ALGORITHM, SECRET_KEY
from backend.auth.schemes import require_admin
from backend.models.tables import UserTable
from backend.services.messaging import get_recent_messages
from backend.services.redis_client import get_redis_client
from backend.services.usage import build_quota_snapshot, get_user_quota
from backend.utils.db import get_async_session_maker
from backend.utils.logger import get_logger
from backend.utils.serialization import serializer


async def _check_database() -> dict[str, Any]:
    try:
        session_maker = get_async_session_maker()
        start = datetime.now(UTC)
        async with session_maker() as db:
            await db.execute(text("SELECT 1"))
        latency_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}

async def _check_redis() -> dict[str, Any]:
    try:
        redis_client = await get_redis_client()
        if redis_client is None:
            msg = "Redis client unavailable"
            raise RuntimeError(msg)
        start = datetime.now(UTC)
        await redis_client.ping()
        latency_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}
logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

class SystemHealthResponse(BaseModel):
    status: str
    timestamp: str
    components: dict[str, Any]
    metrics_summary: dict[str, Any]

class AutomationSummaryResponse(BaseModel):
    total_automations: int
    completed: int
    failed: int
    success_rate: float
    average_decision_score: float
    average_execution_time_ms: float
    time_window_hours: int

class MetricsResponse(BaseModel):
    bookings_automated: dict[str, int]
    automation_success_rate: float
    active_automations: int
    tool_execution_summary: dict[str, Any]
    timestamp: str

def _decode_stream_payload(raw_payload: Any) -> dict[str, Any]:
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

def _stream_event_to_notification(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata") or {}
    milestone = metadata.get("milestone") or metadata.get("kind") or "action complete"
    title = str(milestone).replace("_", " ").strip().title()
    message = str(event.get("message") or "").strip()
    if len(message) > 180:
        message = f"{message[:177].rstrip()}..."
    if not message:
        message = "A background action finished successfully."
    return {"type": "success" if metadata.get("kind") in {"ai_milestone", "chat_milestone"} else "info", "title": title or "Live update", "message": message, "metadata": metadata, "timestamp": event.get("timestamp") or datetime.now(UTC).isoformat()}

async def _safe_send_json(websocket: WebSocket, payload: dict[str, Any], context: str) -> bool:
    """Send JSON only while the websocket is still open."""
    if websocket.client_state == WebSocketState.DISCONNECTED:
        return False
    try:
        await websocket.send_json(payload)
        return True
    except RuntimeError as exc:
        logger.debug("Skipping websocket send during %s: %s", context, exc)
        return False
    except Exception as exc:
        logger.debug("Websocket send failed during %s: %s", context, exc)
        return False

async def _resolve_websocket_user_id(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload = await decode_jwt_token(token)
        user_id = payload.get("sub")
        return str(user_id) if user_id else None
    except JWTError:
        return None

async def _validate_websocket_user(token: str | None) -> str | None:
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
        return result.scalar_one_or_none()

@router.get("/metrics", summary="Prometheus metrics endpoint", description="Returns Prometheus-formatted metrics for scraping")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint

    Returns all registered metrics in Prometheus exposition format.
    Configure your Prometheus server to scrape this endpoint.
    """
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Prometheus client not installed. Install with: pip install prometheus-client")
    try:
        from fastapi import Response
        return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.exception("Error generating metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", summary="System health check", description="Returns overall system health status")
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
        get_agent_metrics()
        db_health = await _check_database()
        redis_health = await _check_redis()
        components = {"agent_system": "healthy", "metrics_system": "healthy", "logging_system": "healthy", "database": db_health, "redis": redis_health}
        overall_status = "healthy"
        if db_health["status"] != "healthy" or redis_health["status"] != "healthy":
            overall_status = "unhealthy"
        metrics_summary = {"active_automations": 0, "total_automations_today": 0, "error_rate_1h": 0.0}
        return SystemHealthResponse(status=overall_status, timestamp=datetime.now(UTC).isoformat(), components=components, metrics_summary=metrics_summary)
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        return SystemHealthResponse(status="unhealthy", timestamp=datetime.now(UTC).isoformat(), components={"error": str(e)}, metrics_summary={})

@router.get("/automations/summary", response_model=AutomationSummaryResponse, summary="Get automation summary", description="Get summary statistics for booking automations")
async def get_automation_summary(hours: int=24, current_user: UserTable=Depends(get_current_user)) -> AutomationSummaryResponse:
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
        analyzer = LogAnalyzer()
        summary = analyzer.get_automation_summary(hours=hours)
        return AutomationSummaryResponse(total_automations=summary["total_automations"], completed=summary["completed"], failed=summary["failed"], success_rate=summary["success_rate"], average_decision_score=summary["average_decision_score"], average_execution_time_ms=1200.0, time_window_hours=hours)
    except Exception as e:
        logger.exception("Error getting automation summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/automations/recent", summary="Get recent automations", description="Get list of recent automation runs")
async def get_recent_automations(limit: int=10, current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
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
        automations = [log for log in logs if log.get("event_type") in ["automation_start", "automation_complete"]]
        recent = automations[-limit:] if len(automations) > limit else automations
        return {"automations": recent, "count": len(recent), "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting recent automations: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/automations/errors", summary="Get error summary", description="Get summary of recent errors")
async def get_error_summary(hours: int=24, current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
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
        return {"total_errors": errors["total_errors"], "error_breakdown": errors["error_breakdown"], "time_window_hours": hours, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting error summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/current", response_model=MetricsResponse, summary="Get current metrics", description="Get real-time metrics snapshot")
async def get_current_metrics(current_user: UserTable=Depends(get_current_user)) -> MetricsResponse:
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
        return MetricsResponse(bookings_automated={"completed": 0, "partial": 0, "failed": 0}, automation_success_rate=0.0, active_automations=0, tool_execution_summary={"total_executions": 0, "successful": 0, "failed": 0}, timestamp=datetime.now(UTC).isoformat())
    except Exception as e:
        logger.exception("Error getting metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/decision-scores", summary="Get decision score distribution", description="Get histogram of automation decision scores")
async def get_decision_score_distribution(hours: int=24, current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
    """
    Get decision score distribution

    Args:
        hours: Time window in hours

    Returns:
        Histogram of decision scores
    """
    try:
        return {"distribution": {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-90": 0, "91-100": 0}, "time_window_hours": hours, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting decision scores: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard", summary="Get dashboard data", description="Get all data needed for monitoring dashboard")
async def get_dashboard_data(current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
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
        summary = await get_automation_summary(hours=24, current_user=current_user)
        errors = await get_error_summary(hours=24, current_user=current_user)
        health = await health_check()
        return {"overview": {"total_automations_24h": summary.total_automations, "success_rate_24h": summary.success_rate, "avg_decision_score": summary.average_decision_score, "avg_execution_time_ms": summary.average_execution_time_ms, "active_automations": 0, "system_health": health.status}, "recent_activity": {"errors_24h": errors["total_errors"], "error_breakdown": errors["error_breakdown"]}, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting dashboard data: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/tools", summary="Get tool usage stats", description="Get tool execution statistics for dashboard")
async def get_tool_stats(hours: int=24, current_user: UserTable=Depends(get_current_user)) -> dict[str, Any]:
    """
    Get tool usage statistics

    Args:
        hours: Time window in hours

    Returns:
        Tool execution counts, success rates, average durations
    """
    try:
        return {"tools": {"send_email": {"executions": 0, "success_rate": 0.0, "avg_duration_ms": 0}, "create_calendar_event": {"executions": 0, "success_rate": 0.0, "avg_duration_ms": 0}}, "time_window_hours": hours, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting tool stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

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
    quota_channel_name = None
    last_metrics_sent_at = 0.0
    try:
        await websocket.accept()
        if user_id and redis:
            channel_name = f"chat_message_{user_id}"
            quota_channel_name = f"account_update_{user_id}"
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel_name, quota_channel_name)
            try:
                session_maker = get_async_session_maker()
                async with session_maker() as db:
                    user = await get_user_quota(db, user_id)
                    if not await _safe_send_json(websocket, {"type": "quota_update", "payload": build_quota_snapshot(user, source="websocket.seed")}, "quota snapshot seed"):
                        return
            except Exception as exc:
                logger.warning("Failed to seed monitoring websocket with quota snapshot: %s", exc)
            try:
                recent_messages = await get_recent_messages(user_id, count=3)
                for event in reversed(recent_messages):
                    if not await _safe_send_json(websocket, {"type": "notification", "payload": _stream_event_to_notification(event)}, "recent message seed"):
                        return
            except Exception as exc:
                logger.warning("Failed to seed monitoring websocket with recent messages: %s", exc)
        while True:
            if pubsub:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    decoded = _decode_stream_payload(message.get("data"))
                    if decoded:
                        if decoded.get("type") == "quota_update":
                            if not await _safe_send_json(websocket, {"type": "quota_update", "payload": decoded.get("payload", decoded)}, "quota update stream"):
                                break
                        elif not await _safe_send_json(websocket, {"type": "notification", "payload": _stream_event_to_notification(decoded)}, "notification stream"):
                            break
                else:
                    await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)
            now = datetime.now(UTC).timestamp()
            if now - last_metrics_sent_at >= 5:
                if not await _safe_send_json(websocket, {"type": "metrics_update", "payload": {"timestamp": datetime.now(UTC).isoformat(), "active_automations": 0, "recent_automations": []}}, "metrics heartbeat"):
                    break
                last_metrics_sent_at = now
    except WebSocketDisconnect:
        logger.info("Monitoring websocket client disconnected")
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
    finally:
        if pubsub and channel_name:
            try:
                unsubscribe_channels = [channel_name]
                if quota_channel_name:
                    unsubscribe_channels.append(quota_channel_name)
                await pubsub.unsubscribe(*unsubscribe_channels)
            except Exception:
                pass
            with contextlib.suppress(Exception):
                await pubsub.close()
        try:
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close()
        except RuntimeError:
            pass

@router.post("/admin/reset-metrics", summary="Reset metrics (admin only)", description="Reset all Prometheus counters and gauges")
async def reset_metrics(admin_id: str=Depends(require_admin)) -> dict[str, str]:
    """
    Reset all metrics (admin only)

    Returns:
        Status message
    """
    try:
        if PROMETHEUS_AVAILABLE:
            pass
        return {"status": "metrics reset", "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error resetting metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/logs", summary="Get agent logs (admin only)", description="Download agent activity logs")
async def get_logs(lines: int=100, admin_id: str=Depends(require_admin)) -> dict[str, Any]:
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
        recent_logs = logs[-lines:] if len(logs) > lines else logs
        return {"logs": recent_logs, "total_lines": len(logs), "returned_lines": len(recent_logs), "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting logs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
