"""
Booking Agent - Validates and routes booking requests
Handles conflict detection, availability checking, and workflow routing
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from backend.ai.agents.base import BaseAgent, AgentContext
from backend.utils.logger import get_logger
from backend.tasks.email_tasks import send_booking_confirmation
from backend.tasks.reminder_tasks import schedule_booking_reminders

logger = get_logger(__name__)


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
            name="BookingAgent",
            description="Validates bookings, checks availability, and routes workflows"
        )
    
    def _get_available_tools(self) -> list:
        return [
            "check_availability",
            "detect_conflicts",
            "validate_attendees",
            "prepare_metadata",
            "route_workflow",
            "schedule_reminders"
        ]
    
    async def _execute(self, context: AgentContext) -> Dict[str, Any]:
        """
        Execute booking validation and routing
        
        Args:
            context: Contains booking data (title, start_time, duration, attendees, etc.)
            
        Returns:
            Booking result with validation status and workflow routing
        """
        data = context.data
        
        # Extract booking details
        title = data.get("title", "Untitled Meeting")
        start_time_str = data.get("start_time")
        duration = data.get("duration", 30)
        attendees = data.get("attendees", [])
        user_id = context.user_id
        
        logger.info(f"BookingAgent processing: {title} for user {user_id}")
        
        # Step 1: Validate booking data
        validation_result = await self._validate_booking_data(data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "stage": "validation",
                "error": validation_result["error"],
                "suggestions": validation_result.get("suggestions", [])
            }
        
        # Step 2: Parse and validate time
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = start_time + timedelta(minutes=duration)
        
        # Step 3: Check availability
        availability = await self._check_availability(user_id, start_time, end_time)
        if not availability["available"]:
            return {
                "success": False,
                "stage": "availability_check",
                "error": "Time slot not available",
                "conflicts": availability.get("conflicts", []),
                "alternative_slots": availability.get("alternatives", [])
            }
        
        # Step 4: Detect conflicts with attendees
        attendee_conflicts = await self._check_attendee_conflicts(attendees, start_time, end_time)
        if attendee_conflicts:
            return {
                "success": False,
                "stage": "attendee_conflict_check",
                "error": "Attendees have conflicts",
                "conflicts": attendee_conflicts,
                "alternative_slots": await self._find_alternative_slots(attendees, duration, start_time)
            }
        
        # Step 5: Prepare booking metadata
        metadata = await self._prepare_metadata(
            title=title,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            attendees=attendees,
            user_id=user_id,
            additional_data=data
        )
        
        # Step 6: Route to appropriate workflow
        workflow_result = await self._route_workflow(metadata)
        
        # Step 7: Schedule reminders if successful
        reminders_scheduled = False
        if workflow_result["success"]:
            reminders_scheduled = await self._schedule_reminders(workflow_result["booking_id"], metadata)

        actions_taken = [
            "validated_booking_data",
            "checked_availability",
            "checked_attendee_conflicts",
            "prepared_metadata",
            "routed_workflow"
        ]
        if reminders_scheduled:
            actions_taken.append("scheduled_reminders")
        
        return {
            "success": workflow_result["success"],
            "stage": "complete",
            "booking_id": workflow_result.get("booking_id"),
            "metadata": metadata,
            "workflow": workflow_result.get("workflow_id"),
            "actions_taken": actions_taken
        }
    
    async def _validate_booking_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate booking request data"""
        errors = []
        suggestions = []
        
        # Check required fields
        if not data.get("title"):
            errors.append("Meeting title is required")
        
        if not data.get("start_time"):
            errors.append("Start time is required")
        else:
            try:
                datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid start time format")
        
        if not data.get("duration") or data.get("duration") <= 0:
            errors.append("Valid duration is required")
        
        # Validate attendees
        attendees = data.get("attendees", [])
        if len(attendees) > 50:
            errors.append("Maximum 50 attendees allowed")
        
        # Check for common issues
        if data.get("duration", 0) > 480:  # 8 hours
            suggestions.append("Consider breaking long meetings into sessions")
        
        if len(attendees) > 10 and data.get("duration", 0) < 30:
            suggestions.append("Large meetings may need more time")
        
        return {
            "valid": len(errors) == 0,
            "error": "; ".join(errors) if errors else None,
            "suggestions": suggestions
        }
    
    async def _check_availability(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Check if time slot is available for user"""
        # Query database for conflicts
        
        # Placeholder: Actual implementation would query EventTable
        # and check work_hours, busy times from integrations
        
        return {
            "available": True,
            "conflicts": [],
            "alternatives": []
        }
    
    async def _check_attendee_conflicts(
        self,
        attendees: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Check if attendees have conflicts"""
        conflicts = []
        
        for attendee in attendees:
            email = attendee.get("email")
            # Check if attendee has conflicting meetings
            # This would query their calendar via integration
            
            # Placeholder logic
            pass
        
        return conflicts
    
    async def _find_alternative_slots(
        self,
        attendees: List[Dict[str, Any]],
        duration: int,
        start_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Find alternative meeting times"""
        # Use optimization algorithm to find best alternative times
        # considering all attendees' availability
        
        alternatives = []
        
        # Placeholder: Return next 3 available slots
        if start_time:
            for i in range(1, 4):
                alt_time = start_time + timedelta(days=i)
                alternatives.append({
                    "start_time": alt_time.isoformat(),
                    "end_time": (alt_time + timedelta(minutes=duration)).isoformat(),
                    "score": 1.0 - (i * 0.1)  # Preference score
                })
        
        return alternatives
    
    async def _prepare_metadata(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        duration: int,
        attendees: List[Dict[str, Any]],
        user_id: str,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare comprehensive booking metadata"""
        return {
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration,
            "attendees": attendees,
            "attendee_count": len(attendees),
            "organizer_id": user_id,
            "location": additional_data.get("location"),
            "description": additional_data.get("description"),
            "is_recurring": additional_data.get("is_recurring", False),
            "recurrence_rule": additional_data.get("recurrence_rule"),
            "timezone": additional_data.get("timezone", "UTC"),
            "meeting_type": self._classify_meeting_type(title, attendees),
            "priority": additional_data.get("priority", "normal"),
            "requires_confirmation": additional_data.get("requires_confirmation", False),
            "created_at": datetime.utcnow().isoformat(),
            "booking_agent_version": "1.0"
        }
    
    def _classify_meeting_type(self, title: str, attendees: List[Dict[str, Any]]) -> str:
        """Classify meeting type based on title and attendees"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["interview", "screening"]):
            return "interview"
        elif any(word in title_lower for word in ["review", "1:1", "one-on-one"]):
            return "review"
        elif any(word in title_lower for word in ["workshop", "training", "demo"]):
            return "workshop"
        elif any(word in title_lower for word in ["sync", "standup", "daily"]):
            return "standup"
        elif len(attendees) > 10:
            return "all_hands"
        else:
            return "general"
    
    async def _route_workflow(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Route booking to appropriate workflow"""
        meeting_type = metadata.get("meeting_type")
        
        # Determine workflow based on meeting type
        workflows = {
            "interview": "interview_booking_workflow",
            "review": "review_booking_workflow",
            "workshop": "workshop_booking_workflow",
            "general": "standard_booking_workflow"
        }
        
        workflow_id = workflows.get(meeting_type, "standard_booking_workflow")
        
        # Create booking record
        # Placeholder: Actual implementation would insert into database
        booking_id = f"booking_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "booking_id": booking_id
        }
    
    async def _schedule_reminders(self, booking_id: str, metadata: Dict[str, Any]) -> bool:
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
            logger.warning(f"No attendee email available for reminders on booking {booking_id}")
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

            logger.info(f"Scheduled reminders for booking {booking_id}")
            return True
        except Exception as exc:
            logger.error(f"Failed to schedule reminders for booking {booking_id}: {exc}")
            return False
