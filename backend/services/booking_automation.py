"""
Booking Automation Service

Complete workflow implementation:

User Creates Booking → AI Agent Triggered → Perception → Reasoning → 
Action → Reflection → Results Stored → User Sees Results

This file demonstrates the full agent lifecycle in practice.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import time

from backend.utils.logger import get_logger
from backend.ai.orchestrator import get_agent_controller, AgentType, AgentRequest
from backend.ai.decision_engine import create_decision_engine, AgentDecision
from backend.ai.memory.multi_layer_memory import create_memory_manager, AgentMemoryContext
from backend.ai.memory.vector_store import get_vector_store
from backend.ai.tools import (
    send_email,
    create_calendar_event,
    create_task,
    get_attendee_info,
    check_business_rules,
    analyze_booking_pattern
)
from backend.ai.monitoring import (
    get_agent_metrics,
    get_agent_logger,
    log_agent_decision,
    log_automation_start,
    log_automation_complete,
    log_phase_execution,
    log_tool_execution,
    measure_decision_latency,
    measure_agent_phase,
    measure_tool_execution,
    measure_memory_operation
)
from backend.utils.db import get_db

logger = get_logger(__name__)
agent_logger = get_agent_logger()


@dataclass
class AutomationResult:
    """Result of booking automation"""
    booking_id: str
    automation_status: str  # completed, partial, failed
    actions_executed: List[Dict[str, Any]]
    agent_decisions: Dict[str, Any]
    external_results: Dict[str, Any]
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
    
    async def _remember_booking(
        self,
        booking_id: str,
        attendee_email: str,
        organizer_id: str,
        action_results: List[Dict[str, Any]],
        success: bool,
        decision_score: int
    ):
        """Persist booking outcome into long-term memory."""
        if not self.memory_manager:
            return

        episode = {
            "key": f"booking_{booking_id}",
            "type": "booking_outcome",
            "description": (
                f"Booking {booking_id} for {attendee_email} "
                f"was {'successful' if success else 'partially successful' if any(r.get('success') for r in action_results) else 'unsuccessful'}."
            ),
            "outcome": "success" if success else "partial" if any(r.get("success") for r in action_results) else "failure",
            "result": {
                "booking_id": booking_id,
                "attendee_email": attendee_email,
                "organizer_id": organizer_id,
                "success": success,
                "actions": action_results,
                "decision_score": decision_score
            },
            "context": {
                "attendee_email": attendee_email,
                "organizer_id": organizer_id,
                "booking_id": booking_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "importance": 0.8 if success else 0.5,
            "tags": ["booking", "automation", "outcome"]
        }

        await self.memory_manager.long_term.store_episode(episode)

    async def _recall_similar_bookings(
        self,
        attendee_email: str,
        organizer_id: str
    ) -> List[Dict[str, Any]]:
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
            if (
                context.get("organizer_id") == organizer_id
                or context.get("attendee_email") == attendee_email
            ):
                filtered.append(item)

        return filtered[:5]

    async def process_booking_created(
        self,
        booking_id: str,
        user_id: str,
        trigger_source: str = "scheduler"
    ) -> AutomationResult:
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
        start_time = datetime.utcnow()
        metrics = get_agent_metrics()
        
        # Record automation start
        metrics.record_automation_start(booking_id)
        
        logger.info(f"🚀 Booking Automation Started: {booking_id}")
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # STEP 1: AI AGENT TRIGGERED
            # Booking Controller calls AgentOrchestrator
            # Event: BOOKING_CREATED
            # ═══════════════════════════════════════════════════════════════
            
            logger.info(f"[{booking_id}] Step 1: AI Agent Triggered")
            
            # Initialize components
            controller = await get_agent_controller()
            self.decision_engine = await create_decision_engine()
            self.vector_store = await get_vector_store()
            self.memory_manager = await create_memory_manager(
                user_id=user_id,
                vector_store=self.vector_store
            )
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 2: AGENT PERCEPTION PHASE
            # Load booking data, attendee profile, preferences, calendar, rules
            # ═══════════════════════════════════════════════════════════════
            
            logger.info(f"[{booking_id}] Step 2: Agent Perception Phase")
            
            # Measure perception phase with metrics
            phase_start = time.time()
            perception_data = await self._perception_phase(
                booking_id=booking_id,
                user_id=user_id
            )
            phase_duration = (time.time() - phase_start) * 1000
            
            # Record phase metrics
            metrics.record_agent_complete(
                tracking_id=metrics.record_agent_start("booking_agent", "perception"),
                agent_type="booking_agent",
                phase="perception",
                status="success"
            )
            log_phase_execution(booking_id, "perception", phase_duration, True)
            
            logger.info(f"[{booking_id}] Perception complete:")
            logger.info(f"  - Attendee: {perception_data['attendee_email']}")
            logger.info(f"  - Past bookings: {perception_data['attendee_info'].get('past_bookings', 0)}")
            logger.info(f"  - No-show rate: {perception_data['attendee_info'].get('no_show_rate', 0):.1%}")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 3: LLaMA REASONING (via Decision Engine)
            # Agent analyzes and decides optimal actions
            # ═══════════════════════════════════════════════════════════════
            
            logger.info(f"[{booking_id}] Step 3: LLaMA Reasoning")
            
            # Build booking data for decision engine
            booking_data = {
                "id": booking_id,
                "title": perception_data["booking_title"],
                "start_time": perception_data["start_time"],
                "duration_minutes": perception_data["duration_minutes"],
                "attendees": [perception_data["attendee_email"]],
                "organizer": user_id,
                "type": perception_data.get("booking_type", "consultation"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Measure decision latency
            decision_start = time.time()
            
            # Get decision from engine
            decision = await self.decision_engine.analyze_and_decide(
                booking=booking_data,
                attendee_info=perception_data["attendee_info"],
                context=perception_data["context"]
            )
            
            # Record decision metrics
            decision_latency = time.time() - decision_start
            metrics.record_decision_latency(
                decision_type=decision.risk_analysis.level.value,
                latency_seconds=decision_latency
            )
            
            # Log structured decision
            log_agent_decision(
                booking_id=booking_id,
                decision=f"risk_{decision.risk_analysis.level.value}",
                confidence=decision.confidence.value if hasattr(decision.confidence, 'value') else 0.8,
                reasoning=decision.reasoning,
                risk_level=decision.risk_analysis.level.value,
                actions=[{"tool_name": a.tool_name, "priority": a.priority.name} for a in decision.actions],
                latency_ms=decision_latency * 1000
            )
            
            # Log reasoning
            logger.info(f"[{booking_id}] Reasoning complete:")
            logger.info(f"  - VIP Level: {decision.attendee_analysis.vip_level.value}")
            logger.info(f"  - Risk: {decision.risk_analysis.level.value}")
            logger.info(f"  - Actions planned: {len(decision.actions)}")
            logger.info(f"  - Human review needed: {decision.requires_human_review}")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 4: AGENT ACTION EXECUTION PHASE
            # Execute decided tools: Email, Calendar, Task, etc.
            # ═══════════════════════════════════════════════════════════════
            
            logger.info(f"[{booking_id}] Step 4: Action Execution Phase")
            
            phase_start = time.time()
            action_results = await self._action_phase(
                booking_id=booking_id,
                decision=decision,
                perception_data=perception_data
            )
            phase_duration = (time.time() - phase_start) * 1000
            
            # Record phase metrics
            metrics.record_agent_complete(
                tracking_id=metrics.record_agent_start("booking_agent", "action"),
                agent_type="booking_agent",
                phase="action",
                status="success" if all(r.get("success") for r in action_results) else "partial"
            )
            log_phase_execution(
                booking_id=booking_id,
                phase="action",
                duration_ms=phase_duration,
                success=all(r.get("success") for r in action_results)
            )
            
            logger.info(f"[{booking_id}] Actions executed: {len(action_results)}")
            for result in action_results:
                status = "✅" if result.get("success") else "❌"
                logger.info(f"  {status} {result.get('tool_name')}: {result.get('status', 'unknown')}")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 5: AGENT REFLECTION PHASE
            # Assess outcomes, learn patterns, update memory
            # ═══════════════════════════════════════════════════════════════
            
            logger.info(f"[{booking_id}] Step 5: Reflection Phase")
            
            phase_start = time.time()
            reflection_data = await self._reflection_phase(
                booking_id=booking_id,
                decision=decision,
                action_results=action_results,
                perception_data=perception_data
            )
            phase_duration = (time.time() - phase_start) * 1000
            
            # Record phase metrics
            metrics.record_agent_complete(
                tracking_id=metrics.record_agent_start("booking_agent", "reflection"),
                agent_type="booking_agent",
                phase="reflection",
                status="success"
            )
            log_phase_execution(booking_id, "reflection", phase_duration, True)
            
            logger.info(f"[{booking_id}] Reflection:")
            logger.info(f"  - Overall: {reflection_data['assessment']}")
            logger.info(f"  - Learnings: {len(reflection_data['learnings'])}")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 6: RESULTS STORED IN DATABASE
            # Store automation status, decisions, external results
            # ═══════════════════════════════════════════════════════════════
            
            logger.info(f"[{booking_id}] Step 6: Storing Results")
            
            external_results = {
                "email_id": next((r.get("email_id") for r in action_results if r.get("tool_name") == "send_email"), None),
                "calendar_id": next((r.get("event_id") for r in action_results if r.get("tool_name") == "create_calendar_event"), None),
                "task_id": next((r.get("task_id") for r in action_results if r.get("tool_name") == "create_task"), None)
            }
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Store results in database
            await self._store_results(
                booking_id=booking_id,
                user_id=user_id,
                decision=decision,
                action_results=action_results,
                external_results=external_results,
                reflection_data=reflection_data,
                execution_time_ms=execution_time,
                fallback_mode=None  # Set to "rule_based" or "manual_review" if fallback was used
            )
            
            # Calculate decision score
            decision_score = self._calculate_decision_score(decision, action_results)
            
            # Record completion metrics
            success = all(r.get("success") for r in action_results)
            status = "completed" if success else "partial"
            
            metrics.record_automation_complete(
                booking_id=booking_id,
                status=status,
                risk_level=decision.risk_analysis.level.value,
                vip_level=decision.attendee_analysis.vip_level.value,
                decision_score=decision_score,
                booking_value=perception_data.get("estimated_value", 0)
            )
            
            # Log structured completion
            log_automation_complete(
                booking_id=booking_id,
                status=status,
                decision_score=decision_score,
                risk_assessment=decision.risk_analysis.level.value,
                actions_executed=len(action_results),
                execution_time_ms=execution_time
            )
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 7: RETURN RESULTS TO USER
            # ═══════════════════════════════════════════════════════════════
            
            result = AutomationResult(
                booking_id=booking_id,
                automation_status="completed" if all(r.get("success") for r in action_results) else "partial",
                actions_executed=action_results,
                agent_decisions={
                    "actions": [a.tool_name for a in decision.actions],
                    "reasoning": decision.reasoning,
                    "risk_assessment": decision.risk_analysis.level.value,
                    "confidence": decision.confidence.name
                },
                external_results=external_results,
                risk_assessment=decision.risk_analysis.level.value,
                decision_score=decision_score,
                execution_time_ms=execution_time,
                timestamp=datetime.utcnow().isoformat()
            )
            
            logger.info(f"✅ Booking Automation Complete: {booking_id}")
            logger.info(f"  - Status: {result.automation_status}")
            logger.info(f"  - Score: {result.decision_score}/100")
            logger.info(f"  - Time: {execution_time:.0f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Booking Automation Failed: {booking_id} - {e}")
            
            # Record error metrics
            metrics.record_error(error_type="automation_failure", component="booking_automation")
            metrics.record_automation_complete(
                booking_id=booking_id,
                status="failed",
                risk_level="unknown",
                vip_level="unknown",
                decision_score=0
            )
            
            # Log structured failure
            log_automation_complete(
                booking_id=booking_id,
                status="failed",
                decision_score=0,
                risk_assessment="unknown",
                actions_executed=0,
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                error=str(e)
            )
            
            # Return failure result
            return AutomationResult(
                booking_id=booking_id,
                automation_status="failed",
                actions_executed=[],
                agent_decisions={"error": str(e)},
                external_results={},
                risk_assessment="unknown",
                decision_score=0,
                execution_time_ms=0,
                timestamp=datetime.utcnow().isoformat()
            )
    
    # ═════════════════════════════════════════════════════════════════
    # PHASE IMPLEMENTATIONS
    # ═════════════════════════════════════════════════════════════════
    
    async def _perception_phase(
        self,
        booking_id: str,
        user_id: str
    ) -> Dict[str, Any]:
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
        async with get_db() as db:
            # 1. Load booking data
            # TODO: Query booking from database
            booking_data = {
                "id": booking_id,
                "title": "Consultation with John Smith",
                "start_time": "2024-01-16T14:00:00",
                "duration_minutes": 30,
                "attendee_email": "john.smith@example.com",
                "booking_type": "consultation",
                "organizer_id": user_id
            }
            
            # 2. Get attendee profile
            attendee_info = await get_attendee_info(
                email=booking_data["attendee_email"]
            )
            
            if not attendee_info.get("success"):
                # New attendee - use defaults
                attendee_profile = {
                    "email": booking_data["attendee_email"],
                    "is_new": True,
                    "past_bookings": 0,
                    "no_show_rate": 0.0,
                    "engagement_score": 0.5,
                    "preferred_communication": ["email"],
                    "avg_response_time_hours": 24,
                    "timezone": "America/New_York"
                }
            else:
                attendee_profile = attendee_info.get("attendee", {})
                attendee_profile["is_new"] = False
            
            # 3. Check past interactions from memory
            recent_interactions = await self.memory_manager.retrieve_by_context(
                query=f"interactions with {booking_data['attendee_email']}",
                n_results=5
            )

            # 3b. Recall similar past booking outcomes
            similar_bookings = await self._recall_similar_bookings(
                booking_data["attendee_email"],
                booking_data["organizer_id"]
            )
            
            # 4. Fetch user preferences
            user_prefs = self.memory_manager.medium_term.user_preferences
            
            # 5. Analyze calendar availability
            # TODO: Check organizer's calendar
            calendar_available = True
            
            # 6. Check business rules
            rules_check = await check_business_rules(
                booking={
                    "duration_minutes": booking_data["duration_minutes"],
                    "attendee_count": 1,
                    "start_time": booking_data["start_time"]
                }
            )
            
            # 7. Build complete context
            context = {
                "booking_type": booking_data["booking_type"],
                "lead_time_hours": self._calculate_lead_time(booking_data["start_time"]),
                "calendar_available": calendar_available,
                "business_rules_compliant": rules_check.get("is_valid", True),
                "recent_interactions": recent_interactions,
                "similar_bookings": similar_bookings,
                "user_preferences": user_prefs
            }
            
            # Store in short-term memory
            await self.memory_manager.store(
                key="perception_data",
                value={
                    "booking_id": booking_id,
                    "attendee_email": booking_data["attendee_email"],
                    "context": context
                },
                layer=self.memory_manager.__class__.__name__,
                priority=self.memory_manager.__class__.__name__,
                source="perception_phase"
            )
            
            return {
                "booking_id": booking_id,
                "booking_title": booking_data["title"],
                "start_time": booking_data["start_time"],
                "duration_minutes": booking_data["duration_minutes"],
                "attendee_email": booking_data["attendee_email"],
                "booking_type": booking_data["booking_type"],
                "attendee_info": attendee_profile,
                "context": context
            }
    
    async def _action_phase(
        self,
        booking_id: str,
        decision: AgentDecision,
        perception_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        ACTION EXECUTION PHASE
        
        Execute decided tools in order:
        1. Send Email (HIGH PRIORITY - immediate)
        2. Create Calendar Event (MEDIUM)
        3. Create Reminder Task (MEDIUM)
        4. Check CRM (LOW)
        """
        results = []
        
        # Get actions in execution order
        for action_id in decision.execution_order:
            action_index = int(action_id.split('_')[1])
            action = decision.actions[action_index]
            
            logger.info(f"  Executing: {action.tool_name} (Priority: {action.priority.value})")
            
            try:
                # Execute tool based on name
                if action.tool_name == "send_email":
                    result = await send_email(**action.parameters)
                    results.append({
                        "tool_name": "send_email",
                        "success": result.get("success", False),
                        "email_id": result.get("email_id"),
                        "status": "sent" if result.get("success") else "failed",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif action.tool_name == "create_calendar_event":
                    result = await create_calendar_event(**action.parameters)
                    results.append({
                        "tool_name": "create_calendar_event",
                        "success": result.get("success", False),
                        "event_id": result.get("event_id"),
                        "status": "created" if result.get("success") else "failed",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif action.tool_name == "create_task":
                    result = await create_task(**action.parameters)
                    results.append({
                        "tool_name": "create_task",
                        "success": result.get("success", False),
                        "task_id": result.get("task_id"),
                        "status": "created" if result.get("success") else "failed",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Store result in short-term memory
                await self.memory_manager.context.store_phase_result(
                    phase="action",
                    key=f"tool_{action.tool_name}",
                    value=result
                )
                
            except Exception as e:
                logger.error(f"Tool execution failed: {action.tool_name} - {e}")
                results.append({
                    "tool_name": action.tool_name,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return results
    
    async def _reflection_phase(
        self,
        booking_id: str,
        decision: AgentDecision,
        action_results: List[Dict[str, Any]],
        perception_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        REFLECTION PHASE
        
        - Assess outcomes
        - Learn patterns
        - Update memory
        - Store for future
        """
        # Assess overall success
        all_success = all(r.get("success") for r in action_results)
        partial_success = any(r.get("success") for r in action_results)
        
        if all_success:
            assessment = "Optimal"
        elif partial_success:
            assessment = "Partial"
        else:
            assessment = "Failed"
        
        # Extract learnings
        learnings = []
        
        # Learning 1: Attendee response pattern
        if perception_data["attendee_info"].get("no_show_rate", 0) < 0.1:
            learnings.append({
                "type": "attendee_reliability",
                "pattern": "Low no-show rate indicates reliable attendee",
                "confidence": 0.9
            })
        
        # Learning 2: Template effectiveness
        email_result = next((r for r in action_results if r.get("tool_name") == "send_email"), None)
        if email_result and email_result.get("success"):
            learnings.append({
                "type": "template_effectiveness",
                "pattern": "Personalized confirmation email works well",
                "confidence": 0.85
            })
        
        # Update medium-term memory with patterns
        for learning in learnings:
            self.memory_manager.medium_term.add_pattern(
                pattern_type=learning["type"],
                pattern_data=learning,
                outcome="success" if all_success else "partial"
            )
        
        # Promote to long-term if high confidence
        if decision.confidence.value >= 0.8 and all_success:
            await self.memory_manager.long_term.store_episode({
                "type": "successful_booking",
                "booking_id": booking_id,
                "attendee": perception_data["attendee_email"],
                "strategy": "standard_confirmation_flow",
                "outcome": "success",
                "confidence": decision.confidence.value,
                "timestamp": datetime.utcnow().isoformat(),
                "importance": 0.8
            })
        
        # End workflow - cleanup short-term
        await self.memory_manager.context.end_workflow()

        # Persist the booking outcome to long-term memory
        await self._remember_booking(
            booking_id=booking_id,
            attendee_email=perception_data["attendee_email"],
            organizer_id=perception_data["organizer_id"],
            action_results=action_results,
            success=all_success,
            decision_score=decision.confidence.value if hasattr(decision, 'confidence') else 0
        )
        
        return {
            "assessment": assessment,
            "all_success": all_success,
            "partial_success": partial_success,
            "learnings": learnings,
            "actions_count": len(action_results),
            "successful_actions": sum(1 for r in action_results if r.get("success"))
        }
    
    async def _store_results(
        self,
        booking_id: str,
        user_id: str,
        decision: AgentDecision,
        action_results: List[Dict[str, Any]],
        external_results: Dict[str, Any],
        reflection_data: Dict[str, Any],
        execution_time_ms: float,
        fallback_mode: Optional[str] = None
    ):
        """Store automation results in database"""
        try:
            async with get_db() as db:
                from backend.models.tables import AIAutomationTable
                from datetime import datetime, timezone
                
                # Calculate status based on action results
                all_success = all(r.get("success") for r in action_results)
                any_success = any(r.get("success") for r in action_results)
                
                if all_success:
                    status = "completed"
                elif any_success:
                    status = "partial"
                else:
                    status = "failed"
                
                # Calculate decision score
                decision_score = self._calculate_decision_score(decision, action_results)
                
                # Build agent decisions dict
                agent_decisions = {
                    "actions": [{
                        "tool_name": a.tool_name,
                        "priority": a.priority.name if hasattr(a.priority, 'name') else str(a.priority),
                        "parameters": a.parameters
                    } for a in decision.actions],
                    "reasoning": decision.reasoning,
                    "confidence": decision.confidence.name if hasattr(decision.confidence, 'name') else str(decision.confidence),
                    "execution_order": decision.execution_order,
                    "requires_human_review": decision.requires_human_review
                }
                
                # Create automation record
                automation = AIAutomationTable(
                    booking_id=booking_id,
                    user_id=user_id,
                    status=status,
                    decision_score=decision_score,
                    risk_assessment=decision.risk_analysis.level.value if hasattr(decision.risk_analysis.level, 'value') else str(decision.risk_analysis.level),
                    agent_decisions=agent_decisions,
                    actions_executed=action_results,
                    external_results=external_results,
                    execution_time_ms=execution_time_ms,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    fallback_mode=fallback_mode,
                    trigger_source="api"
                )
                
                db.add(automation)
                await db.commit()
                
                logger.info(f"[{booking_id}] Automation results stored in database (ID: {automation.id})")
                
                return automation.id
                
        except Exception as e:
            logger.error(f"[{booking_id}] Failed to store automation results: {e}")
            # Don't raise - we don't want to fail the whole workflow if storage fails
            return None
    
    def _calculate_lead_time(self, start_time: str) -> float:
        """Calculate hours until booking"""
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        return (start - datetime.utcnow()).total_seconds() / 3600
    
    def _calculate_decision_score(
        self,
        decision: AgentDecision,
        action_results: List[Dict[str, Any]]
    ) -> int:
        """Calculate decision quality score (0-100)"""
        score = 0
        
        # Base score from confidence
        confidence_scores = {
            "LOW": 50,
            "MEDIUM": 70,
            "HIGH": 85,
            "CERTAIN": 95
        }
        score += confidence_scores.get(decision.confidence.name, 50)
        
        # Adjust for risk
        if decision.risk_analysis.level.value == "low":
            score += 5
        elif decision.risk_analysis.level.value == "high":
            score -= 10
        
        # Adjust for execution success
        success_rate = sum(1 for r in action_results if r.get("success")) / len(action_results) if action_results else 0
        score += int(success_rate * 10)
        
        return max(0, min(100, score))


# Webhook handler for booking creation
def on_booking_created(booking_id: str, user_id: str) -> AutomationResult:
    """
    Webhook handler - called when user creates booking in scheduler
    
    This is the entry point that triggers the entire workflow.
    """
    service = BookingAutomationService()
    
    # Run async workflow
    return asyncio.run(service.process_booking_created(
        booking_id=booking_id,
        user_id=user_id,
        trigger_source="scheduler_webhook"
    ))


# API endpoint for manual trigger
async def api_trigger_booking_automation(
    booking_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    API endpoint to manually trigger booking automation
    
    POST /api/bookings/{booking_id}/automate
    """
    service = BookingAutomationService()
    
    result = await service.process_booking_created(
        booking_id=booking_id,
        user_id=user_id
    )
    
    return {
        "booking_id": result.booking_id,
        "status": result.automation_status,
        "decision_score": result.decision_score,
        "risk_assessment": result.risk_assessment,
        "actions": result.agent_decisions.get("actions", []),
        "external_ids": result.external_results,
        "execution_time_ms": result.execution_time_ms,
        "timestamp": result.timestamp
    }
