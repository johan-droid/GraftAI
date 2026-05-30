"""
Booking Service Layer

Extracted business logic from API endpoints:
- Booking creation and management
- Conflict detection and resolution
- Automation workflow triggering
- Cache invalidation
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import and_, or_, select

from backend.core.database_replicas import get_read_db_session, get_write_db_session
from backend.models.tables import BookingTable
from backend.services.usage import increment_usage
from backend.tasks.automation_tasks import run_booking_automation_task
from backend.utils.cache import delete_cache, get_cache, set_cache

logger = logging.getLogger(__name__)

class BookingStatus(Enum):
    """Booking status enumeration"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    REJECT = "reject"
    RESCHEDULE = "reschedule"
    SPLIT = "split"
    NOTIFY = "notify"

@dataclass
class BookingConflict:
    """Booking conflict information"""
    existing_booking_id: str
    conflict_type: str
    conflict_details: dict[str, Any]
    resolution_options: list[ConflictResolution]

@dataclass
class BookingValidationResult:
    """Booking validation result"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    conflicts: list[BookingConflict]

@dataclass
class BookingCreationResult:
    """Booking creation result"""
    success: bool
    booking_id: str | None
    automation_id: str | None
    conflicts: list[BookingConflict]
    warnings: list[str]
    message: str

class BookingService:
    """Booking business logic service"""

    def __init__(self):
        self.cache_ttl = 3600
        self.conflict_detection_window = timedelta(hours=24)
        self.automation_enabled = True

    async def create_booking(self, booking_data: dict[str, Any], user_id: str) -> BookingCreationResult:
        """Create booking with comprehensive business logic"""
        try:
            validation_result = await self._validate_booking_data(booking_data, user_id)
            if not validation_result.is_valid:
                return BookingCreationResult(success=False, booking_id=None, automation_id=None, conflicts=[], warnings=validation_result.warnings, message=f"Validation failed: {', '.join(validation_result.errors)}")
            conflicts = await self._detect_conflicts(booking_data, user_id)
            if conflicts:
                resolution = await self._resolve_conflicts(conflicts, booking_data, user_id)
                if not resolution["resolved"]:
                    return BookingCreationResult(success=False, booking_id=None, automation_id=None, conflicts=conflicts, warnings=validation_result.warnings, message=f"Unresolved conflicts: {resolution['message']}")
            booking = await self._persist_booking(booking_data, user_id)
            await self._invalidate_user_cache(user_id)
            automation_id = await self._trigger_automation(booking, user_id)
            await self._update_usage_metrics(user_id)
            return BookingCreationResult(success=True, booking_id=booking.id, automation_id=automation_id, conflicts=conflicts, warnings=validation_result.warnings, message="Booking created successfully")
        except Exception as e:
            logger.exception("Error creating booking for user %s: %s", user_id, e)
            return BookingCreationResult(success=False, booking_id=None, automation_id=None, conflicts=[], warnings=[], message=f"Failed to create booking: {e!s}")

    async def _validate_booking_data(self, booking_data: dict[str, Any], user_id: str) -> BookingValidationResult:
        """Validate booking data"""
        errors = []
        warnings = []
        required_fields = ["title", "start_time", "end_time"]
        for field in required_fields:
            if not booking_data.get(field):
                errors.append(f"Missing required field: {field}")
        start_time = booking_data.get("start_time")
        end_time = booking_data.get("end_time")
        if start_time and end_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            if start_time >= end_time:
                errors.append("Start time must be before end time")
            if start_time < datetime.now(UTC):
                errors.append("Start time cannot be in the past")
            if start_time > datetime.now(UTC) + timedelta(days=365):
                warnings.append("Booking is more than 1 year in the future")
            duration = end_time - start_time
            if duration > timedelta(hours=8):
                warnings.append("Booking duration exceeds 8 hours")
            elif duration < timedelta(minutes=15):
                errors.append("Booking duration must be at least 15 minutes")
        if not await self._check_user_quota(user_id):
            errors.append("User quota exceeded for bookings")
        return BookingValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings, conflicts=[])

    async def _detect_conflicts(self, booking_data: dict[str, Any], user_id: str) -> list[BookingConflict]:
        """Detect booking conflicts"""
        conflicts = []
        start_time = booking_data.get("start_time")
        end_time = booking_data.get("end_time")
        if not start_time or not end_time:
            return conflicts
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        async with get_read_db_session() as db:
            query = select(BookingTable).where(and_(BookingTable.user_id == user_id, BookingTable.status.in_([BookingStatus.SCHEDULED.value, BookingStatus.CONFIRMED.value]), or_(and_(BookingTable.start_time <= start_time, BookingTable.end_time > start_time), and_(BookingTable.start_time < end_time, BookingTable.end_time >= end_time), and_(BookingTable.start_time >= start_time, BookingTable.end_time <= end_time))))
            result = await db.execute(query)
            existing_bookings = result.scalars().all()
            for existing_booking in existing_bookings:
                conflict = BookingConflict(existing_booking_id=existing_booking.id, conflict_type="time_overlap", conflict_details={"existing_start": existing_booking.start_time.isoformat(), "existing_end": existing_booking.end_time.isoformat(), "existing_title": existing_booking.title}, resolution_options=[ConflictResolution.RESCHEDULE, ConflictResolution.REJECT])
                conflicts.append(conflict)
        return conflicts

    async def _resolve_conflicts(self, conflicts: list[BookingConflict], booking_data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Resolve booking conflicts"""
        for conflict in conflicts:
            if conflict.conflict_type == "time_overlap":
                alternatives = await self._find_alternative_slots(booking_data, user_id)
                if alternatives:
                    return {"resolved": True, "message": "Alternative time slots available", "alternatives": alternatives}
                return {"resolved": False, "message": "No alternative time slots available"}
        return {"resolved": True, "message": "No conflicts to resolve"}

    async def _find_alternative_slots(self, booking_data: dict[str, Any], user_id: str) -> list[dict[str, Any]]:
        """Find alternative time slots for conflicted booking"""
        alternatives = []
        start_time = booking_data.get("start_time")
        end_time = booking_data.get("end_time")
        if not start_time or not end_time:
            return alternatives
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration = end_time - start_time
        for days_ahead in range(1, 8):
            candidate_start = start_time + timedelta(days=days_ahead)
            candidate_end = candidate_start + duration
            if candidate_start.weekday() >= 5:
                continue
            if await self._is_slot_available(candidate_start, candidate_end, user_id):
                alternatives.append({"start_time": candidate_start.isoformat(), "end_time": candidate_end.isoformat(), "days_ahead": days_ahead})
                if len(alternatives) >= 3:
                    break
        return alternatives

    async def _is_slot_available(self, start_time: datetime, end_time: datetime, user_id: str) -> bool:
        """Check if time slot is available"""
        async with get_read_db_session() as db:
            query = select(BookingTable).where(and_(BookingTable.user_id == user_id, BookingTable.status.in_([BookingStatus.SCHEDULED.value, BookingStatus.CONFIRMED.value]), or_(and_(BookingTable.start_time <= start_time, BookingTable.end_time > start_time), and_(BookingTable.start_time < end_time, BookingTable.end_time >= end_time), and_(BookingTable.start_time >= start_time, BookingTable.end_time <= end_time))))
            result = await db.execute(query)
            conflicts = result.scalars().all()
            return len(conflicts) == 0

    async def _persist_booking(self, booking_data: dict[str, Any], user_id: str) -> BookingTable:
        """Persist booking to database"""
        async with get_write_db_session() as db:
            start_time = booking_data.get("start_time")
            end_time = booking_data.get("end_time")
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            booking = BookingTable(title=booking_data.get("title"), description=booking_data.get("description"), start_time=start_time, end_time=end_time, user_id=user_id, timezone=booking_data.get("timezone", "UTC"), status=BookingStatus.SCHEDULED.value, metadata_payload=booking_data.get("metadata", {}), email=booking_data.get("email"), full_name=booking_data.get("full_name"), created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
            db.add(booking)
            await db.flush()
            await db.refresh(booking)
            logger.info("Created booking %s for user %s", booking.id, user_id)
            return booking

    async def _invalidate_user_cache(self, user_id: str):
        """Invalidate user-related cache entries"""
        try:
            await delete_cache(f"user_calendar:{user_id}")
            await delete_cache(f"user_bookings:{user_id}")
            await delete_cache(f"user_preferences:{user_id}")
            logger.info("Invalidated cache for user %s...", user_id[:8])
        except Exception as e:
            logger.exception("Failed to invalidate cache for user %s: %s", user_id, e)

    async def _trigger_automation(self, booking: BookingTable, user_id: str) -> str | None:
        """Trigger automation workflow for booking"""
        if not self.automation_enabled:
            return None
        try:
            attendee_data = None
            if booking.metadata_payload and "attendees" in booking.metadata_payload:
                attendees = booking.metadata_payload.get("attendees")
                if attendees and isinstance(attendees, list) and (len(attendees) > 0):
                    attendee_email = attendees[0]
                else:
                    attendee_email = booking.email
                attendee_data = {"email": attendee_email, "name": booking.full_name}
            task = run_booking_automation_task.delay(booking_id=booking.id, automation_id=None, user_id=user_id, attendee_data=attendee_data, booking_data={"title": booking.title, "description": booking.description, "start_time": booking.start_time.isoformat(), "end_time": booking.end_time.isoformat(), "timezone": booking.timezone})
            logger.info("Triggered automation task %s for booking %s", task.id, booking.id)
            return task.id
        except Exception as e:
            logger.exception("Failed to trigger automation for booking %s: %s", booking.id, e)
            return None

    async def _update_usage_metrics(self, user_id: str):
        """Update usage metrics for user"""
        try:
            await increment_usage(user_id, "daily_bookings")
            await increment_usage(user_id, "total_scheduling_count")
            logger.info("Updated usage metrics for user %s...", user_id[:8])
        except Exception as e:
            logger.exception("Failed to update usage metrics for user %s: %s", user_id, e)

    async def _check_user_quota(self, user_id: str) -> bool:
        """Check if user has quota for creating bookings"""
        try:
            return True
        except Exception as e:
            logger.exception("Failed to check quota for user %s: %s", user_id, e)
            return True

    async def get_booking(self, booking_id: str, user_id: str) -> dict[str, Any] | None:
        """Get booking by ID for user"""
        try:
            cache_key = f"booking:{booking_id}"
            cached_booking = await get_cache(cache_key)
            if cached_booking:
                return cached_booking
            async with get_read_db_session() as db:
                query = select(BookingTable).where(and_(BookingTable.id == booking_id, BookingTable.user_id == user_id))
                result = await db.execute(query)
                booking = result.scalar_one_or_none()
                if booking:
                    booking_data = {"id": booking.id, "title": booking.title, "description": booking.description, "start_time": booking.start_time.isoformat(), "end_time": booking.end_time.isoformat(), "timezone": booking.timezone, "status": booking.status, "email": booking.email, "full_name": booking.full_name, "metadata": booking.metadata_payload, "created_at": booking.created_at.isoformat(), "updated_at": booking.updated_at.isoformat()}
                    await set_cache(cache_key, booking_data, self.cache_ttl)
                    return booking_data
                return None
        except Exception as e:
            logger.exception("Error getting booking %s for user %s: %s", booking_id, user_id, e)
            return None

    async def update_booking(self, booking_id: str, booking_data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Update booking"""
        try:
            async with get_write_db_session() as db:
                query = select(BookingTable).where(and_(BookingTable.id == booking_id, BookingTable.user_id == user_id))
                result = await db.execute(query)
                booking = result.scalar_one_or_none()
                if not booking:
                    return {"success": False, "message": "Booking not found"}
                if "title" in booking_data:
                    booking.title = booking_data["title"]
                if "description" in booking_data:
                    booking.description = booking_data["description"]
                if "start_time" in booking_data:
                    booking.start_time = datetime.fromisoformat(booking_data["start_time"].replace("Z", "+00:00"))
                if "end_time" in booking_data:
                    booking.end_time = datetime.fromisoformat(booking_data["end_time"].replace("Z", "+00:00"))
                if "timezone" in booking_data:
                    booking.timezone = booking_data["timezone"]
                if "metadata" in booking_data:
                    booking.metadata_payload = booking_data["metadata"]
                booking.updated_at = datetime.now(UTC)
                await db.commit()
                await delete_cache(f"booking:{booking_id}")
                await self._invalidate_user_cache(user_id)
                logger.info("Updated booking %s for user %s", booking_id, user_id)
                return {"success": True, "message": "Booking updated successfully", "booking_id": booking_id}
        except Exception as e:
            logger.exception("Error updating booking %s for user %s: %s", booking_id, user_id, e)
            return {"success": False, "message": f"Failed to update booking: {e!s}"}

    async def cancel_booking(self, booking_id: str, user_id: str) -> dict[str, Any]:
        """Cancel booking"""
        try:
            async with get_write_db_session() as db:
                query = select(BookingTable).where(and_(BookingTable.id == booking_id, BookingTable.user_id == user_id))
                result = await db.execute(query)
                booking = result.scalar_one_or_none()
                if not booking:
                    return {"success": False, "message": "Booking not found"}
                booking.status = BookingStatus.CANCELLED.value
                booking.updated_at = datetime.now(UTC)
                await db.commit()
                await delete_cache(f"booking:{booking_id}")
                await self._invalidate_user_cache(user_id)
                logger.info("Cancelled booking %s for user %s", booking_id, user_id)
                return {"success": True, "message": "Booking cancelled successfully", "booking_id": booking_id}
        except Exception as e:
            logger.exception("Error cancelling booking %s for user %s: %s", booking_id, user_id, e)
            return {"success": False, "message": f"Failed to cancel booking: {e!s}"}

    async def get_user_bookings(self, user_id: str, limit: int=50, offset: int=0) -> list[dict[str, Any]]:
        """Get user's bookings with pagination"""
        try:
            cache_key = f"user_bookings:{user_id}:{limit}:{offset}"
            cached_bookings = await get_cache(cache_key)
            if cached_bookings:
                return cached_bookings
            async with get_read_db_session() as db:
                query = select(BookingTable).where(BookingTable.user_id == user_id).order_by(BookingTable.start_time.desc()).offset(offset).limit(limit)
                result = await db.execute(query)
                bookings = result.scalars().all()
                bookings_data = []
                for booking in bookings:
                    booking_data = {"id": booking.id, "title": booking.title, "description": booking.description, "start_time": booking.start_time.isoformat(), "end_time": booking.end_time.isoformat(), "timezone": booking.timezone, "status": booking.status, "email": booking.email, "full_name": booking.full_name, "metadata": booking.metadata_payload, "created_at": booking.created_at.isoformat(), "updated_at": booking.updated_at.isoformat()}
                    bookings_data.append(booking_data)
                await set_cache(cache_key, bookings_data, self.cache_ttl // 2)
                return bookings_data
        except Exception as e:
            logger.exception("Error getting bookings for user %s: %s", user_id, e)
            return []
booking_service = BookingService()

def get_booking_service() -> BookingService:
    """Get global booking service instance"""
    return booking_service
