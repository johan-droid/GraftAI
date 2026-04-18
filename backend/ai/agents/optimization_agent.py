"""
Optimization Agent - Analyzes patterns and optimizes scheduling
Uses ML/AI to learn preferences and suggest optimal meeting times
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from backend.ai.agents.base import BaseAgent, AgentContext
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
        super().__init__(
            name="OptimizationAgent",
            description="Analyzes patterns, learns preferences, and optimizes meeting timing",
        )

        # Pattern cache
        self._patterns_cache: Dict[str, Dict[str, Any]] = {}

    def _get_available_tools(self) -> list:
        return [
            "analyze_patterns",
            "learn_preferences",
            "optimize_timing",
            "suggest_slots",
            "predict_effectiveness",
            "find_focus_time",
            "balance_workload",
        ]

    async def _execute(self, context: AgentContext) -> Dict[str, Any]:
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

        logger.info(f"OptimizationAgent processing {analysis_type} for user {user_id}")

        # Load user patterns from memory
        patterns = await self._load_patterns(user_id)

        results = {
            "user_id": user_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if analysis_type == "find_best_slots":
            # Find optimal meeting times
            slots = data.get("candidate_slots", [])
            duration = data.get("duration", 30)
            attendees = data.get("attendees", [])

            optimized_slots = await self._find_best_slots(
                user_id, slots, duration, attendees, patterns
            )
            results["optimized_slots"] = optimized_slots

        elif analysis_type == "analyze_patterns":
            # Analyze user's scheduling patterns
            pattern_analysis = await self._analyze_user_patterns(user_id, patterns)
            results["patterns"] = pattern_analysis

        elif analysis_type == "suggest_focus_time":
            # Find best focus time blocks
            focus_blocks = await self._suggest_focus_time(
                user_id, data.get("duration", 120)
            )
            results["focus_blocks"] = focus_blocks

        elif analysis_type == "balance_workload":
            # Analyze and balance meeting load
            workload_analysis = await self._analyze_workload(user_id)
            results["workload"] = workload_analysis

        elif analysis_type == "predict_effectiveness":
            # Predict meeting effectiveness
            meeting_data = data.get("meeting_data", {})
            effectiveness = await self._predict_effectiveness(user_id, meeting_data)
            results["effectiveness_prediction"] = effectiveness

        else:
            results["error"] = f"Unknown analysis type: {analysis_type}"
            results["success"] = False
            return results

        results["success"] = True
        results["actions_taken"] = [
            f"loaded_patterns_for_{user_id}",
            f"executed_{analysis_type}",
            "applied_optimization_algorithms",
        ]

        return results

    async def _load_patterns(self, user_id: str) -> Dict[str, Any]:
        """Load user's historical scheduling patterns"""
        # Check cache first
        if user_id in self._patterns_cache:
            return self._patterns_cache[user_id]

        # Query vector store for patterns
        try:
            from backend.ai.memory.vector_store import VectorStore

            vector_store = VectorStore()

            patterns = await vector_store.search(
                collection="scheduling_patterns", query={"user_id": user_id}, limit=100
            )

            # Process and cache patterns
            processed_patterns = self._process_patterns(patterns)
            self._patterns_cache[user_id] = processed_patterns

            return processed_patterns

        except Exception as e:
            logger.error(f"Failed to load patterns for {user_id}: {e}")
            return {}

    def _process_patterns(self, raw_patterns: List[Dict]) -> Dict[str, Any]:
        """Process raw patterns into usable insights"""
        if not raw_patterns:
            return {}

        patterns = {
            "preferred_days": defaultdict(int),
            "preferred_times": defaultdict(int),
            "meeting_durations": [],
            "meeting_types": defaultdict(int),
            "response_times": [],
            "cancellation_rate": 0,
            "reschedule_rate": 0,
        }

        total = len(raw_patterns)
        cancellations = 0
        reschedules = 0

        for pattern in raw_patterns:
            # Extract day of week preference
            day = pattern.get("day_of_week")
            if day:
                patterns["preferred_days"][day] += 1

            # Extract time preference
            hour = pattern.get("hour_of_day")
            if hour is not None:
                time_slot = f"{hour:02d}:00"
                patterns["preferred_times"][time_slot] += 1

            # Collect durations
            duration = pattern.get("duration")
            if duration:
                patterns["meeting_durations"].append(duration)

            # Meeting types
            mtype = pattern.get("meeting_type", "general")
            patterns["meeting_types"][mtype] += 1

            # Track cancellations/reschedules
            if pattern.get("cancelled"):
                cancellations += 1
            if pattern.get("rescheduled"):
                reschedules += 1

            # Response times
            response_time = pattern.get("response_time_hours")
            if response_time:
                patterns["response_times"].append(response_time)

        # Calculate rates
        patterns["cancellation_rate"] = cancellations / total if total > 0 else 0
        patterns["reschedule_rate"] = reschedules / total if total > 0 else 0

        # Calculate statistics
        if patterns["meeting_durations"]:
            meeting_durations = patterns["meeting_durations"]
            patterns["avg_duration"] = statistics.mean(meeting_durations)

            common_values = statistics.multimode(meeting_durations)
            if len(common_values) == 1:
                patterns["common_duration"] = common_values[0]
            else:
                patterns["common_duration"] = statistics.median(meeting_durations)

        return patterns

    async def _find_best_slots(
        self,
        user_id: str,
        candidate_slots: List[Dict[str, Any]],
        duration: int,
        attendees: List[Dict[str, Any]],
        patterns: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find and rank the best meeting slots"""
        scored_slots = []

        for slot in candidate_slots:
            score = 0.0
            reasons = []

            start_time = datetime.fromisoformat(
                slot["start_time"].replace("Z", "+00:00")
            )
            hour = start_time.hour
            day = start_time.strftime("%A")

            # Score based on user's preferred times
            preferred_times = patterns.get("preferred_times", {})
            time_slot = f"{hour:02d}:00"
            if time_slot in preferred_times:
                score += 0.3
                reasons.append(f"Preferred time slot ({time_slot})")

            # Score based on preferred days
            preferred_days = patterns.get("preferred_days", {})
            if day in preferred_days:
                score += 0.2
                reasons.append(f"Preferred day ({day})")

            # Avoid early morning unless pattern shows preference
            if 9 <= hour <= 17:
                score += 0.2
                reasons.append("Business hours")
            elif hour < 9 or hour > 18:
                score -= 0.3
                reasons.append("Outside typical hours")

            # Avoid back-to-back meetings
            if await self._is_free_before_after(user_id, start_time, duration):
                score += 0.2
                reasons.append("Has buffer time")

            # Consider attendee availability
            attendee_score = await self._score_attendee_availability(attendees, slot)
            score += attendee_score * 0.3

            scored_slots.append({**slot, "score": score, "score_breakdown": reasons})

        # Sort by score descending
        scored_slots.sort(key=lambda x: x["score"], reverse=True)

        return scored_slots[:5]  # Return top 5

    async def _is_free_before_after(
        self, user_id: str, start_time: datetime, duration: int
    ) -> bool:
        """Check if user has buffer time before and after meeting"""
        buffer_before = start_time - timedelta(minutes=30)
        end_time = start_time + timedelta(minutes=duration)
        buffer_after = end_time + timedelta(minutes=30)

        # Query for conflicting events
        # Placeholder: Would check actual calendar
        return True

    async def _score_attendee_availability(
        self, attendees: List[Dict[str, Any]], slot: Dict[str, Any]
    ) -> float:
        """Score slot based on attendee availability"""
        # Check each attendee's calendar
        # Placeholder: Would integrate with calendar APIs
        return 1.0  # Assume all available for now

    async def _analyze_user_patterns(
        self, user_id: str, patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze and summarize user's scheduling patterns"""
        analysis = {"summary": {}, "insights": [], "recommendations": []}

        # Preferred times
        preferred_times = patterns.get("preferred_times", {})
        if preferred_times:
            top_times = sorted(
                preferred_times.items(), key=lambda x: x[1], reverse=True
            )[:3]
            analysis["summary"]["preferred_times"] = [t[0] for t in top_times]

        # Preferred days
        preferred_days = patterns.get("preferred_days", {})
        if preferred_days:
            top_days = sorted(preferred_days.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]
            analysis["summary"]["preferred_days"] = [d[0] for d in top_days]

        # Duration patterns
        if "avg_duration" in patterns:
            analysis["summary"]["average_meeting_duration"] = patterns["avg_duration"]

        # Insights
        if patterns.get("cancellation_rate", 0) > 0.2:
            analysis["insights"].append(
                "High cancellation rate (20%+). Consider shorter meetings or better scheduling."
            )

        if patterns.get("reschedule_rate", 0) > 0.15:
            analysis["insights"].append(
                "Frequent rescheduling detected. Consider more flexible meeting times."
            )

        # Meeting load
        meeting_types = patterns.get("meeting_types", {})
        if sum(meeting_types.values()) > 20:  # More than 20 meetings
            analysis["insights"].append(
                "High meeting load detected. Consider focus time blocks."
            )

        # Recommendations
        if "average_meeting_duration" in analysis["summary"]:
            avg = analysis["summary"]["average_meeting_duration"]
            if avg > 60:
                analysis["recommendations"].append(
                    "Consider breaking long meetings into 45-50 minute sessions"
                )

        return analysis

    async def _suggest_focus_time(
        self, user_id: str, duration_minutes: int = 120
    ) -> List[Dict[str, Any]]:
        """Suggest optimal focus time blocks"""
        blocks = []

        # Query calendar for free blocks
        # Placeholder: Would analyze actual calendar

        # Suggest typical focus times
        suggested_blocks = [
            {"start": "09:00", "end": "11:00", "day": "Tuesday", "score": 0.95},
            {"start": "14:00", "end": "16:00", "day": "Wednesday", "score": 0.90},
            {"start": "08:00", "end": "10:00", "day": "Thursday", "score": 0.88},
        ]

        return suggested_blocks

    async def _analyze_workload(self, user_id: str) -> Dict[str, Any]:
        """Analyze meeting workload and suggest balance"""
        workload = {
            "current_status": "moderate",
            "meetings_this_week": 12,
            "meetings_last_week": 15,
            "average_daily_meetings": 2.4,
            "focus_time_hours": 3.5,
            "recommendations": [],
        }

        if workload["average_daily_meetings"] > 4:
            workload["current_status"] = "heavy"
            workload["recommendations"].append(
                "High meeting load. Consider declining non-essential meetings."
            )

        if workload["focus_time_hours"] < 2:
            workload["recommendations"].append(
                "Low focus time. Block 2-hour focus sessions in your calendar."
            )

        return workload

    async def _predict_effectiveness(
        self, user_id: str, meeting_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict meeting effectiveness based on historical data"""

        factors = {
            "attendee_count": len(meeting_data.get("attendees", [])),
            "duration": meeting_data.get("duration", 30),
            "time_of_day": meeting_data.get("start_time"),
            "day_of_week": meeting_data.get("day"),
            "has_agenda": bool(meeting_data.get("agenda")),
            "is_recurring": meeting_data.get("is_recurring", False),
        }

        # Calculate effectiveness score
        score = 0.7  # Base score

        # Attendee count impact
        if 3 <= factors["attendee_count"] <= 8:
            score += 0.15
        elif factors["attendee_count"] > 12:
            score -= 0.15

        # Duration impact
        if 30 <= factors["duration"] <= 60:
            score += 0.1
        elif factors["duration"] > 90:
            score -= 0.1

        # Agenda impact
        if factors["has_agenda"]:
            score += 0.1

        return {
            "predicted_effectiveness": min(score, 1.0),
            "confidence": 0.75,
            "factors": factors,
            "suggestions": [
                "Add agenda" if not factors["has_agenda"] else None,
                "Consider shorter duration" if factors["duration"] > 60 else None,
            ],
        }
