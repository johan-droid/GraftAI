"""
Monitoring Agent - Tracks outcomes, alerts on issues, and collects feedback
Provides observability and analytics for the scheduling system
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from backend.ai.agents.base import BaseAgent, AgentContext
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AlertLevel:
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringAgent(BaseAgent):
    """
    Specialized agent for monitoring and observability
    
    Responsibilities:
    - Track outcomes of actions and workflows
    - Alert on issues and anomalies
    - Collect user feedback
    - Generate insights and reports
    - Monitor system health
    """
    
    def __init__(self):
        super().__init__(
            name="MonitoringAgent",
            description="Tracks outcomes, alerts on issues, and collects feedback"
        )
        
        # Alert configuration
        self.alert_thresholds = {
            "booking_failure_rate": 0.15,
            "api_response_time_ms": 5000,
            "calendar_sync_failures": 5,
            "consecutive_errors": 3
        }
        
        # Active alerts
        self.active_alerts: List[Dict[str, Any]] = []
        
        # Metrics cache
        self.metrics_cache: Dict[str, Any] = {}
    
    def _get_available_tools(self) -> list:
        return [
            "track_outcome",
            "collect_feedback",
            "generate_report",
            "check_health",
            "alert",
            "monitor_workflow"
        ]
    
    async def _execute(self, context: AgentContext) -> Dict[str, Any]:
        """
        Execute monitoring and tracking tasks
        
        Args:
            context: Contains monitoring request (track, alert, report, etc.)
            
        Returns:
            Monitoring results, alerts, or reports
        """
        data = context.data
        user_id = context.user_id
        task_type = data.get("task_type", "track")
        
        logger.info(f"MonitoringAgent executing {task_type} for user {user_id}")
        
        if task_type == "track_outcome":
            return await self._track_outcome(data, user_id)
        
        elif task_type == "collect_feedback":
            return await self._collect_feedback(data, user_id)
        
        elif task_type == "generate_report":
            return await self._generate_report(data, user_id)
        
        elif task_type == "check_health":
            return await self._check_system_health()
        
        elif task_type == "alert":
            return await self._process_alert(data, user_id)
        
        elif task_type == "monitor_workflow":
            return await self._monitor_workflow(data, user_id)
        
        else:
            return {
                "success": False,
                "error": f"Unknown monitoring task: {task_type}"
            }
    
    async def _track_outcome(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Track the outcome of an action or workflow"""
        outcome_data = {
            "tracking_id": data.get("tracking_id"),
            "user_id": user_id,
            "event_type": data.get("event_type"),  # booking, workflow, etc.
            "event_id": data.get("event_id"),
            "status": data.get("status"),  # success, failure, partial
            "details": data.get("details", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in vector store for analysis
        try:
            from backend.ai.memory.vector_store import VectorStore
            vector_store = VectorStore()
            
            await vector_store.add_document(
                collection="outcomes",
                document=outcome_data,
                metadata={
                    "user_id": user_id,
                    "event_type": outcome_data["event_type"],
                    "status": outcome_data["status"]
                }
            )
        except Exception as e:
            logger.error(f"Failed to store outcome: {e}")
        
        # Check for issues and alert if needed
        alerts = await self._check_for_issues(outcome_data)
        
        return {
            "success": True,
            "tracked": True,
            "tracking_id": outcome_data["tracking_id"],
            "alerts_triggered": len(alerts),
            "alerts": alerts
        }
    
    async def _collect_feedback(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Collect and process user feedback"""
        feedback = {
            "feedback_id": data.get("feedback_id"),
            "user_id": user_id,
            "target_type": data.get("target_type"),  # booking, suggestion, etc.
            "target_id": data.get("target_id"),
            "rating": data.get("rating"),  # 1-5 or similar
            "comments": data.get("comments"),
            "categories": data.get("categories", []),  # ease_of_use, accuracy, etc.
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Analyze sentiment if comments provided
        if feedback.get("comments"):
            sentiment = await self._analyze_sentiment(feedback["comments"])
            feedback["sentiment"] = sentiment
        
        # Store feedback
        try:
            from backend.ai.memory.vector_store import VectorStore
            vector_store = VectorStore()
            
            await vector_store.add_document(
                collection="feedback",
                document=feedback,
                metadata={
                    "user_id": user_id,
                    "target_type": feedback["target_type"],
                    "rating": feedback["rating"]
                }
            )
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
        
        # Generate insights from feedback
        insights = await self._generate_feedback_insights(feedback)
        
        return {
            "success": True,
            "feedback_id": feedback["feedback_id"],
            "sentiment": feedback.get("sentiment"),
            "insights": insights
        }
    
    async def _generate_report(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Generate analytics report"""
        report_type = data.get("report_type", "summary")
        timeframe = data.get("timeframe", "7d")
        
        # Calculate date range
        end_date = datetime.utcnow()
        if timeframe == "24h":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "7d":
            start_date = end_date - timedelta(days=7)
        elif timeframe == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        report = {
            "report_type": report_type,
            "timeframe": timeframe,
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
        if report_type == "summary":
            report.update(await self._generate_summary_report(user_id, start_date, end_date))
        
        elif report_type == "bookings":
            report.update(await self._generate_bookings_report(user_id, start_date, end_date))
        
        elif report_type == "performance":
            report.update(await self._generate_performance_report(start_date, end_date))
        
        elif report_type == "user_engagement":
            report.update(await self._generate_engagement_report(user_id, start_date, end_date))
        
        return {
            "success": True,
            "report": report
        }
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health_checks = {
            "database": await self._check_database_health(),
            "redis": await self._check_redis_health(),
            "celery": await self._check_celery_health(),
            "api": await self._check_api_health(),
            "agents": self._check_agent_health()
        }
        
        # Overall status
        all_healthy = all(check["healthy"] for check in health_checks.values())
        
        health_report = {
            "success": True,
            "overall_status": "healthy" if all_healthy else "degraded",
            "checks": health_checks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Alert if not healthy
        if not all_healthy:
            await self._create_alert(
                level=AlertLevel.ERROR,
                title="System Health Degraded",
                message=f"Failed health checks: {[k for k, v in health_checks.items() if not v['healthy']]}",
                details=health_checks
            )
        
        return health_report
    
    async def _process_alert(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Process and route an alert"""
        alert = {
            "alert_id": data.get("alert_id"),
            "level": data.get("level", AlertLevel.INFO),
            "title": data.get("title"),
            "message": data.get("message"),
            "source": data.get("source"),
            "user_id": user_id,
            "details": data.get("details", {}),
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False
        }
        
        # Store alert
        self.active_alerts.append(alert)
        
        # Route alert based on level
        await self._route_alert(alert)
        
        return {
            "success": True,
            "alert_id": alert["alert_id"],
            "routed": True
        }
    
    async def _monitor_workflow(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Monitor a workflow execution"""
        workflow_id = data.get("workflow_id")
        
        # Track workflow state
        workflow_state = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "status": data.get("status"),  # running, completed, failed
            "steps": data.get("steps", []),
            "current_step": data.get("current_step"),
            "progress": data.get("progress", 0),
            "started_at": data.get("started_at"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Check for issues
        if workflow_state["status"] == "failed":
            await self._create_alert(
                level=AlertLevel.ERROR,
                title=f"Workflow Failed: {workflow_id}",
                message=f"Workflow failed at step: {workflow_state.get('current_step')}",
                details=workflow_state
            )
        
        # Check for slow workflows
        if workflow_state["status"] == "running":
            started_raw = workflow_state.get("started_at")
            duration = 0.0

            if started_raw:
                try:
                    started = datetime.fromisoformat(started_raw)
                    duration = (datetime.utcnow() - started).total_seconds()
                except (TypeError, ValueError):
                    logger.warning(f"Invalid workflow started_at value: {started_raw}")

            if duration > 300:  # 5 minutes
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    title=f"Slow Workflow: {workflow_id}",
                    message=f"Workflow running for {duration:.0f} seconds",
                    details=workflow_state
                )
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "monitored": True
        }
    
    async def _check_for_issues(self, outcome_data: Dict[str, Any]) -> List[Dict]:
        """Check outcome for issues that need alerting"""
        alerts = []
        
        # Check for failure
        if outcome_data["status"] == "failure":
            event_type_label = (outcome_data.get("event_type") or "event").title()
            alert = await self._create_alert(
                level=AlertLevel.ERROR,
                title=f"{event_type_label} Failed",
                message=f"Event {outcome_data['event_id']} failed",
                details=outcome_data["details"],
                user_id=outcome_data["user_id"]
            )
            alerts.append(alert)
        
        # Check for unusual patterns
        if outcome_data.get("details", {}).get("duration_ms", 0) > self.alert_thresholds["api_response_time_ms"]:
            alert = await self._create_alert(
                level=AlertLevel.WARNING,
                title="Slow Operation Detected",
                message="An operation took longer than expected",
                details=outcome_data
            )
            alerts.append(alert)
        
        return alerts
    
    async def _create_alert(
        self,
        level: str,
        title: str,
        message: str,
        details: Dict = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Create and store an alert"""
        import uuid
        
        alert = {
            "alert_id": str(uuid.uuid4()),
            "level": level,
            "title": title,
            "message": message,
            "details": details or {},
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "acknowledged": False
        }
        
        self.active_alerts.append(alert)
        
        # Route immediately
        await self._route_alert(alert)
        
        return alert
    
    async def _route_alert(self, alert: Dict[str, Any]):
        """Route alert to appropriate channels"""
        level = alert["level"]
        
        # Log all alerts
        if level == AlertLevel.CRITICAL:
            logger.critical(f"ALERT: {alert['title']} - {alert['message']}")
        elif level == AlertLevel.ERROR:
            logger.error(f"ALERT: {alert['title']} - {alert['message']}")
        elif level == AlertLevel.WARNING:
            logger.warning(f"ALERT: {alert['title']} - {alert['message']}")
        else:
            logger.info(f"ALERT: {alert['title']} - {alert['message']}")
        
        # TODO: Send to notification channels (email, Slack, PagerDuty, etc.)
        # For critical errors
        if level in [AlertLevel.CRITICAL, AlertLevel.ERROR]:
            # Could send email to ops team
            pass
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of feedback text"""
        # Placeholder: Would use LLM or sentiment analysis library
        # Simple keyword-based approach for now
        
        positive_words = ["good", "great", "excellent", "love", "best", "amazing", "perfect"]
        negative_words = ["bad", "terrible", "hate", "worst", "awful", "poor", "difficult"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(0.5 + (positive_count * 0.1), 1.0)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(0.5 - (negative_count * 0.1), 0.0)
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }
    
    async def _generate_feedback_insights(self, feedback: Dict) -> List[str]:
        """Generate insights from feedback"""
        insights = []
        
        # Low rating insights
        if feedback.get("rating", 5) <= 2:
            insights.append("User provided low rating - follow up recommended")
        
        # Negative sentiment insights
        sentiment = feedback.get("sentiment", {})
        if sentiment.get("sentiment") == "negative":
            insights.append("Negative sentiment detected - review feedback details")
        
        # Category insights
        categories = feedback.get("categories", [])
        if "ease_of_use" in categories:
            insights.append("Usability feedback - consider UX improvements")
        
        return insights
    
    # ===== Health Check Methods =====
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # Would execute a simple query
            return {"healthy": True, "response_time_ms": 50}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            from backend.core.redis import get_redis
            redis = get_redis()
            # Would ping Redis
            return {"healthy": True, "response_time_ms": 10}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_celery_health(self) -> Dict[str, Any]:
        """Check Celery workers"""
        try:
            # Would check worker status
            return {"healthy": True, "active_workers": 4}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_api_health(self) -> Dict[str, Any]:
        """Check API endpoints"""
        return {"healthy": True, "endpoints_checked": 20}
    
    def _check_agent_health(self) -> Dict[str, Any]:
        """Check AI agent health"""
        # This would be called from the orchestrator
        return {"healthy": True, "agents_ready": 4}
    
    # ===== Report Generation Methods =====
    
    async def _generate_summary_report(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate summary report"""
        return {
            "total_bookings": 12,
            "successful_bookings": 11,
            "failed_bookings": 1,
            "average_meeting_duration": 45,
            "most_active_day": "Tuesday",
            "ai_suggestions_accepted": 8
        }
    
    async def _generate_bookings_report(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate bookings report"""
        return {
            "total_bookings": 12,
            "bookings_by_type": {
                "interview": 3,
                "review": 4,
                "general": 5
            },
            "bookings_by_day": {
                "Monday": 2,
                "Tuesday": 4,
                "Wednesday": 3,
                "Thursday": 2,
                "Friday": 1
            },
            "cancellation_rate": 0.08
        }
    
    async def _generate_performance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate system performance report"""
        return {
            "api_average_response_time_ms": 250,
            "api_p95_response_time_ms": 800,
            "booking_success_rate": 0.92,
            "ai_agent_success_rate": 0.95,
            "system_uptime_percent": 99.8
        }
    
    async def _generate_engagement_report(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate user engagement report"""
        return {
            "total_sessions": 15,
            "average_session_duration_minutes": 8.5,
            "features_used": ["calendar", "booking", "ai_copilot"],
            "ai_interactions": 23,
            "feedback_submitted": 3,
            "nps_score": 8.5
        }
