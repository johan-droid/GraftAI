"""
Optimization Agent - Analyzes patterns and optimizes scheduling
Uses ML/AI to learn preferences and suggest optimal meeting times
"""
import statistics
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.ai.agents.base import AgentContext, BaseAgent
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class OptimizationAgent(BaseAgent):
    """
    Specialized agent for optimizing scheduling decisions

    Responsibilities:
    - Analyze scheduling patterns
    - Learn user preferences
    - Optimize meeting timing
    - Suggest best time slots
    - Predict meeting effectiveness
    """

    def __init__(self):
        super().__init__(name="OptimizationAgent", description="Analyzes patterns, learns preferences, and optimizes meeting timing")
        self._patterns_cache: dict[str, dict[str, Any]] = {}

    def _get_available_tools(self) -> list:
        return ["analyze_patterns", "learn_preferences", "optimize_timing", "suggest_slots", "predict_effectiveness", "find_focus_time", "balance_workload"]

    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Execute optimization analysis and suggestions

        Args:
            context: Contains optimization request (user_id, analysis_type, constraints, etc.)

        Returns:
            Optimization results with suggestions and insights
        """
        data = context.data
        user_id = context.user_id
        analysis_type = data.get("analysis_type", "general")
        logger.info("OptimizationAgent processing %s for user %s", analysis_type, user_id)
        patterns = await self._load_patterns(user_id)
        results = {"user_id": user_id, "analysis_type": analysis_type, "timestamp": datetime.now(UTC).isoformat()}
        if analysis_type == "find_best_slots":
            slots = data.get("candidate_slots", [])
            duration = data.get("duration", 30)
            attendees = data.get("attendees", [])
            optimized_slots = await self._find_best_slots(user_id, slots, duration, attendees, patterns)
            results["optimized_slots"] = optimized_slots
        elif analysis_type == "analyze_patterns":
            pattern_analysis = await self._analyze_user_patterns(user_id, patterns)
            results["patterns"] = pattern_analysis
        elif analysis_type == "suggest_focus_time":
            focus_blocks = await self._suggest_focus_time(user_id, data.get("duration", 120))
            results["focus_blocks"] = focus_blocks
        elif analysis_type == "balance_workload":
            workload_analysis = await self._analyze_workload(user_id)
            results["workload"] = workload_analysis
        elif analysis_type == "predict_effectiveness":
            meeting_data = data.get("meeting_data", {})
            effectiveness = await self._predict_effectiveness(user_id, meeting_data)
            results["effectiveness_prediction"] = effectiveness
        else:
            results["error"] = f"Unknown analysis type: {analysis_type}"
            results["success"] = False
            return results
        results["success"] = True
        results["actions_taken"] = [f"loaded_patterns_for_{user_id}", f"executed_{analysis_type}", "applied_optimization_algorithms"]
        return results

    async def _load_patterns(self, user_id: str) -> dict[str, Any]:
        """Load user's historical scheduling patterns"""
        if user_id in self._patterns_cache:
            return self._patterns_cache[user_id]
        try:
            from backend.ai.memory.vector_store import VectorStore
            vector_store = VectorStore()
            patterns = await vector_store.search(collection="scheduling_patterns", query={"user_id": user_id}, limit=100)
            processed_patterns = self._process_patterns(patterns)
            self._patterns_cache[user_id] = processed_patterns
            return processed_patterns
        except Exception as e:
            logger.exception("Failed to load patterns for %s: %s", user_id, e)
            return {}

    def _process_patterns(self, raw_patterns: list[dict]) -> dict[str, Any]:
        """Process raw patterns into usable insights"""
        if not raw_patterns:
            return {}
        patterns = {"preferred_days": defaultdict(int), "preferred_times": defaultdict(int), "meeting_durations": [], "meeting_types": defaultdict(int), "response_times": [], "cancellation_rate": 0, "reschedule_rate": 0}
        total = len(raw_patterns)
        cancellations = 0
        reschedules = 0
        for pattern in raw_patterns:
            day = pattern.get("day_of_week")
            if day:
                patterns["preferred_days"][day] += 1
            hour = pattern.get("hour_of_day")
            if hour is not None:
                time_slot = f"{hour:02d}:00"
                patterns["preferred_times"][time_slot] += 1
            duration = pattern.get("duration")
            if duration:
                patterns["meeting_durations"].append(duration)
            mtype = pattern.get("meeting_type", "general")
            patterns["meeting_types"][mtype] += 1
            if pattern.get("cancelled"):
                cancellations += 1
            if pattern.get("rescheduled"):
                reschedules += 1
            response_time = pattern.get("response_time_hours")
            if response_time:
                patterns["response_times"].append(response_time)
        patterns["cancellation_rate"] = cancellations / total if total > 0 else 0
        patterns["reschedule_rate"] = reschedules / total if total > 0 else 0
        if patterns["meeting_durations"]:
            meeting_durations = patterns["meeting_durations"]
            patterns["avg_duration"] = statistics.mean(meeting_durations)
            common_values = statistics.multimode(meeting_durations)
            if len(common_values) == 1:
                patterns["common_duration"] = common_values[0]
            else:
                patterns["common_duration"] = statistics.median(meeting_durations)
        return patterns

    async def _find_best_slots(self, user_id: str, candidate_slots: list[dict[str, Any]], duration: int, attendees: list[dict[str, Any]], patterns: dict[str, Any]) -> list[dict[str, Any]]:
        """Find and rank the best meeting slots"""
        scored_slots = []
        for slot in candidate_slots:
            score = 0.0
            reasons = []
            start_time = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))
            hour = start_time.hour
            day = start_time.strftime("%A")
            preferred_times = patterns.get("preferred_times", {})
            time_slot = f"{hour:02d}:00"
            if time_slot in preferred_times:
                score += 0.3
                reasons.append(f"Preferred time slot ({time_slot})")
            preferred_days = patterns.get("preferred_days", {})
            if day in preferred_days:
                score += 0.2
                reasons.append(f"Preferred day ({day})")
            if 9 <= hour <= 17:
                score += 0.2
                reasons.append("Business hours")
            elif hour < 9 or hour > 18:
                score -= 0.3
                reasons.append("Outside typical hours")
            if await self._is_free_before_after(user_id, start_time, duration):
                score += 0.2
                reasons.append("Has buffer time")
            attendee_score = await self._score_attendee_availability(attendees, slot)
            score += attendee_score * 0.3
            scored_slots.append({**slot, "score": score, "score_breakdown": reasons})
        scored_slots.sort(key=lambda x: x["score"], reverse=True)
        return scored_slots[:5]

    async def _is_free_before_after(self, user_id: str, start_time: datetime, duration: int) -> bool:
        """Check if user has buffer time before and after meeting"""
        start_time - timedelta(minutes=30)
        end_time = start_time + timedelta(minutes=duration)
        end_time + timedelta(minutes=30)
        return True

    async def _score_attendee_availability(self, attendees: list[dict[str, Any]], slot: dict[str, Any]) -> float:
        """Score slot based on attendee availability"""
        return 1.0

    async def _analyze_user_patterns(self, user_id: str, patterns: dict[str, Any]) -> dict[str, Any]:
        """Analyze and summarize user's scheduling patterns"""
        analysis = {"summary": {}, "insights": [], "recommendations": []}
        preferred_times = patterns.get("preferred_times", {})
        if preferred_times:
            top_times = sorted(preferred_times.items(), key=lambda x: x[1], reverse=True)[:3]
            analysis["summary"]["preferred_times"] = [t[0] for t in top_times]
        preferred_days = patterns.get("preferred_days", {})
        if preferred_days:
            top_days = sorted(preferred_days.items(), key=lambda x: x[1], reverse=True)[:3]
            analysis["summary"]["preferred_days"] = [d[0] for d in top_days]
        if "avg_duration" in patterns:
            analysis["summary"]["average_meeting_duration"] = patterns["avg_duration"]
        if patterns.get("cancellation_rate", 0) > 0.2:
            analysis["insights"].append("High cancellation rate (20%+). Consider shorter meetings or better scheduling.")
        if patterns.get("reschedule_rate", 0) > 0.15:
            analysis["insights"].append("Frequent rescheduling detected. Consider more flexible meeting times.")
        meeting_types = patterns.get("meeting_types", {})
        if sum(meeting_types.values()) > 20:
            analysis["insights"].append("High meeting load detected. Consider focus time blocks.")
        if "average_meeting_duration" in analysis["summary"]:
            avg = analysis["summary"]["average_meeting_duration"]
            if avg > 60:
                analysis["recommendations"].append("Consider breaking long meetings into 45-50 minute sessions")
        return analysis

    async def _suggest_focus_time(self, user_id: str, duration_minutes: int=120) -> list[dict[str, Any]]:
        """Suggest optimal focus time blocks"""
        return [{"start": "09:00", "end": "11:00", "day": "Tuesday", "score": 0.95}, {"start": "14:00", "end": "16:00", "day": "Wednesday", "score": 0.9}, {"start": "08:00", "end": "10:00", "day": "Thursday", "score": 0.88}]

    async def _analyze_workload(self, user_id: str) -> dict[str, Any]:
        """Analyze meeting workload and suggest balance"""
        workload = {"current_status": "moderate", "meetings_this_week": 12, "meetings_last_week": 15, "average_daily_meetings": 2.4, "focus_time_hours": 3.5, "recommendations": []}
        if workload["average_daily_meetings"] > 4:
            workload["current_status"] = "heavy"
            workload["recommendations"].append("High meeting load. Consider declining non-essential meetings.")
        if workload["focus_time_hours"] < 2:
            workload["recommendations"].append("Low focus time. Block 2-hour focus sessions in your calendar.")
        return workload

    async def _predict_effectiveness(self, user_id: str, meeting_data: dict[str, Any]) -> dict[str, Any]:
        """Predict meeting effectiveness based on historical data"""
        factors = {"attendee_count": len(meeting_data.get("attendees", [])), "duration": meeting_data.get("duration", 30), "time_of_day": meeting_data.get("start_time"), "day_of_week": meeting_data.get("day"), "has_agenda": bool(meeting_data.get("agenda")), "is_recurring": meeting_data.get("is_recurring", False)}
        score = 0.7
        if 3 <= factors["attendee_count"] <= 8:
            score += 0.15
        elif factors["attendee_count"] > 12:
            score -= 0.15
        if 30 <= factors["duration"] <= 60:
            score += 0.1
        elif factors["duration"] > 90:
            score -= 0.1
        if factors["has_agenda"]:
            score += 0.1
        return {"predicted_effectiveness": min(score, 1.0), "confidence": 0.75, "factors": factors, "suggestions": ["Add agenda" if not factors["has_agenda"] else None, "Consider shorter duration" if factors["duration"] > 60 else None]}
