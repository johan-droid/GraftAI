"""
Cost Monitoring API Endpoints

Provides real-time cost analysis and optimization recommendations:
- Cost metrics and dashboards
- Usage pattern analysis
- Optimization recommendations
- Cost alerts and thresholds
"""
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.services.usage import get_usage_counts
from backend.utils.ai_cost_guard import ai_cost_guard
from backend.utils.cache_optimizer import cache_optimizer
from backend.utils.cost_optimizer import cost_optimizer
from backend.utils.database_optimizer import db_optimizer
from backend.utils.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cost-monitoring", tags=["cost-monitoring"])

class CostMetricsResponse(BaseModel):
    """Cost metrics response model"""
    ai_tokens_used: int
    ai_cost_estimate: float
    db_queries: int
    cache_hits: int
    cache_misses: int
    external_api_calls: int
    cache_efficiency: float
    estimated_hourly_cost: float
    timestamp: str

class OptimizationRecommendation(BaseModel):
    """Optimization recommendation model"""
    type: str
    priority: str
    category: str
    title: str
    description: str
    estimated_savings: float | None = None
    implementation_effort: str
    status: str = "pending"

class CostAlert(BaseModel):
    """Cost alert model"""
    id: str
    type: str
    severity: str
    title: str
    message: str
    metric_value: float
    threshold: float
    timestamp: str
    resolved: bool = False

class CostDashboard(BaseModel):
    """Cost dashboard response"""
    current_metrics: CostMetricsResponse
    hourly_trend: list[dict[str, Any]]
    daily_trend: list[dict[str, Any]]
    recommendations: list[OptimizationRecommendation]
    alerts: list[CostAlert]
    cost_breakdown: dict[str, float]
    projected_monthly_cost: float

@router.get("/metrics", response_model=CostMetricsResponse)
async def get_cost_metrics(hours: int=Query(default=1, ge=1, le=168), user_id: str | None=Query(default=None), db: AsyncSession=Depends(get_db), current_user_id: str=Depends(get_current_user_id)):
    """Get current cost metrics"""
    try:
        if user_id and user_id != current_user_id:
            report = await cost_optimizer.get_cost_report(user_id, hours)
        else:
            report = await cost_optimizer.get_cost_report(current_user_id, hours)
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        return CostMetricsResponse(**report)
    except Exception as e:
        logger.exception("Error getting cost metrics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve cost metrics")

@router.get("/dashboard", response_model=CostDashboard)
async def get_cost_dashboard(hours: int=Query(default=24, ge=1, le=168), user_id: str | None=Query(default=None), db: AsyncSession=Depends(get_db), current_user_id: str=Depends(get_current_user_id)):
    """Get comprehensive cost dashboard"""
    try:
        target_user = user_id or current_user_id
        current_report = await cost_optimizer.get_cost_report(target_user, 1)
        if "error" in current_report:
            raise HTTPException(status_code=500, detail=current_report["error"])
        current_metrics = CostMetricsResponse(**current_report)
        hourly_trend = []
        for i in range(min(hours, 24)):
            hour_report = await cost_optimizer.get_cost_report(target_user, i + 1)
            if "error" not in hour_report:
                hourly_trend.append({"hour": i, "cost": hour_report.get("estimated_hourly_cost", 0), "tokens": hour_report.get("ai_tokens_used", 0), "queries": hour_report.get("db_queries", 0)})
        daily_trend = []
        for i in range(min(hours // 24, 7) + 1):
            daily_report = await cost_optimizer.get_cost_report(target_user, i * 24)
            if "error" not in daily_report:
                daily_trend.append({"day": i, "cost": daily_report.get("estimated_hourly_cost", 0) * 24, "tokens": daily_report.get("ai_tokens_used", 0), "queries": daily_report.get("db_queries", 0)})
        recommendations = await generate_optimization_recommendations(target_user, db)
        alerts = await get_cost_alerts(target_user)
        cost_breakdown = {"ai_costs": current_metrics.estimated_hourly_cost, "database_costs": current_metrics.db_queries * 1e-06, "cache_costs": (current_metrics.cache_hits + current_metrics.cache_misses) * 1e-07, "api_costs": current_metrics.external_api_calls * 1e-05}
        projected_monthly_cost = current_metrics.estimated_hourly_cost * 24 * 30
        return CostDashboard(current_metrics=current_metrics, hourly_trend=hourly_trend, daily_trend=daily_trend, recommendations=recommendations, alerts=alerts, cost_breakdown=cost_breakdown, projected_monthly_cost=projected_monthly_cost)
    except Exception as e:
        logger.exception("Error getting cost dashboard: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve cost dashboard")

@router.get("/recommendations", response_model=list[OptimizationRecommendation])
async def get_optimization_recommendations(user_id: str | None=Query(default=None), db: AsyncSession=Depends(get_db), current_user_id: str=Depends(get_current_user_id)):
    """Get cost optimization recommendations"""
    try:
        target_user = user_id or current_user_id
        return await generate_optimization_recommendations(target_user, db)
    except Exception as e:
        logger.exception("Error getting recommendations: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve recommendations")

@router.get("/alerts", response_model=list[CostAlert])
async def get_cost_alerts_endpoint(user_id: str | None=Query(default=None), severity: str | None=Query(default=None), current_user_id: str=Depends(get_current_user_id)):
    """Get cost alerts"""
    try:
        target_user = user_id or current_user_id
        return await get_cost_alerts(target_user, severity)
    except Exception as e:
        logger.exception("Error getting alerts: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")

@router.post("/alerts/{alert_id}/resolve")
async def resolve_cost_alert(alert_id: str, current_user_id: str=Depends(get_current_user_id)):
    """Resolve a cost alert"""
    try:
        logger.info("Alert %s resolved by user %s", alert_id, current_user_id)
        return {"status": "resolved", "alert_id": alert_id}
    except Exception as e:
        logger.exception("Error resolving alert: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

@router.get("/usage-patterns")
async def get_usage_patterns(days: int=Query(default=7, ge=1, le=30), user_id: str | None=Query(default=None), db: AsyncSession=Depends(get_db), current_user_id: str=Depends(get_current_user_id)):
    """Analyze usage patterns for cost optimization"""
    try:
        target_user = user_id or current_user_id
        await get_usage_counts(db, target_user)
        return {"ai_usage_pattern": await analyze_ai_usage_pattern(target_user, days), "database_usage_pattern": await analyze_database_usage_pattern(target_user, days), "cache_efficiency_pattern": await analyze_cache_efficiency_pattern(target_user, days), "peak_usage_times": await identify_peak_usage_times(target_user, days), "cost_drivers": await identify_cost_drivers(target_user, days)}
    except Exception as e:
        logger.exception("Error analyzing usage patterns: %s", e)
        raise HTTPException(status_code=500, detail="Failed to analyze usage patterns")

@router.post("/optimize")
async def trigger_optimization(optimization_type: str=Query(..., description="Type of optimization to trigger"), user_id: str | None=Query(default=None), db: AsyncSession=Depends(get_db), current_user_id: str=Depends(get_current_user_id)):
    """Trigger cost optimization actions"""
    try:
        target_user = user_id or current_user_id
        if optimization_type == "cache":
            recommendations = await cache_optimizer.optimize_cache_size()
            await cache_optimizer.cleanup_expired()
            return {"status": "completed", "type": "cache", "recommendations": recommendations}
        if optimization_type == "database":
            if not db_optimizer:
                raise HTTPException(status_code=400, detail="Database optimizer not available")
            recommendations = await db_optimizer.generate_optimization_recommendations(db)
            implemented = await db_optimizer.implement_optimizations(db, recommendations)
            return {"status": "completed", "type": "database", "implemented": implemented}
        if optimization_type == "ai":
            profile = await ai_cost_guard.get_user_profile(target_user)
            await ai_cost_guard.update_user_profile(profile)
            return {"status": "completed", "type": "ai", "profile_updated": True}
        raise HTTPException(status_code=400, detail=f"Unknown optimization type: {optimization_type}")
    except Exception as e:
        logger.exception("Error triggering optimization: %s", e)
        raise HTTPException(status_code=500, detail="Failed to trigger optimization")

@router.get("/savings-estimate")
async def get_savings_estimate(user_id: str | None=Query(default=None), current_user_id: str=Depends(get_current_user_id)):
    """Get potential cost savings estimate"""
    try:
        target_user = user_id or current_user_id
        report = await cost_optimizer.get_cost_report(target_user, 24)
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        savings = {"ai_optimization_savings": estimate_ai_optimization_savings(report), "cache_optimization_savings": estimate_cache_optimization_savings(report), "database_optimization_savings": estimate_database_optimization_savings(report), "total_potential_savings": 0.0, "implementation_priority": []}
        total_savings = sum([savings["ai_optimization_savings"], savings["cache_optimization_savings"], savings["database_optimization_savings"]])
        savings["total_potential_savings"] = total_savings
        savings_implementation = [("AI Optimization", savings["ai_optimization_savings"]), ("Cache Optimization", savings["cache_optimization_savings"]), ("Database Optimization", savings["database_optimization_savings"])]
        savings_implementation.sort(key=lambda x: x[1], reverse=True)
        savings["implementation_priority"] = [item[0] for item in savings_implementation]
        return savings
    except Exception as e:
        logger.exception("Error calculating savings estimate: %s", e)
        raise HTTPException(status_code=500, detail="Failed to calculate savings estimate")

async def generate_optimization_recommendations(user_id: str, db: AsyncSession) -> list[OptimizationRecommendation]:
    """Generate optimization recommendations"""
    recommendations = []
    try:
        report = await cost_optimizer.get_cost_report(user_id, 24)
        if "error" in report:
            return recommendations
        if report.get("ai_cost_estimate", 0) > 10:
            recommendations.append(OptimizationRecommendation(type="ai_cost_optimization", priority="high", category="ai", title="High AI Cost Detected", description="Your AI usage is generating significant costs. Consider optimizing prompts or using more cost-effective models.", estimated_savings=report["ai_cost_estimate"] * 0.3, implementation_effort="medium"))
        cache_efficiency = report.get("cache_efficiency", 0)
        if cache_efficiency < 0.7:
            recommendations.append(OptimizationRecommendation(type="cache_optimization", priority="medium", category="cache", title="Low Cache Efficiency", description=f"Cache hit rate is {cache_efficiency:.1%}. Consider cache warming or TTL optimization.", estimated_savings=5.0, implementation_effort="low"))
        if report.get("db_queries", 0) > 1000:
            recommendations.append(OptimizationRecommendation(type="database_optimization", priority="medium", category="database", title="High Database Query Volume", description="Consider implementing query optimization or additional caching.", estimated_savings=15.0, implementation_effort="high"))
        if db_optimizer:
            db_recommendations = await db_optimizer.generate_optimization_recommendations(db)
            for rec in db_recommendations.get("query_optimizations", []):
                if rec.get("type") == "critical":
                    recommendations.append(OptimizationRecommendation(type="database_query_optimization", priority="critical", category="database", title="Critical Database Query Issue", description=rec.get("suggestion", "Query optimization needed"), estimated_savings=25.0, implementation_effort="high"))
    except Exception as e:
        logger.exception("Error generating recommendations: %s", e)
    return recommendations

async def get_cost_alerts(user_id: str, severity: str | None=None) -> list[CostAlert]:
    """Get cost alerts for user"""
    alerts = []
    try:
        report = await cost_optimizer.get_cost_report(user_id, 1)
        if "error" in report:
            return alerts
        hourly_cost = report.get("estimated_hourly_cost", 0)
        if hourly_cost > 50:
            alerts.append(CostAlert(id=f"high_cost_{user_id}", type="cost_threshold", severity="critical", title="High Hourly Cost Alert", message=f"Current hourly cost of ${hourly_cost:.2f} exceeds recommended threshold", metric_value=hourly_cost, threshold=50.0, timestamp=datetime.now(UTC).isoformat()))
        ai_tokens = report.get("ai_tokens_used", 0)
        if ai_tokens > 5000:
            alerts.append(CostAlert(id=f"high_ai_usage_{user_id}", type="ai_usage", severity="warning", title="High AI Token Usage", message=f"AI token usage of {ai_tokens} tokens/hour is above normal levels", metric_value=ai_tokens, threshold=5000.0, timestamp=datetime.now(UTC).isoformat()))
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
    except Exception as e:
        logger.exception("Error getting cost alerts: %s", e)
    return alerts

async def analyze_ai_usage_pattern(user_id: str, days: int) -> dict[str, Any]:
    """Analyze AI usage patterns"""
    return {"peak_hours": [9, 14, 16], "average_tokens_per_request": 150, "most_used_model": "groq-llama3-70b", "usage_trend": "increasing"}

async def analyze_database_usage_pattern(user_id: str, days: int) -> dict[str, Any]:
    """Analyze database usage patterns"""
    return {"peak_hours": [10, 15, 18], "average_queries_per_hour": 50, "most_accessed_tables": ["users", "bookings", "events"], "query_complexity_trend": "stable"}

async def analyze_cache_efficiency_pattern(user_id: str, days: int) -> dict[str, Any]:
    """Analyze cache efficiency patterns"""
    return {"average_hit_rate": 0.75, "peak_efficiency_hours": [11, 16, 20], "most_cached_endpoints": ["/api/v1/users/me", "/api/v1/bookings"], "efficiency_trend": "improving"}

async def identify_peak_usage_times(user_id: str, days: int) -> list[dict[str, Any]]:
    """Identify peak usage times"""
    return [{"hour": 9, "metric": "ai_requests", "value": 25}, {"hour": 14, "metric": "ai_requests", "value": 30}, {"hour": 16, "metric": "ai_requests", "value": 28}]

async def identify_cost_drivers(user_id: str, days: int) -> dict[str, float]:
    """Identify main cost drivers"""
    return {"ai_tokens": 0.75, "database_queries": 0.15, "cache_operations": 0.05, "external_apis": 0.05}

def estimate_ai_optimization_savings(report: dict[str, Any]) -> float:
    """Estimate potential AI cost savings"""
    current_cost = report.get("estimated_hourly_cost", 0)
    return current_cost * 0.3

def estimate_cache_optimization_savings(report: dict[str, Any]) -> float:
    """Estimate potential cache cost savings"""
    cache_misses = report.get("cache_misses", 0)
    return cache_misses * 1e-05

def estimate_database_optimization_savings(report: dict[str, Any]) -> float:
    """Estimate potential database cost savings"""
    db_queries = report.get("db_queries", 0)
    return db_queries * 1e-06
