"""
Booking Service Layer

Extracted business logic from API endpoints:
- Booking creation and management
- Conflict detection and resolution
- Automation workflow triggering
- Cache invalidation
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from backend.models.tables import BookingTable, UserTable, EventTypeTable
from backend.core.database_replicas import get_read_db_session, get_write_db_session
from backend.utils.cache import get_cache, set_cache, delete_cache
from backend.tasks.automation_tasks import run_booking_automation_task
from backend.services.usage import increment_usage, check_usage_limit

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
    conflict_type: str  # "time_overlap", "resource_conflict", "double_booking"
    conflict_details: Dict[str, Any]
    resolution_options: List[ConflictResolution]


@dataclass
class BookingValidationResult:
    """Booking validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    conflicts: List[BookingConflict]


@dataclass
class BookingCreationResult:
    """Booking creation result"""
    success: bool
    booking_id: Optional[str]
    automation_id: Optional[str]
    conflicts: List[BookingConflict]
    warnings: List[str]
    message: str


class BookingService:
    """Booking business logic service"""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour
        self.conflict_detection_window = timedelta(hours=24)
        self.automation_enabled = True
        
    async def create_booking(self, booking_data: Dict[str, Any], user_id: str) -> BookingCreationResult:
        """Create booking with comprehensive business logic"""
        try:
            # Validate booking data
            validation_result = await self._validate_booking_data(booking_data, user_id)
            if not validation_result.is_valid:
                return BookingCreationResult(
                    success=False,
                    booking_id=None,
                    automation_id=None,
                    conflicts=[],
                    warnings=validation_result.warnings,
                    message=f"Validation failed: {', '.join(validation_result.errors)}"
                )
            
            # Check for conflicts
            conflicts = await self._detect_conflicts(booking_data, user_id)
            
            # Handle conflicts based on strategy
            if conflicts:
                resolution = await self._resolve_conflicts(conflicts, booking_data, user_id)
                if not resolution["resolved"]:
                    return BookingCreationResult(
                        success=False,
                        booking_id=None,
                        automation_id=None,
                        conflicts=conflicts,
                        warnings=validation_result.warnings,
                        message=f"Unresolved conflicts: {resolution['message']}"
                    )
            
            # Create booking in database
            booking = await self._persist_booking(booking_data, user_id)
            
            # Invalidate cache
            await self._invalidate_user_cache(user_id)
            
            # Trigger automation
            automation_id = await self._trigger_automation(booking, user_id)
            
            # Update usage metrics
            await self._update_usage_metrics(user_id)
            
            return BookingCreationResult(
                success=True,
                booking_id=booking.id,
                automation_id=automation_id,
                conflicts=conflicts,
                warnings=validation_result.warnings,
                message="Booking created successfully"
            )
            
        except Exception as e:
            logger.error(f"Error creating booking for user {user_id}: {e}")
            return BookingCreationResult(
                success=False,
                booking_id=None,
                automation_id=None,
                conflicts=[],
                warnings=[],
                message=f"Failed to create booking: {str(e)}"
            )
    
    async def _validate_booking_data(self, booking_data: Dict[str, Any], user_id: str) -> BookingValidationResult:
        """Validate booking data"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["title", "start_time", "end_time"]
        for field in required_fields:
            if not booking_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Time validation
        start_time = booking_data.get("start_time")
        end_time = booking_data.get("end_time")
        
        if start_time and end_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if start_time >= end_time:
                errors.append("Start time must be before end time")
            
            if start_time < datetime.now(timezone.utc):
                errors.append("Start time cannot be in the past")
            
            # Check if booking is too far in future
            if start_time > datetime.now(timezone.utc) + timedelta(days=365):
                warnings.append("Booking is more than 1 year in the future")
            
            # Check duration
            duration = end_time - start_time
            if duration > timedelta(hours=8):
                warnings.append("Booking duration exceeds 8 hours")
            elif duration < timedelta(minutes=15):
                errors.append("Booking duration must be at least 15 minutes")
        
        # User quota check
        if not await self._check_user_quota(user_id):
            errors.append("User quota exceeded for bookings")
        
        return BookingValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            conflicts=[]
        )
    
    async def _detect_conflicts(self, booking_data: Dict[str, Any], user_id: str) -> List[BookingConflict]:
        """Detect booking conflicts"""
        conflicts = []
        
        start_time = booking_data.get("start_time")
        end_time = booking_data.get("end_time")
        
        if not start_time or not end_time:
            return conflicts
        
        # Convert to datetime objects if needed
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        async with get_read_db_session() as db:
            # Check time conflicts with user's existing bookings
            query = select(BookingTable).where(
                and_(
                    BookingTable.user_id == user_id,
                    BookingTable.status.in_([BookingStatus.SCHEDULED.value, BookingStatus.CONFIRMED.value]),
                    or_(
                        and_(BookingTable.start_time <= start_time, BookingTable.end_time > start_time),
                        and_(BookingTable.start_time < end_time, BookingTable.end_time >= end_time),
                        and_(BookingTable.start_time >= start_time, BookingTable.end_time <= end_time)
                    )
                )
            )
            
            result = await db.execute(query)
            existing_bookings = result.scalars().all()
            
            for existing_booking in existing_bookings:
                conflict = BookingConflict(
                    existing_booking_id=existing_booking.id,
                    conflict_type="time_overlap",
                    conflict_details={
                        "existing_start": existing_booking.start_time.isoformat(),
                        "existing_end": existing_booking.end_time.isoformat(),
                        "existing_title": existing_booking.title
                    },
                    resolution_options=[ConflictResolution.RESCHEDULE, ConflictResolution.REJECT]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    async def _resolve_conflicts(self, conflicts: List[BookingConflict], 
                               booking_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Resolve booking conflicts"""
        for conflict in conflicts:
            if conflict.conflict_type == "time_overlap":
                # Try to find alternative time slots
                alternatives = await self._find_alternative_slots(booking_data, user_id)
                if alternatives:
                    return {
                        "resolved": True,
                        "message": "Alternative time slots available",
                        "alternatives": alternatives
                    }
                else:
                    return {
                        "resolved": False,
                        "message": "No alternative time slots available"
                    }
        
        return {"resolved": True, "message": "No conflicts to resolve"}
    
    async def _find_alternative_slots(self, booking_data: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Find alternative time slots for conflicted booking"""
        alternatives = []
        start_time = booking_data.get("start_time")
        end_time = booking_data.get("end_time")
        
        if not start_time or not end_time:
            return alternatives
        
        # Convert to datetime objects if needed
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        duration = end_time - start_time
        
        # Look for slots in the next 7 days
        for days_ahead in range(1, 8):
            candidate_start = start_time + timedelta(days=days_ahead)
            candidate_end = candidate_start + duration
            
            # Skip weekends if preferred
            if candidate_start.weekday() >= 5:  # Saturday or Sunday
                continue
            
            # Check if slot is available
            if await self._is_slot_available(candidate_start, candidate_end, user_id):
                alternatives.append({
                    "start_time": candidate_start.isoformat(),
                    "end_time": candidate_end.isoformat(),
                    "days_ahead": days_ahead
                })
                
                # Limit alternatives to 3 options
                if len(alternatives) >= 3:
                    break
        
        return alternatives
    
    async def _is_slot_available(self, start_time: datetime, end_time: datetime, user_id: str) -> bool:
        """Check if time slot is available"""
        async with get_read_db_session() as db:
            query = select(BookingTable).where(
                and_(
                    BookingTable.user_id == user_id,
                    BookingTable.status.in_([BookingStatus.SCHEDULED.value, BookingStatus.CONFIRMED.value]),
                    or_(
                        and_(BookingTable.start_time <= start_time, BookingTable.end_time > start_time),
                        and_(BookingTable.start_time < end_time, BookingTable.end_time >= end_time),
                        and_(BookingTable.start_time >= start_time, BookingTable.end_time <= end_time)
                    )
                )
            )
            
            result = await db.execute(query)
            conflicts = result.scalars().all()
            
            return len(conflicts) == 0
    
    async def _persist_booking(self, booking_data: Dict[str, Any], user_id: str) -> BookingTable:
        """Persist booking to database"""
        async with get_write_db_session() as db:
            # Convert string times to datetime objects
            start_time = booking_data.get("start_time")
            end_time = booking_data.get("end_time")
            
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Create booking record
            booking = BookingTable(
                title=booking_data.get("title"),
                description=booking_data.get("description"),
                start_time=start_time,
                end_time=end_time,
                user_id=user_id,
                timezone=booking_data.get("timezone", "UTC"),
                status=BookingStatus.SCHEDULED.value,
                metadata_payload=booking_data.get("metadata", {}),
                email=booking_data.get("email"),
                full_name=booking_data.get("full_name"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.add(booking)
            await db.flush()
            await db.refresh(booking)
            
            logger.info(f"Created booking {booking.id} for user {user_id}")
            return booking
    
    async def _invalidate_user_cache(self, user_id: str):
        """Invalidate user-related cache entries"""
        try:
            # Invalidate calendar cache
            await delete_cache(f"user_calendar:{user_id}")
            
            # Invalidate booking cache
            await delete_cache(f"user_bookings:{user_id}")
            
            # Invalidate user preferences cache
            await delete_cache(f"user_preferences:{user_id}")
            
            logger.info(f"Invalidated cache for user {user_id[:8]}...")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for user {user_id}: {e}")
    
    async def _trigger_automation(self, booking: BookingTable, user_id: str) -> Optional[str]:
        """Trigger automation workflow for booking"""
        if not self.automation_enabled:
            return None
        
        try:
            # Build attendee data
            attendee_data = None
            if booking.metadata_payload and "attendees" in booking.metadata_payload:
                attendees = booking.metadata_payload.get("attendees")
                if attendees and isinstance(attendees, list) and len(attendees) > 0:
                    attendee_email = attendees[0]
                else:
                    attendee_email = booking.email
                
                attendee_data = {
                    "email": attendee_email,
                    "name": booking.full_name,
                }
            
            # Trigger Celery task
            task = run_booking_automation_task.delay(
                booking_id=booking.id,
                automation_id=None,  # Will be generated
                user_id=user_id,
                attendee_data=attendee_data,
                booking_data={
                    "title": booking.title,
                    "description": booking.description,
                    "start_time": booking.start_time.isoformat(),
                    "end_time": booking.end_time.isoformat(),
                    "timezone": booking.timezone
                }
            )
            
            logger.info(f"Triggered automation task {task.id} for booking {booking.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to trigger automation for booking {booking.id}: {e}")
            return None
    
    async def _update_usage_metrics(self, user_id: str):
        """Update usage metrics for user"""
        try:
            await increment_usage(user_id, "daily_bookings")
            await increment_usage(user_id, "total_scheduling_count")
            logger.info(f"Updated usage metrics for user {user_id[:8]}...")
        except Exception as e:
            logger.error(f"Failed to update usage metrics for user {user_id}: {e}")
    
    async def _check_user_quota(self, user_id: str) -> bool:
        """Check if user has quota for creating bookings"""
        try:
            # This would check against user's subscription limits
            # For now, return True (no quota limit)
            return True
        except Exception as e:
            logger.error(f"Failed to check quota for user {user_id}: {e}")
            return True  # Allow booking on quota check failure
    
    async def get_booking(self, booking_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get booking by ID for user"""
        try:
            # Try cache first
            cache_key = f"booking:{booking_id}"
            cached_booking = await get_cache(cache_key)
            if cached_booking:
                return cached_booking
            
            async with get_read_db_session() as db:
                query = select(BookingTable).where(
                    and_(
                        BookingTable.id == booking_id,
                        BookingTable.user_id == user_id
                    )
                )
                
                result = await db.execute(query)
                booking = result.scalar_one_or_none()
                
                if booking:
                    booking_data = {
                        "id": booking.id,
                        "title": booking.title,
                        "description": booking.description,
                        "start_time": booking.start_time.isoformat(),
                        "end_time": booking.end_time.isoformat(),
                        "timezone": booking.timezone,
                        "status": booking.status,
                        "email": booking.email,
                        "full_name": booking.full_name,
                        "metadata": booking.metadata_payload,
                        "created_at": booking.created_at.isoformat(),
                        "updated_at": booking.updated_at.isoformat()
                    }
                    
                    # Cache the result
                    await set_cache(cache_key, booking_data, self.cache_ttl)
                    
                    return booking_data
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting booking {booking_id} for user {user_id}: {e}")
            return None
    
    async def update_booking(self, booking_id: str, booking_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update booking"""
        try:
            async with get_write_db_session() as db:
                # Get existing booking
                query = select(BookingTable).where(
                    and_(
                        BookingTable.id == booking_id,
                        BookingTable.user_id == user_id
                    )
                )
                
                result = await db.execute(query)
                booking = result.scalar_one_or_none()
                
                if not booking:
                    return {"success": False, "message": "Booking not found"}
                
                # Update booking fields
                if "title" in booking_data:
                    booking.title = booking_data["title"]
                if "description" in booking_data:
                    booking.description = booking_data["description"]
                if "start_time" in booking_data:
                    booking.start_time = datetime.fromisoformat(booking_data["start_time"].replace('Z', '+00:00'))
                if "end_time" in booking_data:
                    booking.end_time = datetime.fromisoformat(booking_data["end_time"].replace('Z', '+00:00'))
                if "timezone" in booking_data:
                    booking.timezone = booking_data["timezone"]
                if "metadata" in booking_data:
                    booking.metadata_payload = booking_data["metadata"]
                
                booking.updated_at = datetime.now(timezone.utc)
                
                await db.commit()
                
                # Invalidate cache
                await delete_cache(f"booking:{booking_id}")
                await self._invalidate_user_cache(user_id)
                
                logger.info(f"Updated booking {booking_id} for user {user_id}")
                
                return {
                    "success": True,
                    "message": "Booking updated successfully",
                    "booking_id": booking_id
                }
                
        except Exception as e:
            logger.error(f"Error updating booking {booking_id} for user {user_id}: {e}")
            return {"success": False, "message": f"Failed to update booking: {str(e)}"}
    
    async def cancel_booking(self, booking_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel booking"""
        try:
            async with get_write_db_session() as db:
                # Get existing booking
                query = select(BookingTable).where(
                    and_(
                        BookingTable.id == booking_id,
                        BookingTable.user_id == user_id
                    )
                )
                
                result = await db.execute(query)
                booking = result.scalar_one_or_none()
                
                if not booking:
                    return {"success": False, "message": "Booking not found"}
                
                # Update status to cancelled
                booking.status = BookingStatus.CANCELLED.value
                booking.updated_at = datetime.now(timezone.utc)
                
                await db.commit()
                
                # Invalidate cache
                await delete_cache(f"booking:{booking_id}")
                await self._invalidate_user_cache(user_id)
                
                logger.info(f"Cancelled booking {booking_id} for user {user_id}")
                
                return {
                    "success": True,
                    "message": "Booking cancelled successfully",
                    "booking_id": booking_id
                }
                
        except Exception as e:
            logger.error(f"Error cancelling booking {booking_id} for user {user_id}: {e}")
            return {"success": False, "message": f"Failed to cancel booking: {str(e)}"}
    
    async def get_user_bookings(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's bookings with pagination"""
        try:
            # Try cache first
            cache_key = f"user_bookings:{user_id}:{limit}:{offset}"
            cached_bookings = await get_cache(cache_key)
            if cached_bookings:
                return cached_bookings
            
            async with get_read_db_session() as db:
                query = select(BookingTable).where(
                    BookingTable.user_id == user_id
                ).order_by(BookingTable.start_time.desc()).offset(offset).limit(limit)
                
                result = await db.execute(query)
                bookings = result.scalars().all()
                
                bookings_data = []
                for booking in bookings:
                    booking_data = {
                        "id": booking.id,
                        "title": booking.title,
                        "description": booking.description,
                        "start_time": booking.start_time.isoformat(),
                        "end_time": booking.end_time.isoformat(),
                        "timezone": booking.timezone,
                        "status": booking.status,
                        "email": booking.email,
                        "full_name": booking.full_name,
                        "metadata": booking.metadata_payload,
                        "created_at": booking.created_at.isoformat(),
                        "updated_at": booking.updated_at.isoformat()
                    }
                    bookings_data.append(booking_data)
                
                # Cache the result
                await set_cache(cache_key, bookings_data, self.cache_ttl // 2)  # Shorter cache for list
                
                return bookings_data
                
        except Exception as e:
            logger.error(f"Error getting bookings for user {user_id}: {e}")
            return []


# Global booking service instance
booking_service = BookingService()


def get_booking_service() -> BookingService:
    """Get global booking service instance"""
    return booking_service
