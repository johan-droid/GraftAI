"""
Booking Automation Service

Complete workflow implementation:

User Creates Booking → AI Agent Triggered → Perception → Reasoning →
Action → Reflection → Results Stored → User Sees Results

This file demonstrates the full agent lifecycle in practice.
"""
import asyncio
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.decision_engine import AgentDecision, create_decision_engine
from backend.ai.memory.multi_layer_memory import create_memory_manager
from backend.ai.memory.vector_store import get_vector_store
from backend.ai.monitoring import (
    get_agent_logger,
    get_agent_metrics,
    log_agent_decision,
    log_automation_complete,
    log_phase_execution,
)
from backend.ai.orchestrator import get_agent_controller
from backend.ai.tools import (
    check_business_rules,
    create_calendar_event,
    create_task,
    get_attendee_info,
    send_email,
)
from backend.models.tables import AIAutomationTable, BookingTable
from backend.utils.db import get_async_session_maker
from backend.utils.logger import get_logger

logger = get_logger(__name__)
agent_logger = get_agent_logger()

def sanitize_ai_memory(payload: dict, max_kb: int=10) -> dict:
    """Prevent DB bloat by truncating oversized AI result payloads."""
    if not isinstance(payload, dict):
        return {"error": "Invalid payload type for sanitization"}
    try:
        json_str = json.dumps(payload, default=str)
        size_kb = len(json_str.encode("utf-8")) / 1024
        if size_kb > max_kb:
            core_decisions = payload.get("agent_decisions") or payload.get("decision") or {}
            return {"status": "truncated_due_to_size", "original_size_kb": round(size_kb, 2), "core_decisions": core_decisions, "error": "Full external results stripped to prevent DB bloat."}
        return payload
    except Exception as e:
        logger.warning("Failed to sanitize AI memory payload: %s", e)
        return {"error": "Failed to serialize AI memory payload"}

@dataclass
class AutomationResult:
    """Result of booking automation"""
    booking_id: str
    automation_status: str
    actions_executed: list[dict[str, Any]]
    agent_decisions: dict[str, Any]
    external_results: dict[str, Any]
    risk_assessment: str
    decision_score: int
    execution_time_ms: float
    timestamp: str

class BookingAutomationService:
    """
    Service that orchestrates the complete booking automation workflow
    as shown in the diagram.
    """

    def __init__(self):
        self.decision_engine = None
        self.memory_manager = None
        self.vector_store = None

    async def _remember_booking(self, booking_id: str, attendee_email: str, organizer_id: str, action_results: list[dict[str, Any]], success: bool, decision_score: int):
        """Persist booking outcome into long-term memory."""
        if not self.memory_manager:
            return
        episode = {"key": f"booking_{booking_id}", "type": "booking_outcome", "description": f"Booking {booking_id} for {attendee_email} was {('successful' if success else 'partially successful' if any(r.get('success') for r in action_results) else 'unsuccessful')}.", "outcome": "success" if success else "partial" if any(r.get("success") for r in action_results) else "failure", "result": {"booking_id": booking_id, "attendee_email": attendee_email, "organizer_id": organizer_id, "success": success, "actions": action_results, "decision_score": decision_score}, "context": {"attendee_email": attendee_email, "organizer_id": organizer_id, "booking_id": booking_id, "timestamp": datetime.now(UTC).isoformat()}, "timestamp": datetime.now(UTC).isoformat(), "importance": 0.8 if success else 0.5, "tags": ["booking", "automation", "outcome"]}
        await self.memory_manager.long_term.store_episode(episode)

    async def _recall_similar_bookings(self, attendee_email: str, organizer_id: str) -> list[dict[str, Any]]:
        """Retrieve similar past booking experiences from long-term memory."""
        if not self.memory_manager:
            return []
        query = f"Booking for {attendee_email} with {organizer_id}"
        results = await self.memory_manager.long_term.retrieve_similar_episodes(query, 5)
        filtered = []
        for item in results:
            if not isinstance(item, dict):
                filtered.append(item)
                continue
            context = item.get("context", {})
            if context.get("organizer_id") == organizer_id or context.get("attendee_email") == attendee_email:
                filtered.append(item)
        return filtered[:5]

    async def process_booking_created(self, booking_id: str, user_id: str, trigger_source: str="scheduler") -> AutomationResult:
        """Transaction wrapper for booking automation."""
        session_factory = get_async_session_maker()
        async with session_factory() as db:
            try:
                async with db.begin():
                    try:
                        booking_lookup = await db.execute(select(BookingTable).where(BookingTable.id == booking_id).with_for_update(nowait=True))
                    except Exception as e:
                        logger.warning("Booking %s locked by another worker: %s", booking_id, e)
                        return AutomationResult(booking_id=booking_id, automation_status="failed", actions_executed=[], agent_decisions={"error": "locked"}, external_results={}, risk_assessment="unknown", decision_score=0, execution_time_ms=0, timestamp=datetime.now(UTC).isoformat())
                    if not booking_lookup.scalar_one_or_none():
                        return AutomationResult(booking_id=booking_id, automation_status="failed", actions_executed=[], agent_decisions={"error": "not found"}, external_results={}, risk_assessment="unknown", decision_score=0, execution_time_ms=0, timestamp=datetime.now(UTC).isoformat())
                    return await self._execute_booking_automation_core(db, booking_id, user_id, trigger_source)
            except Exception as e:
                logger.error("Booking %s failed during automation: %s. Rolled back.", booking_id, e, exc_info=True)
                return AutomationResult(booking_id=booking_id, automation_status="failed", actions_executed=[], agent_decisions={"error": str(e)}, external_results={}, risk_assessment="unknown", decision_score=0, execution_time_ms=0, timestamp=datetime.now(UTC).isoformat())

    async def _execute_booking_automation_core(self, db, booking_id: str, user_id: str, trigger_source: str="scheduler") -> AutomationResult:
        """
        Main entry point - triggered when user creates booking

        Flow:
        1. AI Agent Triggered (Event: BOOKING_CREATED)
        2. Agent Perception Phase
        3. LLaMA Reasoning
        4. Agent Action Execution Phase
        5. Agent Reflection Phase
        6. Results Stored in Database
        7. Return results to user
        """
        start_time = datetime.now(UTC)
        metrics = get_agent_metrics()
        metrics.record_automation_start(booking_id)
        logger.info("🚀 Booking Automation Started: %s", booking_id)
        try:
            logger.info("[%s] Step 1: AI Agent Triggered", booking_id)
            await get_agent_controller()
            self.decision_engine = await create_decision_engine()
            self.vector_store = await get_vector_store()
            self.memory_manager = await create_memory_manager(user_id=user_id, vector_store=self.vector_store)
            logger.info("[%s] Step 2: Agent Perception Phase", booking_id)
            phase_start = time.time()
            perception_data = await self._perception_phase(db, booking_id, user_id)
            phase_duration = (time.time() - phase_start) * 1000
            metrics.record_agent_complete(tracking_id=metrics.record_agent_start("booking_agent", "perception"), agent_type="booking_agent", phase="perception", status="success")
            log_phase_execution(booking_id, "perception", phase_duration, True)
            logger.info("[%s] Perception complete:", booking_id)
            logger.info("  - Attendee: %s", perception_data["attendee_email"])
            logger.info("  - Past bookings: %s", perception_data["attendee_info"].get("past_bookings", 0))
            logger.info("  - No-show rate: %s", perception_data["attendee_info"].get("no_show_rate", 0))
            logger.info("[%s] Step 3: LLaMA Reasoning", booking_id)
            booking_data = {"id": booking_id, "title": perception_data["booking_title"], "start_time": perception_data["start_time"], "duration_minutes": perception_data["duration_minutes"], "attendees": [perception_data["attendee_email"]], "organizer": user_id, "type": perception_data.get("booking_type", "consultation"), "created_at": datetime.now(UTC).isoformat()}
            decision_start = time.time()
            decision = await self.decision_engine.analyze_and_decide(booking=booking_data, attendee_info=perception_data["attendee_info"], context=perception_data["context"])
            decision_latency = time.time() - decision_start
            metrics.record_decision_latency(decision_type=decision.risk_analysis.level.value, latency_seconds=decision_latency)
            log_agent_decision(booking_id=booking_id, decision=f"risk_{decision.risk_analysis.level.value}", confidence=decision.confidence.value if hasattr(decision.confidence, "value") else 0.8, reasoning=decision.reasoning, risk_level=decision.risk_analysis.level.value, actions=[{"tool_name": a.tool_name, "priority": a.priority.name} for a in decision.actions], latency_ms=decision_latency * 1000)
            logger.info("[%s] Reasoning complete:", booking_id)
            logger.info("  - VIP Level: %s", decision.attendee_analysis.vip_level.value)
            logger.info("  - Risk: %s", decision.risk_analysis.level.value)
            logger.info("  - Actions planned: %s", len(decision.actions))
            logger.info("  - Human review needed: %s", decision.requires_human_review)
            logger.info("[%s] Step 4: Action Execution Phase", booking_id)
            phase_start = time.time()
            action_results = await self._action_phase(booking_id=booking_id, decision=decision, perception_data=perception_data, db=db)
            phase_duration = (time.time() - phase_start) * 1000
            metrics.record_agent_complete(tracking_id=metrics.record_agent_start("booking_agent", "action"), agent_type="booking_agent", phase="action", status="success" if all(r.get("success") for r in action_results) else "partial")
            log_phase_execution(booking_id=booking_id, phase="action", duration_ms=phase_duration, success=all(r.get("success") for r in action_results))
            logger.info("[%s] Actions executed: %s", booking_id, len(action_results))
            for result in action_results:
                status = "✅" if result.get("success") else "❌"
                logger.info("  %s %s: %s", status, result.get("tool_name"), result.get("status", "unknown"))
            logger.info("[%s] Step 5: Reflection Phase", booking_id)
            phase_start = time.time()
            reflection_data = await self._reflection_phase(booking_id=booking_id, decision=decision, action_results=action_results, perception_data=perception_data)
            phase_duration = (time.time() - phase_start) * 1000
            metrics.record_agent_complete(tracking_id=metrics.record_agent_start("booking_agent", "reflection"), agent_type="booking_agent", phase="reflection", status="success")
            log_phase_execution(booking_id, "reflection", phase_duration, True)
            logger.info("[%s] Reflection:", booking_id)
            logger.info("  - Overall: %s", reflection_data["assessment"])
            logger.info("  - Learnings: %s", len(reflection_data["learnings"]))
            logger.info("[%s] Step 6: Storing Results", booking_id)
            external_results = {"email_id": next((r.get("email_id") for r in action_results if r.get("tool_name") == "send_email"), None), "calendar_id": next((r.get("event_id") for r in action_results if r.get("tool_name") == "create_calendar_event"), None), "task_id": next((r.get("task_id") for r in action_results if r.get("tool_name") == "create_task"), None)}
            execution_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            await self._store_results_with_transaction(db=db, booking_id=booking_id, user_id=user_id, decision=decision, action_results=action_results, external_results=sanitize_ai_memory(external_results), reflection_data=reflection_data, execution_time_ms=execution_time, fallback_mode=None, trigger_source=trigger_source)
            decision_score = self._calculate_decision_score(decision, action_results)
            success = all(r.get("success") for r in action_results)
            status = "completed" if success else "partial"
            metrics.record_automation_complete(booking_id=booking_id, status=status, risk_level=decision.risk_analysis.level.value, vip_level=decision.attendee_analysis.vip_level.value, decision_score=decision_score, booking_value=perception_data.get("estimated_value", 0))
            log_automation_complete(booking_id=booking_id, status=status, decision_score=decision_score, risk_assessment=decision.risk_analysis.level.value, actions_executed=len(action_results), execution_time_ms=execution_time)
            result = AutomationResult(booking_id=booking_id, automation_status="completed" if all(r.get("success") for r in action_results) else "partial", actions_executed=action_results, agent_decisions={"actions": [a.tool_name for a in decision.actions], "reasoning": decision.reasoning, "risk_assessment": decision.risk_analysis.level.value, "confidence": decision.confidence.name}, external_results=external_results, risk_assessment=decision.risk_analysis.level.value, decision_score=decision_score, execution_time_ms=execution_time, timestamp=datetime.now(UTC).isoformat())
            logger.info("✅ Booking Automation Complete: %s", booking_id)
            logger.info("  - Status: %s", result.automation_status)
            logger.info("  - Score: %s/100", result.decision_score)
            logger.info("  - Time: %sms", execution_time)
            return result
        except Exception as e:
            logger.exception("❌ Booking Automation Failed: %s - %s", booking_id, e)
            metrics.record_error(error_type="automation_failure", component="booking_automation")
            metrics.record_automation_complete(booking_id=booking_id, status="failed", risk_level="unknown", vip_level="unknown", decision_score=0)
            log_automation_complete(booking_id=booking_id, status="failed", decision_score=0, risk_assessment="unknown", actions_executed=0, execution_time_ms=(datetime.now(UTC) - start_time).total_seconds() * 1000, error=str(e))
            raise

    async def _perception_phase(self, db, booking_id: str, user_id: str) -> dict[str, Any]:
        """
        PERCEPTION PHASE

        Load:
        - Booking data
        - Attendee profile
        - Past interactions
        - User preferences
        - Calendar availability
        - Business rules
        """
        if True:
            booking_result = await db.execute(select(BookingTable).where(BookingTable.id == booking_id))
            booking = booking_result.scalar_one_or_none()
            if booking:
                metadata = booking.metadata_payload or {}
                attendees = metadata.get("attendees") or []
                attendee_email = attendees[0] if attendees else booking.email
                booking_data = {"id": booking.id, "title": metadata.get("title") or f"Booking with {booking.full_name}", "start_time": booking.start_time.isoformat(), "duration_minutes": max(int((booking.end_time - booking.start_time).total_seconds() / 60), 1), "attendee_email": attendee_email, "booking_type": metadata.get("meeting_type", "consultation"), "organizer_id": booking.user_id, "estimated_value": metadata.get("estimated_value")}
            else:
                booking_data = {"id": booking_id, "title": "Consultation with John Smith", "start_time": "2024-01-16T14:00:00", "duration_minutes": 30, "attendee_email": "john.smith@example.com", "booking_type": "consultation", "organizer_id": user_id}
            attendee_info = await get_attendee_info(email=booking_data["attendee_email"])
            if not attendee_info.get("success"):
                attendee_profile = {"email": booking_data["attendee_email"], "is_new": True, "past_bookings": 0, "no_show_rate": 0.0, "engagement_score": 0.5, "preferred_communication": ["email"], "avg_response_time_hours": 24, "timezone": "America/New_York"}
            else:
                attendee_profile = attendee_info.get("attendee", {})
                attendee_profile["is_new"] = False
            recent_interactions = await self.memory_manager.retrieve_by_context(query=f"interactions with {booking_data['attendee_email']}", n_results=5)
            similar_bookings = await self._recall_similar_bookings(booking_data["attendee_email"], booking_data["organizer_id"])
            user_prefs = self.memory_manager.medium_term.user_preferences
            calendar_available = True
            rules_check = await check_business_rules(booking={"duration_minutes": booking_data["duration_minutes"], "attendee_count": 1, "start_time": booking_data["start_time"]})
            context = {"booking_type": booking_data["booking_type"], "lead_time_hours": self._calculate_lead_time(booking_data["start_time"]), "calendar_available": calendar_available, "business_rules_compliant": rules_check.get("is_valid", True), "recent_interactions": recent_interactions, "similar_bookings": similar_bookings, "user_preferences": user_prefs}
            await self.memory_manager.store(key="perception_data", value={"booking_id": booking_id, "attendee_email": booking_data["attendee_email"], "context": context}, layer=self.memory_manager.__class__.__name__, priority=self.memory_manager.__class__.__name__, source="perception_phase")
            return {"booking_id": booking_id, "booking_title": booking_data["title"], "start_time": booking_data["start_time"], "duration_minutes": booking_data["duration_minutes"], "attendee_email": booking_data["attendee_email"], "booking_type": booking_data["booking_type"], "attendee_info": attendee_profile, "context": context}
        return None

    async def _action_phase(self, booking_id: str, decision: AgentDecision, perception_data: dict[str, Any], db: AsyncSession) -> list[dict[str, Any]]:
        """
        ACTION EXECUTION PHASE

        Execute decided tools in order:
        1. Send Email (HIGH PRIORITY - immediate)
        2. Create Calendar Event (MEDIUM)
        3. Create Reminder Task (MEDIUM)
        4. Check CRM (LOW)
        """
        results = []
        for action_id in decision.execution_order:
            action_index = int(action_id.split("_")[1])
            action = decision.actions[action_index]
            logger.info("  Executing: %s (Priority: %s)", action.tool_name, action.priority.value)
            try:
                if action.tool_name == "send_email":
                    result = await send_email(**action.parameters)
                    results.append({"tool_name": "send_email", "success": result.get("success", False), "email_id": result.get("email_id"), "status": "sent" if result.get("success") else "failed", "timestamp": datetime.now(UTC).isoformat()})
                    if not result.get("success", False):
                        msg = f"Critical action send_email failed: {result.get('error') or result.get('status')}"
                        raise RuntimeError(msg)
                elif action.tool_name == "create_calendar_event":
                    result = await create_calendar_event(**action.parameters, db=db)
                    results.append({"tool_name": "create_calendar_event", "success": result.get("success", False), "event_id": result.get("event_id"), "status": "created" if result.get("success") else "failed", "timestamp": datetime.now(UTC).isoformat()})
                    if not result.get("success", False):
                        msg = f"Critical action create_calendar_event failed: {result.get('error') or result.get('status')}"
                        raise RuntimeError(msg)
                elif action.tool_name == "create_task":
                    result = await create_task(**action.parameters)
                    results.append({"tool_name": "create_task", "success": result.get("success", False), "task_id": result.get("task_id"), "status": "created" if result.get("success") else "failed", "timestamp": datetime.now(UTC).isoformat()})
                await self.memory_manager.context.store_phase_result(phase="action", key=f"tool_{action.tool_name}", value=result)
            except Exception as e:
                logger.exception("Tool execution failed: %s - %s", action.tool_name, e)
                results.append({"tool_name": action.tool_name, "success": False, "error": str(e), "timestamp": datetime.now(UTC).isoformat()})
        return results

    async def _reflection_phase(self, booking_id: str, decision: AgentDecision, action_results: list[dict[str, Any]], perception_data: dict[str, Any]) -> dict[str, Any]:
        """
        REFLECTION PHASE

        - Assess outcomes
        - Learn patterns
        - Update memory
        - Store for future
        """
        all_success = all(r.get("success") for r in action_results)
        partial_success = any(r.get("success") for r in action_results)
        if all_success:
            assessment = "Optimal"
        elif partial_success:
            assessment = "Partial"
        else:
            assessment = "Failed"
        learnings = []
        if perception_data["attendee_info"].get("no_show_rate", 0) < 0.1:
            learnings.append({"type": "attendee_reliability", "pattern": "Low no-show rate indicates reliable attendee", "confidence": 0.9})
        email_result = next((r for r in action_results if r.get("tool_name") == "send_email"), None)
        if email_result and email_result.get("success"):
            learnings.append({"type": "template_effectiveness", "pattern": "Personalized confirmation email works well", "confidence": 0.85})
        for learning in learnings:
            self.memory_manager.medium_term.add_pattern(pattern_type=learning["type"], pattern_data=learning, outcome="success" if all_success else "partial")
        if decision.confidence.value >= 0.8 and all_success:
            await self.memory_manager.long_term.store_episode({"type": "successful_booking", "booking_id": booking_id, "attendee": perception_data["attendee_email"], "strategy": "standard_confirmation_flow", "outcome": "success", "confidence": decision.confidence.value, "timestamp": datetime.now(UTC).isoformat(), "importance": 0.8})
        await self.memory_manager.context.end_workflow()
        await self._remember_booking(booking_id=booking_id, attendee_email=perception_data["attendee_email"], organizer_id=perception_data["organizer_id"], action_results=action_results, success=all_success, decision_score=decision.confidence.value if hasattr(decision, "confidence") else 0)
        return {"assessment": assessment, "all_success": all_success, "partial_success": partial_success}

    async def _store_results_with_transaction(self, db: AsyncSession, booking_id: str, user_id: str, decision: AgentDecision, action_results: list[dict[str, Any]], external_results: dict[str, Any], reflection_data: dict[str, Any], execution_time_ms: float, fallback_mode: str | None=None, trigger_source: str="api"):
        """
        Store automation results to database within a transaction.

        Args:
            db: Database session (within transaction)
            booking_id: Booking ID
            user_id: User ID
            decision: Agent decision
            action_results: Results from action execution
            external_results: Results from external APIs
            reflection_data: Reflection phase results
            execution_time_ms: Total execution time
            fallback_mode: Fallback mode if used
        """
        try:
            result = await db.execute(select(BookingTable).where(BookingTable.id == booking_id, not BookingTable.is_deleted).with_for_update())
            booking = result.scalar_one_or_none()
            if booking:
                booking.automation_status = "completed" if all(r.get("success") for r in action_results) else "partial"
                booking.automation_run_at = datetime.now(UTC)
                booking.decision_score = self._calculate_decision_score(decision, action_results)
                booking.risk_level = decision.risk_analysis.level.value
                db.add(booking)
            automation_status = "completed" if all(r.get("success") for r in action_results) else "partial"
            decision_score = self._calculate_decision_score(decision, action_results)
            now = datetime.now(UTC)
            automation_lookup = await db.execute(select(AIAutomationTable).where(AIAutomationTable.booking_id == booking_id, AIAutomationTable.user_id == user_id).order_by(AIAutomationTable.created_at.desc()))
            automation_record = automation_lookup.scalars().first()
            agent_decisions = {"actions": [a.tool_name for a in decision.actions], "reasoning": decision.reasoning, "confidence": getattr(decision.confidence, "name", str(decision.confidence)), "risk_assessment": decision.risk_analysis.level.value, "reflection": reflection_data}
            if automation_record is None:
                automation_record = AIAutomationTable(booking_id=booking_id, user_id=user_id, status=automation_status, decision_score=decision_score, risk_assessment=decision.risk_analysis.level.value, agent_decisions=agent_decisions, actions_executed=action_results, external_results=external_results, execution_time_ms=execution_time_ms, started_at=now, completed_at=now, fallback_mode=fallback_mode, trigger_source=trigger_source, error_message=None)
                db.add(automation_record)
            else:
                automation_record.status = automation_status
                automation_record.decision_score = decision_score
                automation_record.risk_assessment = decision.risk_analysis.level.value
                automation_record.agent_decisions = agent_decisions
                automation_record.actions_executed = action_results
                automation_record.external_results = external_results
                automation_record.execution_time_ms = execution_time_ms
                automation_record.completed_at = now
                automation_record.fallback_mode = fallback_mode
                automation_record.trigger_source = trigger_source
                automation_record.error_message = None
                if automation_record.started_at is None:
                    automation_record.started_at = now
            await db.flush()
            logger.info("[Booking:%s] Results stored in transaction (status: %s)", booking_id, automation_record.status)
            return automation_record.id
        except IntegrityError as e:
            logger.exception("[Booking:%s] Integrity error: %s", booking_id, e)
            raise
        except Exception as e:
            logger.exception("[Booking:%s] Failed to store results: %s", booking_id, e)
            raise

    async def _store_results(self, booking_id: str, user_id: str, decision: AgentDecision, action_results: list[dict[str, Any]], external_results: dict[str, Any], reflection_data: dict[str, Any], execution_time_ms: float, fallback_mode: str | None=None, trigger_source: str="api"):
        """
        Store automation results to database with transaction safety.

        Legacy method - now wraps _store_results_with_transaction in a transaction.
        """
        session_factory = get_async_session_maker()
        async with session_factory() as db, db.begin():
            return await self._store_results_with_transaction(db=db, booking_id=booking_id, user_id=user_id, decision=decision, action_results=action_results, external_results=external_results, reflection_data=reflection_data, execution_time_ms=execution_time_ms, fallback_mode=fallback_mode, trigger_source=trigger_source)

    def _calculate_lead_time(self, start_time: str) -> float:
        """Calculate hours until booking"""
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        return (start - datetime.now(UTC)).total_seconds() / 3600

    def _calculate_decision_score(self, decision: AgentDecision, action_results: list[dict[str, Any]]) -> int:
        """Calculate decision quality score (0-100)"""
        score = 0
        confidence_scores = {"LOW": 50, "MEDIUM": 70, "HIGH": 85, "CERTAIN": 95}
        score += confidence_scores.get(decision.confidence.name, 50)
        if decision.risk_analysis.level.value == "low":
            score += 5
        elif decision.risk_analysis.level.value == "high":
            score -= 10
        success_rate = sum(1 for r in action_results if r.get("success")) / len(action_results) if action_results else 0
        score += int(success_rate * 10)
        return max(0, min(100, score))

def on_booking_created(booking_id: str, user_id: str) -> AutomationResult:
    """
    Webhook handler - called when user creates booking in scheduler

    This is the entry point that triggers the entire workflow.
    """
    service = BookingAutomationService()
    return asyncio.run(service.process_booking_created(booking_id=booking_id, user_id=user_id, trigger_source="scheduler_webhook"))

async def api_trigger_booking_automation(booking_id: str, user_id: str) -> dict[str, Any]:
    """
    API endpoint to manually trigger booking automation

    POST /api/bookings/{booking_id}/automate
    """
    service = BookingAutomationService()
    result = await service.process_booking_created(booking_id=booking_id, user_id=user_id)
    return {"booking_id": result.booking_id, "status": result.automation_status, "decision_score": result.decision_score, "risk_assessment": result.risk_assessment, "actions": result.agent_decisions.get("actions", []), "external_ids": result.external_results, "execution_time_ms": result.execution_time_ms, "timestamp": result.timestamp}
