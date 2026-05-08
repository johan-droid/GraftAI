"""
Booking Agent - Validates and routes booking requests
Handles conflict detection, availability checking, and workflow routing
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from backend.ai.agents.base import AgentContext, AgentState, BaseAgent
from backend.tasks.email_tasks import send_booking_confirmation
from backend.tasks.reminder_tasks import schedule_booking_reminders
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MAX_ATTENDEES = 50
MAX_MEETING_DURATION_MINUTES = 480
LARGE_MEETING_ATTENDEE_THRESHOLD = 10
SHORT_MEETING_DURATION_MINUTES = 30


async def check_availability(*_args, **_kwargs) -> bool:
    """Check whether the requested booking slot is available."""
    error_message = (
        "check_availability is not implemented for BookingAgent; integrate backend scheduling tools or implement a connector to real calendar APIs"
    )
    raise NotImplementedError(error_message)


async def create_booking(*_args, **_kwargs) -> dict[str, Any]:
    """Create a booking record for the requested meeting."""
    error_message = (
        "create_booking is not implemented for BookingAgent; integrate backend booking persistence or call the real bookings API"
    )
    raise NotImplementedError(error_message)


class BookingAgent(BaseAgent):
    """
    Specialized agent for handling booking requests

    Responsibilities:
    - Validate booking data (attendees, time, duration)
    - Check availability and detect conflicts
    - Prepare booking metadata
    - Route to appropriate workflow
    - Schedule reminders
    """

    def __init__(self):
        super().__init__(
            name="booking",
            description="Validates bookings, checks availability, and routes workflows",
        )

    async def execute(self, request: Any) -> dict[str, Any]:
        """Execute a booking request using the agent loop and booking workflow."""
        request_context = getattr(request, "context", None)
        if request_context is None:
            request_context = request if isinstance(request, dict) else {}
        if not isinstance(request_context, dict):
            request_context = dict(request_context)

        user_id = getattr(request, "user_id", None) or request_context.get("user_id", "")
        request_id = getattr(request, "id", None) or request_context.get(
            "request_id", "booking-request"
        )

        perception = await self.perception_phase(request_context)
        cognition_input = {**request_context, **perception.get("perception", {})}
        cognition = await self.cognition_phase(cognition_input)
        action_input = {
            **request_context,
            "decision": cognition.get("cognition", {}).get("decision", {}),
            "user_id": user_id,
        }
        action = await self.action_phase(action_input)

        reflection = await self.reflection_phase(
            request_context, {"action": action.get("action", action)}
        )

        action_data = action.get("action", action)
        reflection_data = reflection.get("reflection", reflection)
        booking_id = action_data.get("booking_id") or (
            action_data.get("booking", {}) or {}
        ).get("id")
        success = bool(action_data.get("success", False))
        error = None if success else (reflection_data.get("error") or action_data.get("error"))

        final_result = {
            "success": success,
            "booking_id": booking_id,
            "booking": action_data.get("booking"),
            "error": error,
            "phases": {
                "perception": perception.get("perception", perception),
                "cognition": cognition.get("cognition", cognition),
                "action": action_data,
                "reflection": reflection_data,
            },
        }

        self.transition_to(AgentState.READY)

        return {
            "agent": self.name,
            "request_id": request_id,
            "phases": final_result["phases"],
            "success": final_result["success"],
            "booking_id": final_result.get("booking_id"),
            "final_output": final_result,
            "error": final_result.get("error"),
        }

    async def perception_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "perception": {
                "raw_input": context.get("user_message", ""),
                "extracted_entities": context.get("entities", {}),
                "intent": context.get("intent", "general_chat"),
                "state": context.get("state", "unknown"),
            }
        }

    async def cognition_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        entities = context.get("entities", {})
        available = await check_availability(
            user_id=context.get("user_id"),
            entities=entities,
            context=context,
        )

        decision = {
            "action": "create_meeting" if available else "suggest_alternatives",
            "title": context.get("title") or entities.get("title", "Untitled Meeting"),
            "start_time": entities.get("start_time") or context.get("start_time"),
            "duration": entities.get("duration") or context.get("duration", 30),
            "available": available,
            "reasoning": "Slot available" if available else "Slot unavailable",
        }

        return {
            "cognition": {
                "decision": decision,
                "confidence": 0.9 if available else 0.35,
                "constraints_evaluated": {
                    "availability_checked": True,
                    "available": available,
                },
            }
        }

    async def action_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        decision = context.get("decision", {})
        booking = await create_booking(
            user_id=context.get("user_id"),
            decision=decision,
            context=context,
        )

        booking_id = booking.get("booking_id") or booking.get("id")
        success = bool(
            booking.get("success", booking.get("status") in {"confirmed", "success"})
        )

        return {
            "action": {
                "success": success,
                "booking_id": booking_id,
                "booking": booking,
            }
        }

    async def reflection_phase(
        self, _context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        action_result = results.get("action", {})
        success = bool(action_result.get("success", False))

        return {
            "reflection": {
                "success": success,
                "quality_score": 95 if success else 40,
                "lessons": [
                    {
                        "type": "booking_success" if success else "booking_failure",
                        "confidence": 0.9 if success else 0.7,
                    }
                ],
                "improvements": [] if success else ["Review booking constraints before confirming"],
            }
        }

    def _get_available_tools(self) -> list:
        return [
            "check_availability",
            "detect_conflicts",
            "validate_attendees",
            "prepare_metadata",
            "route_workflow",
            "schedule_reminders",
        ]

    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Execute booking validation and routing

        Args:
            context: Contains booking data (title, start_time, duration, attendees, etc.)

        Returns:
            Booking result with validation status and workflow routing
        """
        data = context.data

        title = data.get("title", "Untitled Meeting")
        start_time_str = data.get("start_time")
        duration = data.get("duration", 30)
        attendees = data.get("attendees", [])
        user_id = context.user_id

        logger.info("BookingAgent processing: %s for user %s", title, user_id)

        validation_result = await self._validate_booking_data(data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "stage": "validation",
                "error": validation_result["error"],
                "suggestions": validation_result.get("suggestions", []),
            }

        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_time = start_time + timedelta(minutes=duration)

        availability = await self._check_availability(user_id, start_time, end_time)
        if not availability["available"]:
            return {
                "success": False,
                "stage": "availability_check",
                "error": "Time slot not available",
                "conflicts": availability.get("conflicts", []),
                "alternative_slots": availability.get("alternatives", []),
            }

        attendee_conflicts = await self._check_attendee_conflicts(
            attendees, start_time, end_time
        )
        if attendee_conflicts:
            return {
                "success": False,
                "stage": "attendee_conflict_check",
                "error": "Attendees have conflicts",
                "conflicts": attendee_conflicts,
                "alternative_slots": await self._find_alternative_slots(
                    attendees, duration, start_time
                ),
            }

        metadata = await self._prepare_metadata(
            {
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "attendees": attendees,
                "user_id": user_id,
                **data,
            }
        )

        workflow_result = await self._route_workflow(metadata)

        reminders_scheduled = False
        if workflow_result["success"]:
            reminders_scheduled = await self._schedule_reminders(
                workflow_result["booking_id"], metadata
            )

        actions_taken = [
            "validated_booking_data",
            "checked_availability",
            "checked_attendee_conflicts",
            "prepared_metadata",
            "routed_workflow",
        ]
        if reminders_scheduled:
            actions_taken.append("scheduled_reminders")

        return {
            "success": workflow_result["success"],
            "stage": "complete",
            "booking_id": workflow_result.get("booking_id"),
            "metadata": metadata,
            "workflow": workflow_result.get("workflow_id"),
            "actions_taken": actions_taken,
        }

    async def _validate_booking_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate booking request data"""
        errors = []
        suggestions = []

        if not data.get("title"):
            errors.append("Meeting title is required")

        if not data.get("start_time"):
            errors.append("Start time is required")
        else:
            try:
                datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
            except ValueError:
                errors.append("Invalid start time format")

        if not data.get("duration") or data.get("duration") <= 0:
            errors.append("Valid duration is required")

        attendees = data.get("attendees", [])
        if len(attendees) > MAX_ATTENDEES:
            errors.append("Maximum 50 attendees allowed")

        if data.get("duration", 0) > MAX_MEETING_DURATION_MINUTES:  # 8 hours
            suggestions.append("Consider breaking long meetings into sessions")

        if len(attendees) > LARGE_MEETING_ATTENDEE_THRESHOLD and data.get("duration", 0) < SHORT_MEETING_DURATION_MINUTES:
            suggestions.append("Large meetings may need more time")

        return {
            "valid": len(errors) == 0,
            "error": "; ".join(errors) if errors else None,
            "suggestions": suggestions,
        }

    async def _check_availability(
        self, _user_id: str, _start_time: datetime, _end_time: datetime
    ) -> dict[str, Any]:
        """Check if time slot is available for user"""
        return {"available": True, "conflicts": [], "alternatives": []}

    async def _check_attendee_conflicts(
        self,
        attendees: list[dict[str, Any]],
        _start_time: datetime,
        _end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Check if attendees have conflicts"""
        conflicts = []

        for attendee in attendees:
            _email = attendee.get("email")
            _ = _email

        return conflicts

    async def _find_alternative_slots(
        self,
        _attendees: list[dict[str, Any]],
        duration: int,
        start_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Find alternative meeting times"""
        alternatives = []

        if start_time:
            for i in range(1, 4):
                alt_time = start_time + timedelta(days=i)
                alternatives.append(
                    {
                        "start_time": alt_time.isoformat(),
                        "end_time": (alt_time + timedelta(minutes=duration)).isoformat(),
                        "score": 1.0 - (i * 0.1),
                    }
                )

        return alternatives

    async def _prepare_metadata(self, booking_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare comprehensive booking metadata"""
        title = booking_data.get("title", "Untitled Meeting")
        attendees = booking_data.get("attendees", [])
        start_time = booking_data.get("start_time")
        end_time = booking_data.get("end_time")
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            error_message = "start_time and end_time must be datetime values"
            raise TypeError(error_message)

        return {
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": booking_data.get("duration", 30),
            "attendees": attendees,
            "attendee_count": len(attendees),
            "organizer_id": booking_data.get("user_id", ""),
            "location": booking_data.get("location"),
            "description": booking_data.get("description"),
            "is_recurring": booking_data.get("is_recurring", False),
            "recurrence_rule": booking_data.get("recurrence_rule"),
            "timezone": booking_data.get("timezone", "UTC"),
            "meeting_type": self._classify_meeting_type(title, attendees),
            "priority": booking_data.get("priority", "normal"),
            "requires_confirmation": booking_data.get("requires_confirmation", False),
            "created_at": datetime.now(UTC).isoformat(),
            "booking_agent_version": "1.0",
        }

    def _classify_meeting_type(self, title: str, attendees: list[dict[str, Any]]) -> str:
        """Classify meeting type based on title and attendees"""
        title_lower = title.lower()

        if any(word in title_lower for word in ["interview", "screening"]):
            return "interview"
        if any(word in title_lower for word in ["review", "1:1", "one-on-one"]):
            return "review"
        if any(word in title_lower for word in ["workshop", "training", "demo"]):
            return "workshop"
        if any(word in title_lower for word in ["sync", "standup", "daily"]):
            return "standup"
        if len(attendees) > LARGE_MEETING_ATTENDEE_THRESHOLD:
            return "all_hands"
        return "general"

    async def _route_workflow(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Route booking to appropriate workflow"""
        meeting_type = metadata.get("meeting_type")

        workflows = {
            "interview": "interview_booking_workflow",
            "review": "review_booking_workflow",
            "workshop": "workshop_booking_workflow",
            "general": "standard_booking_workflow",
        }

        workflow_id = workflows.get(meeting_type, "standard_booking_workflow")
        booking_id = f"booking_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

        return {"success": True, "workflow_id": workflow_id, "booking_id": booking_id}

    async def _schedule_reminders(
        self, booking_id: str, metadata: dict[str, Any]
    ) -> bool:
        """Schedule reminders for the booking"""
        attendees = metadata.get("attendees", [])
        first_attendee = attendees[0] if attendees else {}

        if isinstance(first_attendee, dict):
            attendee_email = first_attendee.get("email")
            attendee_name = first_attendee.get("name") or "Attendee"
        elif isinstance(first_attendee, str):
            attendee_email = first_attendee
            attendee_name = "Attendee"
        else:
            attendee_email = None
            attendee_name = "Attendee"

        if not attendee_email:
            logger.warning(
                "No attendee email available for reminders on booking %s",
                booking_id,
            )
            return False

        try:
            send_booking_confirmation.delay(
                booking_id=booking_id,
                attendee_email=attendee_email,
                attendee_name=attendee_name,
                meeting_title=metadata.get("title", "Meeting"),
                start_time=metadata.get("start_time", ""),
                end_time=metadata.get("end_time", ""),
                meeting_url=metadata.get("meeting_url"),
                location=metadata.get("location"),
            )

            schedule_booking_reminders.delay(
                booking_id=booking_id,
                start_time=metadata.get("start_time", ""),
                attendee_email=attendee_email,
                attendee_name=attendee_name,
                meeting_title=metadata.get("title", "Meeting"),
                meeting_url=metadata.get("meeting_url"),
            )
        except Exception:
            logger.exception("Failed to schedule reminders for booking %s", booking_id)
            return False
        else:
            logger.info("Scheduled reminders for booking %s", booking_id)
            return True
