"""
Intelligent Fallback System for GraftAI Booking Automation

Provides multi-level fallback to ensure bookings are always handled:

Level 1: Full AI Agent (4-phase loop with LLM reasoning)
Level 2: Rule-Based Engine (fast deterministic decisions)
Level 3: Manual Review (notify admin for human handling)

┌──────────────────────────────────────────────────────────────┐
│                FALLBACK HIERARCHY                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  LEVEL 1: AI AGENT                                          │
│  ├─ Full 4-phase loop                                       │
│  ├─ LLM reasoning + decision engine                         │
│  ├─ Multi-layer memory                                      │
│  ├─ Tool selection + execution                              │
│  └─ Latency: 500-3000ms                                     │
│       ↓ (on failure)                                        │
│                                                              │
│  LEVEL 2: RULE-BASED ENGINE                                 │
│  ├─ Deterministic rule matching                             │
│  ├─ Risk-level based actions                                │
│  ├─ VIP-level templates                                     │
│  ├─ Standard tool execution                                 │
│  └─ Latency: 50-200ms                                      │
│       ↓ (on failure)                                        │
│                                                              │
│  LEVEL 3: MANUAL REVIEW                                     │
│  ├─ Notify admin via Slack/email                            │
│  ├─ Create review task in CRM                               │
│  ├─ Mark booking as pending_review                          │
│  └─ Latency: Notification only                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncio

from backend.utils.logger import get_logger
from backend.ai.monitoring import get_agent_metrics, log_error

logger = get_logger(__name__)


class FallbackLevel(Enum):
    """Fallback hierarchy levels"""

    AI_AGENT = "ai_agent"
    RULE_BASED = "rule_based"
    MANUAL_REVIEW = "manual_review"


class BookingRiskLevel(Enum):
    """Risk level classification"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BookingVIPLevel(Enum):
    """VIP level classification"""

    STANDARD = "standard"
    PREFERRED = "preferred"
    VIP = "vip"
    EXECUTIVE = "executive"


@dataclass
class FallbackResult:
    """Result from fallback execution"""

    booking_id: str
    status: str  # completed, partial, pending_review
    mode: FallbackLevel
    actions: List[Dict[str, Any]]
    error: Optional[str] = None
    execution_time_ms: float = 0
    timestamp: str = ""


# ═══════════════════════════════════════════════════════════════════
# RULE-BASED FALLBACK ENGINE
# ═══════════════════════════════════════════════════════════════════


class RuleBasedFallbackEngine:
    """
    Deterministic rule-based fallback when AI agent fails.

    Uses simple heuristics to decide actions based on:
    - No-show rate
    - VIP level
    - Booking value
    - Time until meeting
    """

    def __init__(self):
        self.rules = self._load_rules()
        logger.info("RuleBasedFallbackEngine initialized")

    def _load_rules(self) -> Dict[str, Any]:
        """Load rule definitions"""
        return {
            # High-risk rules (no-show rate > 30%)
            "high_risk": {
                "conditions": {"no_show_rate_gt": 0.3},
                "actions": [
                    {
                        "type": "send_email",
                        "template": "high_risk_confirmation",
                        "priority": "critical",
                    },
                    {"type": "send_sms", "template": "reminder", "priority": "high"},
                    {"type": "create_calendar_event", "priority": "high"},
                    {
                        "type": "create_task",
                        "task_type": "monitoring",
                        "priority": "high",
                    },
                ],
                "risk_level": BookingRiskLevel.HIGH,
                "human_review": False,
            },
            # VIP rules
            "vip": {
                "conditions": {"vip_level_in": ["vip", "executive"]},
                "actions": [
                    {
                        "type": "send_email",
                        "template": "vip_welcome",
                        "priority": "critical",
                    },
                    {
                        "type": "send_sms",
                        "template": "vip_confirmation",
                        "priority": "high",
                    },
                    {"type": "create_calendar_event", "priority": "critical"},
                    {
                        "type": "create_task",
                        "task_type": "vip_followup",
                        "priority": "critical",
                    },
                    {
                        "type": "post_to_slack",
                        "channel": "#vip-bookings",
                        "priority": "high",
                    },
                ],
                "risk_level": BookingRiskLevel.LOW,
                "human_review": False,
            },
            # Critical risk (no-show rate > 60%)
            "critical_risk": {
                "conditions": {"no_show_rate_gt": 0.6},
                "actions": [
                    {
                        "type": "send_email",
                        "template": "critical_confirmation",
                        "priority": "critical",
                    },
                    {
                        "type": "send_sms",
                        "template": "urgent_reminder",
                        "priority": "critical",
                    },
                    {"type": "create_calendar_event", "priority": "critical"},
                    {
                        "type": "create_task",
                        "task_type": "critical_monitoring",
                        "priority": "critical",
                    },
                    {
                        "type": "post_to_slack",
                        "channel": "#critical-bookings",
                        "priority": "critical",
                    },
                ],
                "risk_level": BookingRiskLevel.CRITICAL,
                "human_review": True,
            },
            # Standard rules (default)
            "standard": {
                "conditions": {},
                "actions": [
                    {
                        "type": "send_email",
                        "template": "standard_confirmation",
                        "priority": "medium",
                    },
                    {"type": "create_calendar_event", "priority": "medium"},
                    {
                        "type": "create_task",
                        "task_type": "follow_up",
                        "priority": "low",
                    },
                ],
                "risk_level": BookingRiskLevel.LOW,
                "human_review": False,
            },
        }

    def evaluate(
        self, booking: Dict[str, Any], attendee: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate booking against rules and return actions

        Args:
            booking: Booking data
            attendee: Attendee data

        Returns:
            Rule evaluation result with actions
        """
        no_show_rate = attendee.get("no_show_rate", 0)
        vip_level = attendee.get("vip_level", "standard")

        # Match rules in priority order
        matched_rule = None

        # Check critical risk first
        if no_show_rate > 0.6:
            matched_rule = self.rules["critical_risk"]
        # Check VIP
        elif vip_level in ["vip", "executive"]:
            matched_rule = self.rules["vip"]
        # Check high risk
        elif no_show_rate > 0.3:
            matched_rule = self.rules["high_risk"]
        # Default to standard
        else:
            matched_rule = self.rules["standard"]

        logger.info(
            f"Rule matched: {matched_rule.get('risk_level', BookingRiskLevel.LOW).value} "
            f"for booking {booking.get('id', 'unknown')}"
        )

        return {
            "actions": matched_rule["actions"],
            "risk_level": matched_rule["risk_level"].value,
            "human_review": matched_rule.get("human_review", False),
            "matched_rule": [k for k, v in self.rules.items() if v is matched_rule][0],
        }

    async def execute(
        self, booking: Dict[str, Any], attendee: Dict[str, Any]
    ) -> FallbackResult:
        """
        Execute rule-based fallback

        Args:
            booking: Booking data
            attendee: Attendee data

        Returns:
            FallbackResult with actions taken
        """
        start_time = datetime.utcnow()
        booking_id = booking.get("id", "unknown")

        logger.info(f"[{booking_id}] Executing rule-based fallback")

        try:
            # Evaluate rules
            evaluation = self.evaluate(booking, attendee)

            # Execute actions
            action_results = []
            for action in evaluation["actions"]:
                result = await self._execute_action(action, booking, attendee)
                action_results.append(result)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Determine status
            success = all(r.get("success") for r in action_results)
            status = "completed" if success else "partial"

            # If human review needed, escalate
            if evaluation.get("human_review"):
                await self._escalate_to_manual(
                    booking_id, "Rule-based detected need for human review"
                )
                status = "pending_review"

            return FallbackResult(
                booking_id=booking_id,
                status=status,
                mode=FallbackLevel.RULE_BASED,
                actions=action_results,
                execution_time_ms=execution_time,
                timestamp=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"[{booking_id}] Rule-based fallback failed: {e}")
            return FallbackResult(
                booking_id=booking_id,
                status="failed",
                mode=FallbackLevel.RULE_BASED,
                actions=[],
                error=str(e),
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds()
                * 1000,
                timestamp=datetime.utcnow().isoformat(),
            )

    async def _execute_action(
        self, action: Dict[str, Any], booking: Dict[str, Any], attendee: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single rule-based action"""
        action_type = action.get("type")

        try:
            if action_type == "send_email":
                from backend.ai.tools import send_email

                result = await send_email(
                    to=attendee.get("email", ""),
                    subject=f"Booking Confirmation: {booking.get('title', 'Meeting')}",
                    body=f"Your booking has been confirmed for {booking.get('start_time', 'TBD')}.",
                    template=action.get("template", "standard_confirmation"),
                )
                return {"tool_name": "send_email", "success": True, **result}

            elif action_type == "send_sms":
                from backend.ai.tools import send_sms

                result = await send_sms(
                    to=attendee.get("phone", ""),
                    message=f"Reminder: Your meeting '{booking.get('title')}' is scheduled.",
                )
                return {"tool_name": "send_sms", "success": True, **result}

            elif action_type == "create_calendar_event":
                from backend.ai.tools import create_calendar_event

                result = await create_calendar_event(
                    title=booking.get("title", "Meeting"),
                    start_time=booking.get("start_time", ""),
                    duration_minutes=booking.get("duration_minutes", 30),
                    attendees=[attendee.get("email", "")],
                )
                return {"tool_name": "create_calendar_event", "success": True, **result}

            elif action_type == "create_task":
                from backend.ai.tools import create_task

                result = await create_task(
                    contact_id=attendee.get("id", ""),
                    task_type=action.get("task_type", "follow_up"),
                    title=f"Follow up: {booking.get('title', 'Booking')}",
                    priority=action.get("priority", "medium"),
                )
                return {"tool_name": "create_task", "success": True, **result}

            elif action_type == "post_to_slack":
                from backend.ai.tools import post_to_slack

                result = await post_to_slack(
                    channel=action.get("channel", "#bookings"),
                    message=f"Booking created: {booking.get('title')} for {attendee.get('name', 'attendee')}",
                )
                return {"tool_name": "post_to_slack", "success": True, **result}

            else:
                logger.warning(f"Unknown action type: {action_type}")
                return {
                    "tool_name": action_type,
                    "success": False,
                    "error": "Unknown action",
                }

        except Exception as e:
            logger.error(f"Action {action_type} failed: {e}")
            return {"tool_name": action_type, "success": False, "error": str(e)}

    async def _escalate_to_manual(self, booking_id: str, reason: str):
        """Escalate to manual review"""
        await AdminNotifier.notify(booking_id=booking_id, reason=reason, urgency="high")


# ═══════════════════════════════════════════════════════════════════
# ADMIN NOTIFICATION SYSTEM
# ═══════════════════════════════════════════════════════════════════


class AdminNotifier:
    """
    Notify administrators when automation requires manual review

    Channels:
    - Slack notification
    - Email to admin
    - CRM task creation
    """

    ADMIN_EMAIL = "admin@graftai.com"
    ADMIN_SLACK_CHANNEL = "#booking-review"

    @staticmethod
    async def notify(
        booking_id: str,
        reason: str,
        urgency: str = "high",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Notify admin about booking needing manual review

        Args:
            booking_id: Booking ID
            reason: Reason for escalation
            urgency: Urgency level (low, medium, high, critical)
            details: Additional details

        Returns:
            Notification results
        """
        logger.warning(
            f"🔔 Admin notification: Booking {booking_id} needs review - {reason}"
        )

        results = {}

        # 1. Send Slack notification
        try:
            from backend.ai.tools import post_to_slack

            slack_result = await post_to_slack(
                channel=AdminNotifier.ADMIN_SLACK_CHANNEL,
                message=(
                    f"⚠️ *Manual Review Required*\n"
                    f"Booking: `{booking_id}`\n"
                    f"Reason: {reason}\n"
                    f"Urgency: {urgency}\n"
                    f"Time: {datetime.utcnow().isoformat()}"
                ),
            )
            results["slack"] = slack_result
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            results["slack"] = {"error": str(e)}

        # 2. Send email to admin
        try:
            from backend.ai.tools import send_email

            email_result = await send_email(
                to=AdminNotifier.ADMIN_EMAIL,
                subject=f"[{urgency.upper()}] Manual Review: Booking {booking_id}",
                body=(
                    f"Booking {booking_id} requires manual review.\n\n"
                    f"Reason: {reason}\n"
                    f"Urgency: {urgency}\n"
                    f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
                    f"Details: {details or 'None provided'}\n\n"
                    f"Please review and take appropriate action."
                ),
            )
            results["email"] = email_result
        except Exception as e:
            logger.error(f"Failed to send admin email: {e}")
            results["email"] = {"error": str(e)}

        # 3. Create review task in CRM
        try:
            from backend.ai.tools import create_task

            task_result = await create_task(
                contact_id="admin",
                task_type="manual_review",
                title=f"Review booking {booking_id}",
                priority=urgency,
                description=f"Reason: {reason}. Details: {details}",
            )
            results["task"] = task_result
        except Exception as e:
            logger.error(f"Failed to create review task: {e}")
            results["task"] = {"error": str(e)}

        # Record metrics
        try:
            metrics = get_agent_metrics()
            metrics.record_error(
                error_type="manual_review_required", component="fallback_system"
            )
        except Exception:
            pass

        return results


# ═══════════════════════════════════════════════════════════════════
# INTELLIGENT FALLBACK ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════


class FallbackOrchestrator:
    """
    Orchestrates the multi-level fallback system

    Tries each level in order:
    1. AI Agent (full automation)
    2. Rule-based engine (fast fallback)
    3. Manual review (admin notification)
    """

    def __init__(self):
        self.rule_engine = RuleBasedFallbackEngine()
        self.metrics = get_agent_metrics()
        logger.info("FallbackOrchestrator initialized")

    async def automate_with_fallback(
        self, booking: Dict[str, Any], attendee: Optional[Dict[str, Any]] = None
    ) -> FallbackResult:
        """
        Automate booking with intelligent fallback

        Args:
            booking: Booking data
            attendee: Attendee data (optional)

        Returns:
            FallbackResult from the highest successful level
        """
        booking_id = booking.get("id", "unknown")
        start_time = datetime.utcnow()

        logger.info(f"[{booking_id}] Starting automation with fallback")

        # ═══════════════════════════════════════════════════════════
        # LEVEL 1: Try full AI Agent
        # ═══════════════════════════════════════════════════════════

        try:
            logger.info(f"[{booking_id}] Level 1: Attempting AI Agent automation")

            from backend.services.booking_automation import BookingAutomationService

            service = BookingAutomationService()

            result = await service.process_booking_created(
                booking_id=booking_id,
                user_id=booking.get("organizer_id", "system"),
                trigger_source="fallback_orchestrator",
            )

            # AI agent succeeded
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            logger.info(
                f"[{booking_id}] ✅ AI Agent succeeded: score={result.decision_score}"
            )

            return FallbackResult(
                booking_id=booking_id,
                status=result.automation_status,
                mode=FallbackLevel.AI_AGENT,
                actions=result.actions_executed,
                execution_time_ms=execution_time,
                timestamp=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"[{booking_id}] ❌ AI Agent failed: {e}")
            log_error(
                "ai_agent_failure",
                "fallback_orchestrator",
                str(e),
                booking_id=booking_id,
            )

        # ═══════════════════════════════════════════════════════════
        # LEVEL 2: Try rule-based fallback
        # ═══════════════════════════════════════════════════════════

        try:
            logger.info(f"[{booking_id}] Level 2: Attempting rule-based fallback")

            if attendee:
                result = await self.rule_engine.execute(booking, attendee)

                if result.status in ["completed", "partial"]:
                    logger.info(
                        f"[{booking_id}] ✅ Rule-based fallback succeeded: {result.status}"
                    )
                    return result
                else:
                    logger.warning(
                        f"[{booking_id}] Rule-based fallback returned: {result.status}"
                    )
            else:
                # No attendee data - apply default rules
                result = await self._apply_default_rules(booking)
                logger.info(f"[{booking_id}] ✅ Default rules applied")
                return result

        except Exception as e:
            logger.error(f"[{booking_id}] ❌ Rule-based fallback failed: {e}")
            log_error(
                "rule_based_failure",
                "fallback_orchestrator",
                str(e),
                booking_id=booking_id,
            )

        # ═══════════════════════════════════════════════════════════
        # LEVEL 3: Manual review
        # ═══════════════════════════════════════════════════════════

        logger.info(f"[{booking_id}] Level 3: Escalating to manual review")

        try:
            notification_results = await AdminNotifier.notify(
                booking_id=booking_id,
                reason="All automation levels failed. AI Agent and rule-based engine both encountered errors.",
                urgency="critical",
                details={
                    "booking": booking,
                    "attendee": attendee,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"[{booking_id}] Admin notification also failed: {e}")
            notification_results = {"error": str(e)}

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return FallbackResult(
            booking_id=booking_id,
            status="pending_review",
            mode=FallbackLevel.MANUAL_REVIEW,
            actions=[{"type": "admin_notification", "results": notification_results}],
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat(),
        )

    async def _apply_default_rules(self, booking: Dict[str, Any]) -> FallbackResult:
        """
        Apply default rules when no attendee data is available

        Args:
            booking: Booking data

        Returns:
            FallbackResult with standard actions
        """
        start_time = datetime.utcnow()
        booking_id = booking.get("id", "unknown")

        # Standard actions for any booking
        default_actions = [
            {
                "type": "send_email",
                "template": "standard_confirmation",
                "priority": "medium",
            },
            {"type": "create_calendar_event", "priority": "medium"},
        ]

        action_results = []
        for action in default_actions:
            result = await self.rule_engine._execute_action(
                action, booking, {"email": booking.get("attendees", [""])[0]}
            )
            action_results.append(result)

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return FallbackResult(
            booking_id=booking_id,
            status="completed"
            if all(r.get("success") for r in action_results)
            else "partial",
            mode=FallbackLevel.RULE_BASED,
            actions=action_results,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat(),
        )


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

_orchestrator: Optional[FallbackOrchestrator] = None


async def get_fallback_orchestrator() -> FallbackOrchestrator:
    """Get or create the global fallback orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FallbackOrchestrator()
    return _orchestrator


async def automate_booking_with_fallback(
    booking: Dict[str, Any], attendee: Optional[Dict[str, Any]] = None
) -> FallbackResult:
    """
    Automate booking with intelligent fallback

    This is the main entry point for booking automation with fallback support.

    Args:
        booking: Booking data
        attendee: Optional attendee data

    Returns:
        FallbackResult from highest successful level
    """
    orchestrator = await get_fallback_orchestrator()
    return await orchestrator.automate_with_fallback(booking, attendee)


async def apply_default_rules(booking: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply simple rule-based automation

    Args:
        booking: Booking data

    Returns:
        Standard actions for any booking
    """
    return {
        "actions": [
            {
                "type": "send_email",
                "template": "standard_confirmation",
                "priority": "medium",
            },
            {"type": "create_calendar_event", "priority": "medium"},
            {"type": "create_task", "task_type": "follow_up", "priority": "low"},
        ],
        "status": "completed",
        "mode": "fallback_rules",
    }


async def notify_admin(
    message: str, booking_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Notify admin about an issue

    Args:
        message: Notification message
        booking_id: Optional booking ID

    Returns:
        Notification results
    """
    return await AdminNotifier.notify(
        booking_id=booking_id or "unknown", reason=message, urgency="high"
    )


# ═══════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════


async def example_fallback_usage():
    """Example: Using the fallback system"""

    booking = {
        "id": "booking_123",
        "title": "Consultation",
        "start_time": "2024-04-15T14:00:00",
        "duration_minutes": 30,
        "organizer_id": "user_456",
        "attendees": ["john@example.com"],
    }

    attendee = {
        "email": "john@example.com",
        "name": "John Smith",
        "no_show_rate": 0.5,
        "vip_level": "standard",
    }

    # Run with full fallback support
    result = await automate_booking_with_fallback(booking, attendee)

    print(f"Status: {result.status}")
    print(f"Mode: {result.mode.value}")
    print(f"Actions: {len(result.actions)}")
    print(f"Time: {result.execution_time_ms:.0f}ms")

    # If AI fails, rule-based kicks in automatically
    # If rules fail, admin is notified automatically


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_fallback_usage())
