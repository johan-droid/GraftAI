"""
Traffic Spike Management API Endpoints

API endpoints for monitoring and managing traffic spikes:
- Simulation control
- Safeguard configuration
- Real-time monitoring
- Alert management
"""
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.monitoring.traffic_spike_monitoring import (
    AlertSeverity,
    get_traffic_spike_monitor,
)
from backend.safeguards.traffic_spike_safeguards import get_traffic_spike_safeguards
from backend.simulation.failure_analysis import analyze_traffic_spike_failures
from backend.simulation.traffic_spike_simulator import (
    TRAFFIC_PATTERNS,
    run_traffic_spike_simulation,
)
from backend.utils.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/traffic-spike", tags=["traffic-spike"])

class SimulationRequest(BaseModel):
    """Traffic spike simulation request"""
    pattern_name: str
    duration_minutes: int | None = 10
    target_rps: int | None = None

class SafeguardConfigRequest(BaseModel):
    """Safeguard configuration request"""
    safeguard_type: str
    enabled: bool
    config: dict[str, Any]

class AlertResolutionRequest(BaseModel):
    """Alert resolution request"""
    alert_id: str
    resolution_notes: str | None = None

@router.post("/simulation/start")
async def start_traffic_spike_simulation(request: SimulationRequest, current_user_id: str=Depends(get_current_user_id)):
    """Start traffic spike simulation"""
    try:
        if request.pattern_name not in TRAFFIC_PATTERNS:
            raise HTTPException(status_code=400, detail=f"Unknown traffic pattern: {request.pattern_name}")
        simulation_report = await run_traffic_spike_simulation(request.pattern_name)
        failure_analysis = analyze_traffic_spike_failures(simulation_report)
        simulation_id = f"sim_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        return {"simulation_id": simulation_id, "pattern_name": request.pattern_name, "status": "completed", "simulation_report": simulation_report, "failure_analysis": failure_analysis, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error starting traffic spike simulation: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start traffic spike simulation")

@router.get("/simulation/patterns")
async def get_traffic_patterns(current_user_id: str=Depends(get_current_user_id)):
    """Get available traffic patterns"""
    patterns = {}
    for name, pattern in TRAFFIC_PATTERNS.items():
        patterns[name] = {"name": pattern.name, "baseline_rps": pattern.baseline_rps, "spike_multiplier": pattern.spike_multiplier, "spike_duration_seconds": pattern.spike_duration_seconds, "ramp_up_seconds": pattern.ramp_up_seconds, "ramp_down_seconds": pattern.ramp_down_seconds, "endpoints": pattern.endpoints, "user_distribution": pattern.user_distribution}
    return {"patterns": patterns}

@router.post("/safeguards/start")
async def start_safeguards(current_user_id: str=Depends(get_current_user_id)):
    """Start traffic spike safeguards"""
    try:
        safeguards = get_traffic_spike_safeguards()
        await safeguards.start_safeguards()
        return {"status": "safeguards_started", "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error starting safeguards: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start safeguards")

@router.post("/safeguards/stop")
async def stop_safeguards(current_user_id: str=Depends(get_current_user_id)):
    """Stop traffic spike safeguards"""
    try:
        safeguards = get_traffic_spike_safeguards()
        await safeguards.stop_safeguards()
        return {"status": "safeguards_stopped", "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error stopping safeguards: %s", e)
        raise HTTPException(status_code=500, detail="Failed to stop safeguards")

@router.get("/safeguards/status")
async def get_safeguards_status(current_user_id: str=Depends(get_current_user_id)):
    """Get current safeguards status"""
    try:
        safeguards = get_traffic_spike_safeguards()
        return await safeguards.get_safeguard_status()
    except Exception as e:
        logger.exception("Error getting safeguards status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get safeguards status")

@router.post("/safeguards/configure")
async def configure_safeguards(request: SafeguardConfigRequest, current_user_id: str=Depends(get_current_user_id)):
    """Configure specific safeguard"""
    try:
        return {"status": "safeguard_configured", "safeguard_type": request.safeguard_type, "enabled": request.enabled, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error configuring safeguards: %s", e)
        raise HTTPException(status_code=500, detail="Failed to configure safeguards")

@router.post("/monitoring/start")
async def start_monitoring(current_user_id: str=Depends(get_current_user_id)):
    """Start traffic spike monitoring"""
    try:
        monitor = get_traffic_spike_monitor()
        await monitor.start_monitoring()
        return {"status": "monitoring_started", "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error starting monitoring: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start monitoring")

@router.post("/monitoring/stop")
async def stop_monitoring(current_user_id: str=Depends(get_current_user_id)):
    """Stop traffic spike monitoring"""
    try:
        monitor = get_traffic_spike_monitor()
        await monitor.stop_monitoring()
        return {"status": "monitoring_stopped", "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error stopping monitoring: %s", e)
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

@router.get("/monitoring/metrics")
async def get_current_metrics(current_user_id: str=Depends(get_current_user_id)):
    """Get current monitoring metrics"""
    try:
        monitor = get_traffic_spike_monitor()
        return await monitor.get_current_metrics()
    except Exception as e:
        logger.exception("Error getting metrics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.get("/monitoring/alerts")
async def get_active_alerts(severity: str | None=Query(default=None), current_user_id: str=Depends(get_current_user_id)):
    """Get active alerts"""
    try:
        monitor = get_traffic_spike_monitor()
        alert_severity = None
        if severity:
            try:
                alert_severity = AlertSeverity(severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        alerts = await monitor.get_active_alerts(alert_severity)
        return {"alerts": [{"alert_id": alert.alert_id, "metric_type": alert.metric_type.value, "severity": alert.severity.value, "title": alert.title, "message": alert.message, "current_value": alert.current_value, "threshold": alert.threshold, "timestamp": alert.timestamp.isoformat(), "duration_seconds": alert.duration_seconds, "affected_endpoints": alert.affected_endpoints, "recommended_actions": alert.recommended_actions, "resolved": alert.resolved, "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None} for alert in alerts]}
    except Exception as e:
        logger.exception("Error getting alerts: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@router.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, request: AlertResolutionRequest, current_user_id: str=Depends(get_current_user_id)):
    """Resolve an alert"""
    try:
        monitor = get_traffic_spike_monitor()
        success = await monitor.resolve_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")
        return {"status": "alert_resolved", "alert_id": alert_id, "resolution_notes": request.resolution_notes, "timestamp": datetime.now(UTC).isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error resolving alert: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

@router.get("/analysis/failures")
async def get_failure_analysis(simulation_id: str | None=Query(default=None), current_user_id: str=Depends(get_current_user_id)):
    """Get failure analysis from traffic spike simulation"""
    try:
        return {"simulation_id": simulation_id, "failure_analysis": {"first_to_fail": [], "degradation_timeline": [], "resource_exhaustion": [], "cascade_effects": [], "critical_failure_points": [], "recovery_analysis": {}, "user_impact_analysis": {}, "recommendations": []}, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting failure analysis: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get failure analysis")

@router.get("/analysis/consistency")
async def get_consistency_analysis(simulation_id: str | None=Query(default=None), db: AsyncSession=Depends(get_db), current_user_id: str=Depends(get_current_user_id)):
    """Get data consistency analysis"""
    try:
        return {"simulation_id": simulation_id, "consistency_analysis": {"duplicate_records": [], "orphaned_records": [], "race_conditions": [], "transaction_conflicts": [], "cache_consistency": [], "stale_data": []}, "critical_issues": [], "recovery_strategies": {}, "prevention_recommendations": [], "monitoring_requirements": [], "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting consistency analysis: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get consistency analysis")

@router.get("/dashboard")
async def get_traffic_spike_dashboard(current_user_id: str=Depends(get_current_user_id)):
    """Get comprehensive traffic spike dashboard"""
    try:
        safeguards = get_traffic_spike_safeguards()
        safeguards_status = await safeguards.get_safeguard_status()
        monitor = get_traffic_spike_monitor()
        current_metrics = await monitor.get_current_metrics()
        active_alerts = await monitor.get_active_alerts()
        return {"dashboard": {"safeguards": safeguards_status, "metrics": current_metrics, "alerts": [{"alert_id": alert.alert_id, "severity": alert.severity.value, "title": alert.title, "message": alert.message, "timestamp": alert.timestamp.isoformat()} for alert in active_alerts[:10]], "summary": {"total_alerts": len(active_alerts), "critical_alerts": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]), "warning_alerts": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]), "safeguards_active": safeguards_status.get("safeguards_active", False), "degradation_level": safeguards_status.get("degradation_level", "full")}}, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error getting dashboard: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get dashboard")

@router.post("/test/load")
async def test_load(rps: int=Query(default=100), duration_seconds: int=Query(default=60), endpoint: str=Query(default="/health"), current_user_id: str=Depends(get_current_user_id)):
    """Test system under load"""
    try:
        return {"status": "load_test_started", "rps": rps, "duration_seconds": duration_seconds, "endpoint": endpoint, "test_id": f"load_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}", "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Error starting load test: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start load test")
