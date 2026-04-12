"""
Agent Decision Engine

Implements the agent's decision-making process:

Booking Created
    ↓
Agent Analyzes:
  ├─ Is attendee VIP? (frequency, value, engagement)
  ├─ Is this high-risk? (conflicts, timezone, no-show)
  ├─ What's optimal timing? (timezone, response time)
  ├─ Communication preferences? (past prefs, tolerance)
  ├─ Business rules? (industry, department, region)
  └─ Full context? (calendar, weather, events, trends)
    ↓
Agent Decides:
  ├─ Which actions (email, calendar, CRM, etc.)
  ├─ Execution order
  ├─ Priority levels
  ├─ Human review needed?
  └─ What to monitor
    ↓
Agent Executes → Agent Reflects
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from backend.utils.logger import get_logger
from backend.ai.tools.registry import ToolPriority

logger = get_logger(__name__)


class RiskLevel(Enum):
    """Risk levels for bookings"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VIPLevel(Enum):
    """VIP classification levels"""
    STANDARD = "standard"
    PREFERRED = "preferred"
    VIP = "vip"
    EXECUTIVE = "executive"


class DecisionConfidence(Enum):
    """Confidence in decision"""
    LOW = 0.5
    MEDIUM = 0.75
    HIGH = 0.9
    CERTAIN = 1.0


@dataclass
class AttendeeAnalysis:
    """Analysis of an attendee"""
    email: str
    vip_level: VIPLevel
    is_new: bool
    booking_frequency: int  # Bookings per month
    no_show_rate: float  # 0-1
    avg_response_time_hours: float
    preferred_communication: List[str]  # email, sms, slack
    engagement_score: float  # 0-1
    timezone: str
    phone: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None


@dataclass
class RiskAnalysis:
    """Risk analysis for booking"""
    level: RiskLevel
    score: float  # 0-1
    factors: List[Dict[str, Any]]  # Risk factors identified
    mitigations: List[str]  # Suggested mitigations


@dataclass
class TimingAnalysis:
    """Timing analysis for booking"""
    optimal_send_time: str  # ISO timestamp
    timezone_offset_hours: int
    expected_response_time_hours: float
    urgency_level: str  # low, medium, high
    business_hours_aligned: bool


@dataclass
class BusinessRuleCheck:
    """Business rule compliance check"""
    rule_name: str
    compliant: bool
    severity: str  # info, warning, error
    message: str
    auto_action: Optional[str] = None


@dataclass
class ContextAnalysis:
    """Full context analysis"""
    calendar_conflicts: List[Dict]
    concurrent_bookings: int
    day_of_week: str
    time_of_day: str
    weather: Optional[str] = None  # Could affect in-person meetings
    local_events: List[str] = field(default_factory=list)
    market_trends: Optional[str] = None
    company_news: List[str] = field(default_factory=list)


@dataclass
class ActionDecision:
    """A decided action"""
    tool_name: str
    parameters: Dict[str, Any]
    priority: ToolPriority
    execute_immediately: bool
    depends_on: Optional[List[str]] = None  # Must execute after these actions
    human_review_required: bool = False
    condition: Optional[str] = None  # Conditional execution


@dataclass
class AgentDecision:
    """Complete decision from the agent"""
    # Analysis results
    attendee_analysis: AttendeeAnalysis
    risk_analysis: RiskAnalysis
    timing_analysis: TimingAnalysis
    business_rules: List[BusinessRuleCheck]
    context_analysis: ContextAnalysis
    
    # Decisions
    actions: List[ActionDecision]
    execution_order: List[str]  # Ordered action IDs
    requires_human_review: bool
    human_review_reason: Optional[str] = None
    
    # Monitoring
    metrics_to_track: List[str]
    alert_thresholds: Dict[str, float]
    
    # Metadata
    confidence: DecisionConfidence
    decision_timestamp: datetime
    reasoning: str


class DecisionEngine:
    """
    Central decision engine for agent actions
    
    Analyzes bookings and decides:
    - What actions to take
    - In what order
    - At what priority
    - Whether human review needed
    """
    
    def __init__(self):
        self.vip_thresholds = {
            "booking_frequency": 5,  # >5/month = VIP
            "engagement_score": 0.8,
            "estimated_value": 1000
        }
        
        self.risk_thresholds = {
            "no_show": 0.3,  # >30% no-show rate
            "short_notice": 24,  # <24 hours
            "timezone_diff": 6,  # >6 hour difference
            "conflict_probability": 0.7
        }
    
    async def analyze_and_decide(
        self,
        booking: Dict[str, Any],
        attendee_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentDecision:
        """
        Main decision method - analyzes and decides actions
        
        Args:
            booking: Booking details
            attendee_info: Attendee profile and history
            context: Additional context (calendar, preferences, etc.)
        
        Returns:
            AgentDecision with all analysis and decided actions
        """
        logger.info(f"DecisionEngine analyzing booking for {attendee_info.get('email')}")
        
        # ═══════════════════════════════════════════════════════════════
        # 1. ATTENDEE ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        attendee_analysis = await self._analyze_attendee(attendee_info)
        
        # ═══════════════════════════════════════════════════════════════
        # 2. RISK ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        risk_analysis = await self._analyze_risk(booking, attendee_analysis)
        
        # ═══════════════════════════════════════════════════════════════
        # 3. TIMING ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        timing_analysis = await self._analyze_timing(booking, attendee_analysis)
        
        # ═══════════════════════════════════════════════════════════════
        # 4. BUSINESS RULES CHECK
        # ═══════════════════════════════════════════════════════════════
        business_rules = await self._check_business_rules(booking, attendee_analysis)
        
        # ═══════════════════════════════════════════════════════════════
        # 5. CONTEXT ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        context_analysis = await self._analyze_context(booking, context)
        
        # ═══════════════════════════════════════════════════════════════
        # 6. MAKE DECISIONS
        # ═══════════════════════════════════════════════════════════════
        actions = await self._decide_actions(
            booking,
            attendee_analysis,
            risk_analysis,
            timing_analysis,
            business_rules,
            context_analysis
        )
        
        # ═══════════════════════════════════════════════════════════════
        # 7. DETERMINE EXECUTION ORDER
        # ═══════════════════════════════════════════════════════════════
        execution_order = self._determine_execution_order(actions)
        
        # ═══════════════════════════════════════════════════════════════
        # 8. HUMAN REVIEW CHECK
        # ═══════════════════════════════════════════════════════════════
        requires_human_review, review_reason = self._check_human_review(
            risk_analysis,
            business_rules,
            attendee_analysis
        )
        
        # ═══════════════════════════════════════════════════════════════
        # 9. MONITORING SETUP
        # ═══════════════════════════════════════════════════════════════
        metrics_to_track, alert_thresholds = self._setup_monitoring(
            booking,
            risk_analysis
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            risk_analysis,
            business_rules,
            attendee_analysis
        )
        
        # Build reasoning
        reasoning = self._build_reasoning(
            attendee_analysis,
            risk_analysis,
            actions
        )
        
        return AgentDecision(
            attendee_analysis=attendee_analysis,
            risk_analysis=risk_analysis,
            timing_analysis=timing_analysis,
            business_rules=business_rules,
            context_analysis=context_analysis,
            actions=actions,
            execution_order=execution_order,
            requires_human_review=requires_human_review,
            human_review_reason=review_reason,
            metrics_to_track=metrics_to_track,
            alert_thresholds=alert_thresholds,
            confidence=confidence,
            decision_timestamp=datetime.utcnow(),
            reasoning=reasoning
        )
    
    # ═════════════════════════════════════════════════════════════════
    # ANALYSIS METHODS
    # ═════════════════════════════════════════════════════════════════
    
    async def _analyze_attendee(self, attendee_info: Dict) -> AttendeeAnalysis:
        """
        Analyze attendee to determine VIP level and preferences
        
        Checks:
        - Booking frequency (VIP if >5/month)
        - No-show rate
        - Response time
        - Engagement score
        """
        email = attendee_info.get("email", "")
        
        # Calculate metrics
        frequency = attendee_info.get("monthly_booking_count", 0)
        no_show_rate = attendee_info.get("no_show_rate", 0.0)
        response_time = attendee_info.get("avg_response_time_hours", 24)
        engagement = attendee_info.get("engagement_score", 0.5)
        
        # Determine VIP level
        if frequency >= 10 and engagement >= 0.9:
            vip_level = VIPLevel.EXECUTIVE
        elif frequency >= 5 and engagement >= 0.8:
            vip_level = VIPLevel.VIP
        elif frequency >= 3 and engagement >= 0.6:
            vip_level = VIPLevel.PREFERRED
        else:
            vip_level = VIPLevel.STANDARD
        
        # Communication preferences
        comm_prefs = attendee_info.get("communication_preferences", ["email"])
        if not comm_prefs:
            # Default based on VIP level
            comm_prefs = ["email", "calendar_invite"]
            if vip_level in [VIPLevel.VIP, VIPLevel.EXECUTIVE]:
                comm_prefs.extend(["sms", "slack"])
        
        return AttendeeAnalysis(
            email=email,
            vip_level=vip_level,
            is_new=attendee_info.get("is_new_contact", frequency == 0),
            booking_frequency=frequency,
            no_show_rate=no_show_rate,
            avg_response_time_hours=response_time,
            preferred_communication=comm_prefs,
            engagement_score=engagement,
            timezone=attendee_info.get("timezone", "UTC"),
            phone=attendee_info.get("phone"),
            company_size=attendee_info.get("company_size"),
            industry=attendee_info.get("industry")
        )
    
    async def _analyze_risk(
        self,
        booking: Dict,
        attendee: AttendeeAnalysis
    ) -> RiskAnalysis:
        """
        Analyze risk factors for booking
        
        Risk factors:
        - High no-show rate
        - Short notice
        - Timezone issues
        - Calendar conflicts
        """
        factors = []
        mitigations = []
        risk_score = 0.0
        
        # Check no-show rate
        if attendee.no_show_rate > self.risk_thresholds["no_show"]:
            factors.append({
                "type": "no_show_history",
                "severity": "high",
                "description": f"High no-show rate: {attendee.no_show_rate:.1%}",
                "impact": 0.3
            })
            risk_score += 0.3
            mitigations.append("Send additional confirmation 24h before")
            mitigations.append("Offer easy rescheduling option")
        
        # Check booking lead time
        start_time = booking.get("start_time", "")
        if start_time:
            from datetime import datetime as dt
            booking_time = dt.fromisoformat(start_time.replace('Z', '+00:00'))
            if booking_time.tzinfo is None:
                booking_time = booking_time.replace(tzinfo=timezone.utc)
            hours_until = (booking_time - dt.now(timezone.utc)).total_seconds() / 3600
            
            if hours_until < self.risk_thresholds["short_notice"]:
                factors.append({
                    "type": "short_notice",
                    "severity": "medium",
                    "description": f"Short notice: {hours_until:.1f} hours",
                    "impact": 0.2
                })
                risk_score += 0.2
                mitigations.append("Send immediate notification")
                mitigations.append("Mark as urgent in calendar")
        
        # Check timezone difference
        # TODO: Calculate actual timezone offset
        
        # Determine risk level
        if risk_score >= 0.6:
            level = RiskLevel.CRITICAL
        elif risk_score >= 0.4:
            level = RiskLevel.HIGH
        elif risk_score >= 0.2:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        return RiskAnalysis(
            level=level,
            score=min(risk_score, 1.0),
            factors=factors,
            mitigations=mitigations
        )
    
    async def _analyze_timing(
        self,
        booking: Dict,
        attendee: AttendeeAnalysis
    ) -> TimingAnalysis:
        """Analyze optimal timing for communications"""
        # TODO: Calculate optimal send time based on timezone
        # For now, use attendee timezone as guide
        
        optimal_time = datetime.utcnow().isoformat()
        
        return TimingAnalysis(
            optimal_send_time=optimal_time,
            timezone_offset_hours=0,  # TODO: Calculate
            expected_response_time_hours=attendee.avg_response_time_hours,
            urgency_level="medium",
            business_hours_aligned=True
        )
    
    async def _check_business_rules(
        self,
        booking: Dict,
        attendee: AttendeeAnalysis
    ) -> List[BusinessRuleCheck]:
        """Check business rules and compliance"""
        rules = []
        
        # Rule: VIP booking notification
        if attendee.vip_level in [VIPLevel.VIP, VIPLevel.EXECUTIVE]:
            rules.append(BusinessRuleCheck(
                rule_name="vip_notification",
                compliant=False,  # Needs action
                severity="info",
                message="VIP booking - notify manager",
                auto_action="notify_manager"
            ))
        
        # Rule: Max attendees
        max_attendees = booking.get("max_attendees", 10)
        actual_attendees = len(booking.get("attendees", []))
        if actual_attendees > max_attendees:
            rules.append(BusinessRuleCheck(
                rule_name="max_attendees",
                compliant=False,
                severity="error",
                message=f"Attendees ({actual_attendees}) exceeds limit ({max_attendees})"
            ))
        
        # Rule: High-value booking follow-up
        estimated_value = booking.get("estimated_value", 0)
        if estimated_value > 1000:
            rules.append(BusinessRuleCheck(
                rule_name="high_value_followup",
                compliant=False,
                severity="info",
                message="High-value booking - create follow-up task",
                auto_action="create_followup_task"
            ))
        
        return rules
    
    async def _analyze_context(
        self,
        booking: Dict,
        context: Dict
    ) -> ContextAnalysis:
        """Analyze full context for booking"""
        return ContextAnalysis(
            calendar_conflicts=context.get("calendar_conflicts", []),
            concurrent_bookings=context.get("concurrent_bookings", 0),
            day_of_week=datetime.utcnow().strftime("%A"),
            time_of_day=datetime.utcnow().strftime("%H:%M"),
            weather=context.get("weather"),
            local_events=context.get("local_events", []),
            market_trends=context.get("market_trends"),
            company_news=context.get("company_news", [])
        )
    
    # ═════════════════════════════════════════════════════════════════
    # DECISION METHODS
    # ═════════════════════════════════════════════════════════════════
    
    async def _decide_actions(
        self,
        booking: Dict,
        attendee: AttendeeAnalysis,
        risk: RiskAnalysis,
        timing: TimingAnalysis,
        rules: List[BusinessRuleCheck],
        context: ContextAnalysis
    ) -> List[ActionDecision]:
        """
        Decide which actions to take based on all analysis
        
        Returns list of ActionDecision objects
        """
        actions = []
        
        # ═══════════════════════════════════════════════════════════════
        # ALWAYS: Create calendar event
        # ═══════════════════════════════════════════════════════════════
        actions.append(ActionDecision(
            tool_name="create_calendar_event",
            parameters={
                "title": booking.get("title", "Meeting"),
                "start_time": booking.get("start_time"),
                "duration_minutes": booking.get("duration_minutes", 30),
                "attendees": booking.get("attendees", []),
                "description": booking.get("description"),
                "location": booking.get("location")
            },
            priority=ToolPriority.CRITICAL,
            execute_immediately=True
        ))
        
        # ═══════════════════════════════════════════════════════════════
        # ALWAYS: Send calendar invite
        # ═══════════════════════════════════════════════════════════════
        for attendee_email in booking.get("attendees", []):
            actions.append(ActionDecision(
                tool_name="send_calendar_invite",
                parameters={
                    "attendee": attendee_email,
                    "title": booking.get("title"),
                    "start_time": booking.get("start_time"),
                    "duration_minutes": booking.get("duration_minutes", 30),
                    "location": booking.get("location")
                },
                priority=ToolPriority.CRITICAL,
                execute_immediately=True,
                depends_on=["create_calendar_event"]
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # VIP: Additional notifications
        # ═══════════════════════════════════════════════════════════════
        if attendee.vip_level in [VIPLevel.VIP, VIPLevel.EXECUTIVE]:
            # Send email confirmation
            actions.append(ActionDecision(
                tool_name="send_email",
                parameters={
                    "to": attendee.email,
                    "subject": f"Meeting Confirmed: {booking.get('title')}",
                    "template": "vip_confirmation" if attendee.vip_level == VIPLevel.VIP else "executive_confirmation",
                    "body": self._build_vip_email_body(booking, attendee)
                },
                priority=ToolPriority.HIGH,
                execute_immediately=True
            ))
            
            # Post to Slack for visibility
            actions.append(ActionDecision(
                tool_name="post_to_slack",
                parameters={
                    "channel": "#vip-bookings",
                    "message": f"🔥 New {attendee.vip_level.value.upper()} booking: {booking.get('title')} with {attendee.email}"
                },
                priority=ToolPriority.MEDIUM,
                execute_immediately=False
            ))
            
            # Create CRM task for follow-up
            actions.append(ActionDecision(
                tool_name="create_task",
                parameters={
                    "title": f"Follow up after {booking.get('title')}",
                    "due_date": self._calculate_followup_time(booking.get("start_time")),
                    "owner": "account_manager@company.com",
                    "priority": "high",
                    "related_to": attendee.email,
                    "task_type": "vip_followup"
                },
                priority=ToolPriority.HIGH,
                execute_immediately=False
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # HIGH RISK: Additional confirmations
        # ═══════════════════════════════════════════════════════════════
        if risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            # Send SMS reminder if phone available
            if "sms" in attendee.preferred_communication and attendee.phone:
                actions.append(ActionDecision(
                    tool_name="send_sms",
                    parameters={
                        "to": attendee.phone,
                        "message": f"Reminder: {booking.get('title')} on {booking.get('start_time')}"
                    },
                    priority=ToolPriority.HIGH,
                    execute_immediately=False,
                    condition="24_hours_before_meeting"
                ))
            
            # Send additional confirmation email
            actions.append(ActionDecision(
                tool_name="send_email",
                parameters={
                    "to": attendee.email,
                    "subject": "Please Confirm Your Attendance",
                    "template": "confirmation_request",
                    "body": f"Please confirm your attendance for {booking.get('title')}"
                },
                priority=ToolPriority.HIGH,
                execute_immediately=False,
                condition="48_hours_before_meeting"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # BUSINESS RULES: Auto-actions
        # ═══════════════════════════════════════════════════════════════
        for rule in rules:
            if rule.auto_action == "notify_manager":
                actions.append(ActionDecision(
                    tool_name="send_email",
                    parameters={
                        "to": "manager@company.com",
                        "subject": f"VIP Booking Alert: {attendee.email}",
                        "body": f"New VIP booking requires attention: {booking.get('title')}"
                    },
                    priority=ToolPriority.HIGH,
                    execute_immediately=True
                ))
            
            elif rule.auto_action == "create_followup_task":
                actions.append(ActionDecision(
                    tool_name="create_task",
                    parameters={
                        "title": f"High-value booking follow-up: {booking.get('title')}",
                        "due_date": self._calculate_followup_time(booking.get("start_time")),
                        "owner": "sales@company.com",
                        "priority": "high",
                        "related_to": booking.get("id")
                    },
                    priority=ToolPriority.MEDIUM,
                    execute_immediately=False
                ))
        
        # ═══════════════════════════════════════════════════════════════
        # ANALYTICS: Track metrics
        # ═══════════════════════════════════════════════════════════════
        actions.append(ActionDecision(
            tool_name="analyze_booking_pattern",
            parameters={
                "user_id": booking.get("user_id"),
                "timeframe_days": 30
            },
            priority=ToolPriority.LOW,
            execute_immediately=False
        ))
        
        return actions
    
    def _determine_execution_order(self, actions: List[ActionDecision]) -> List[str]:
        """Determine optimal execution order for actions"""
        ordered: List[str] = []
        action_map = {f"action_{i}": action for i, action in enumerate(actions)}

        tool_name_to_action_ids: Dict[str, List[str]] = {}
        for action_id, action in action_map.items():
            tool_name_to_action_ids.setdefault(action.tool_name, []).append(action_id)

        priority_rank = {
            ToolPriority.CRITICAL: 0,
            ToolPriority.HIGH: 1,
            ToolPriority.MEDIUM: 2,
            ToolPriority.LOW: 3,
        }

        candidate_ids = sorted(
            action_map.keys(),
            key=lambda action_id: (
                priority_rank.get(action_map[action_id].priority, 99),
                0 if action_map[action_id].execute_immediately else 1,
                int(action_id.split("_")[1]),
            ),
        )

        def dependencies_satisfied(action: ActionDecision) -> bool:
            if not action.depends_on:
                return True

            resolved_dependency_ids: List[str] = []
            for dependency in action.depends_on:
                if dependency in action_map:
                    resolved_dependency_ids.append(dependency)
                elif dependency in tool_name_to_action_ids:
                    resolved_dependency_ids.extend(tool_name_to_action_ids[dependency])
                else:
                    return False

            return all(dep_id in ordered for dep_id in resolved_dependency_ids)

        while len(ordered) < len(actions):
            progress = False

            for action_id in candidate_ids:
                if action_id in ordered:
                    continue
                action = action_map[action_id]
                if dependencies_satisfied(action):
                    ordered.append(action_id)
                    progress = True

            if not progress:
                # Break dependency cycles and keep deterministic ordering.
                for action_id in candidate_ids:
                    if action_id not in ordered:
                        ordered.append(action_id)
                break

        return ordered
    
    def _check_human_review(
        self,
        risk: RiskAnalysis,
        rules: List[BusinessRuleCheck],
        attendee: AttendeeAnalysis
    ) -> tuple:
        """Check if human review is required"""
        requires_review = False
        reason = None
        
        # Critical risk requires review
        if risk.level == RiskLevel.CRITICAL:
            requires_review = True
            reason = f"Critical risk level: {len(risk.factors)} risk factors"
        
        # Business rule violations
        violations = [r for r in rules if r.severity == "error" and not r.compliant]
        if violations:
            requires_review = True
            reason = f"Business rule violations: {len(violations)}"
        
        # Executive VIP always gets review option
        if attendee.vip_level == VIPLevel.EXECUTIVE:
            requires_review = True
            reason = "Executive-level booking"
        
        return requires_review, reason
    
    def _setup_monitoring(
        self,
        booking: Dict,
        risk: RiskAnalysis
    ) -> tuple:
        """Setup what metrics to track and alert thresholds"""
        metrics = [
            "booking_confirmed",
            "attendee_response",
            "calendar_sync"
        ]
        
        thresholds = {
            "no_response_hours": 24,
            "conflict_detected": 1.0
        }
        
        # High risk bookings need more monitoring
        if risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            metrics.extend([
                "confirmation_received",
                "reminder_sent",
                "no_show_risk_score"
            ])
            thresholds["no_response_hours"] = 12  # Faster alerts
        
        return metrics, thresholds
    
    def _calculate_confidence(
        self,
        risk: RiskAnalysis,
        rules: List[BusinessRuleCheck],
        attendee: AttendeeAnalysis
    ) -> DecisionConfidence:
        """Calculate confidence in the decision"""
        score = 1.0
        
        # Reduce confidence based on risk
        score -= risk.score * 0.3
        
        # Reduce confidence for rule violations
        violations = len([r for r in rules if r.severity == "error"])
        score -= violations * 0.2
        
        # Reduce confidence for unknown/new attendees
        if attendee.is_new:
            score -= 0.1
        
        # Map to confidence level
        if score >= 0.9:
            return DecisionConfidence.CERTAIN
        elif score >= 0.75:
            return DecisionConfidence.HIGH
        elif score >= 0.5:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW
    
    def _build_reasoning(
        self,
        attendee: AttendeeAnalysis,
        risk: RiskAnalysis,
        actions: List[ActionDecision]
    ) -> str:
        """Build human-readable reasoning for the decision"""
        reasoning_parts = [
            f"Attendee Analysis: {attendee.vip_level.value.upper()} level",
            f"  - Booking frequency: {attendee.booking_frequency}/month",
            f"  - No-show rate: {attendee.no_show_rate:.1%}",
            f"  - Engagement: {attendee.engagement_score:.1%}",
            "",
            f"Risk Assessment: {risk.level.value.upper()}",
            f"  - Risk score: {risk.score:.2f}",
            f"  - Factors: {len(risk.factors)}",
            "",
            f"Actions Planned: {len(actions)}",
            f"  - Critical: {len([a for a in actions if a.priority == ToolPriority.CRITICAL])}",
            f"  - High: {len([a for a in actions if a.priority == ToolPriority.HIGH])}",
            f"  - Medium: {len([a for a in actions if a.priority == ToolPriority.MEDIUM])}",
        ]
        
        return "\n".join(reasoning_parts)
    
    # ═════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═════════════════════════════════════════════════════════════════
    
    def _build_vip_email_body(self, booking: Dict, attendee: AttendeeAnalysis) -> str:
        """Build personalized email body for VIP"""
        return f"""
Dear {attendee.email},

Your meeting "{booking.get('title')}" has been confirmed.

Time: {booking.get('start_time')}
Duration: {booking.get('duration_minutes')} minutes
Location: {booking.get('location', 'TBD')}

As one of our valued {attendee.vip_level.value} members, we've reserved your preferred time slot.

If you need to reschedule, please contact us directly.

Best regards,
GraftAI Team
        """.strip()
    
    def _calculate_followup_time(self, start_time: str) -> str:
        """Calculate when to schedule follow-up task"""
        from datetime import datetime as dt, timedelta
        
        if start_time:
            meeting_time = dt.fromisoformat(start_time.replace('Z', '+00:00'))
            followup_time = meeting_time + timedelta(hours=24)
            return followup_time.isoformat()
        
        return (dt.utcnow() + timedelta(days=1)).isoformat()


# Factory function
async def create_decision_engine() -> DecisionEngine:
    """Create a decision engine instance"""
    return DecisionEngine()


# Convenience function for quick analysis
async def analyze_booking(
    booking: Dict[str, Any],
    attendee_info: Dict[str, Any],
    context: Dict[str, Any]
) -> AgentDecision:
    """Quick analysis of a booking"""
    engine = DecisionEngine()
    return await engine.analyze_and_decide(booking, attendee_info, context)
