"""
Query Tools for Agent Actions

Tools for querying databases, retrieving history, and checking business rules.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from backend.utils.logger import get_logger
from .registry import register_tool, ToolCategory, ToolPriority

try:
    import sqlparse
except ImportError:
    sqlparse = None


def _is_select_only(sql: str) -> bool:
    stripped = sql.strip()
    if not stripped[:6].upper() == "SELECT":
        return False

    if sqlparse is not None:
        statements = sqlparse.parse(sql)
        if not statements:
            return False
        for stmt in statements:
            if stmt.get_type() != 'SELECT':
                return False
        return True

    forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
    upper = stripped.upper()
    return not any(keyword in upper for keyword in forbidden_keywords)


def _mask_email(email: str) -> str:
    if not isinstance(email, str) or "@" not in email:
        return "[masked]"
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"

logger = get_logger(__name__)


@register_tool(
    name="query_database",
    description="Execute a SQL query against the database",
    category=ToolCategory.QUERY,
    priority=ToolPriority.HIGH,
    examples=[
        {
            "sql": "SELECT * FROM bookings WHERE user_id = 'user_123' AND created_at > NOW() - INTERVAL '30 days'"
        }
    ]
)
async def query_database(
    sql: str,
    parameters: Optional[Dict[str, Any]] = None,
    max_rows: int = 100
) -> dict:
    """
    Execute a SQL query (read-only for safety).
    
    Args:
        sql: SQL query string
        parameters: Optional query parameters for safe interpolation
        max_rows: Maximum rows to return (safety limit)
    
    Returns:
        Dict with query results
    """
    try:
        # Safety check - only allow SELECT queries
        if not _is_select_only(sql):
            raise ValueError("Only SELECT queries are allowed.")

        logger.info(f"Executing query", extra={"query_preview": sql[:50]})
        
        # TODO: Execute query through database
        # async with get_db() as db:
        #     result = await db.execute(text(sql), parameters or {})
        #     rows = result.fetchmany(max_rows)
        
        # Demo response
        rows = []
        columns = []
        
        return {
            "success": True,
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(rows) >= max_rows,
            "executed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "sql": sql
        }


@register_tool(
    name="get_booking_history",
    description="Get booking history for a user",
    category=ToolCategory.QUERY,
    priority=ToolPriority.HIGH,
    examples=[
        {
            "user_id": "user_123",
            "limit": 10
        }
    ]
)
async def get_booking_history(
    user_id: str,
    limit: int = 10,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    """
    Get booking history for a user.
    
    Args:
        user_id: User ID
        limit: Maximum bookings to return
        status: Optional filter by status (confirmed, cancelled, pending)
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    
    Returns:
        Dict with booking history
    """
    try:
        logger.info(f"Getting booking history for user {user_id}")
        
        # TODO: Query database for user's bookings
        # Query: SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        
        # Demo history
        bookings = []
        
        return {
            "success": True,
            "user_id": user_id,
            "bookings": bookings,
            "total_count": len(bookings),
            "filters": {
                "status": status,
                "start_date": start_date,
                "end_date": end_date
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get booking history: {e}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id
        }


@register_tool(
    name="get_attendee_info",
    description="Get information about an attendee by email",
    category=ToolCategory.QUERY,
    priority=ToolPriority.HIGH,
    examples=[
        {
            "email": "john@example.com"
        }
    ]
)
async def get_attendee_info(
    email: str
) -> dict:
    """
    Get information about an attendee.
    
    Args:
        email: Attendee email address
    
    Returns:
        Dict with attendee information
    """
    try:
        logger.info("Getting info for attendee", extra={"email": _mask_email(email)})
        
        # TODO: Query user/contact database
        # Check if user exists in system
        # Get profile, preferences, history
        
        # Demo info
        info = {
            "email": email,
            "exists_in_system": True,
            "name": "John Smith",
            "timezone": "America/New_York",
            "preferences": {
                "meeting_duration": 30,
                "preferred_times": ["morning"]
            },
            "recent_meetings": [],
            "no_show_rate": 0.05,
            "average_response_time_hours": 4
        }
        
        return {
            "success": True,
            "attendee": info,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get attendee info: {e}")
        return {
            "success": False,
            "error": str(e),
            "email": email
        }


@register_tool(
    name="check_business_rules",
    description="Check if a booking complies with business rules",
    category=ToolCategory.QUERY,
    priority=ToolPriority.CRITICAL,
    examples=[
        {
            "booking": {
                "user_id": "user_123",
                "duration_minutes": 120,
                "attendee_count": 10,
                "start_time": "2024-04-15T14:00:00"
            }
        }
    ]
)
async def check_business_rules(
    booking: Dict[str, Any]
) -> dict:
    """
    Check if booking complies with business rules.
    
    Args:
        booking: Dict with booking details to validate
    
    Returns:
        Dict with validation results
    """
    try:
        logger.info(f"Checking business rules for booking")
        
        # TODO: Check various business rules
        # - Max duration
        # - Max attendees
        # - Advance booking required
        # - Room capacity
        # - Budget limits
        
        rules_checked = []
        violations = []
        warnings = []
        
        # Rule: Max duration
        max_duration = 480  # 8 hours
        duration = booking.get("duration_minutes", 0)
        if duration > max_duration:
            violations.append({
                "rule": "max_duration",
                "message": f"Duration {duration}min exceeds maximum {max_duration}min",
                "severity": "error"
            })
        rules_checked.append("max_duration")
        
        # Rule: Max attendees
        max_attendees = 50
        attendee_count = booking.get("attendee_count", 1)
        if attendee_count > max_attendees:
            violations.append({
                "rule": "max_attendees",
                "message": f"Attendees {attendee_count} exceeds maximum {max_attendees}",
                "severity": "error"
            })
        rules_checked.append("max_attendees")
        
        # Rule: Advance booking
        min_advance_hours = 2
        start_time = booking.get("start_time")
        if start_time:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            hours_until = (start - datetime.now(timezone.utc)).total_seconds() / 3600
            if hours_until < min_advance_hours:
                warnings.append({
                    "rule": "advance_booking",
                    "message": f"Booking is within {min_advance_hours} hours",
                    "severity": "warning"
                })
        rules_checked.append("advance_booking")
        
        # Rule: Working hours
        rules_checked.append("working_hours")
        
        is_valid = len([v for v in violations if v["severity"] == "error"]) == 0
        
        return {
            "success": True,
            "booking": booking,
            "is_valid": is_valid,
            "rules_checked": rules_checked,
            "violations": violations,
            "warnings": warnings,
            "compliance_score": 1.0 - (len(violations) * 0.2 + len(warnings) * 0.1),
            "checked_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to check business rules: {e}")
        return {
            "success": False,
            "error": str(e),
            "booking": booking
        }
