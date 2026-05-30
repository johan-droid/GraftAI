"""
CRM Tools for Agent Actions

Tools for managing contacts, tasks, and CRM operations.
"""
from datetime import UTC, datetime
from typing import Any

from backend.utils.logger import get_logger

from .registry import ToolCategory, ToolPriority, register_tool

logger = get_logger(__name__)

@register_tool(name="create_contact", description="Create a new contact in the CRM system", category=ToolCategory.CRM, priority=ToolPriority.HIGH, examples=[{"name": "John Smith", "email": "john@example.com", "details": {"phone": "+1234567890", "company": "Acme Corp", "title": "VP of Engineering"}}])
async def create_contact(name: str, email: str, details: dict[str, Any] | None=None, tags: list[str] | None=None) -> dict:
    """
    Create a new contact in CRM.

    Args:
        name: Contact full name
        email: Contact email address
        details: Optional dict with phone, company, title, notes, etc.
        tags: Optional list of tags

    Returns:
        Dict with contact_id and details
    """
    try:
        contact_id = f"contact_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        logger.info("Creating contact: %s (%s)", name, email)
        return {"success": True, "contact_id": contact_id, "name": name, "email": email, "details": details or {}, "tags": tags or [], "created_at": datetime.now(UTC).isoformat(), "crm_link": f"https://crm.example.com/contacts/{contact_id}"}
    except Exception as e:
        logger.exception("Failed to create contact: %s", e)
        return {"success": False, "error": str(e), "name": name, "email": email}

@register_tool(name="update_contact", description="Update an existing contact in the CRM", category=ToolCategory.CRM, priority=ToolPriority.HIGH, examples=[{"id": "contact_123", "changes": {"company": "New Company Inc", "title": "CTO"}}])
async def update_contact(id: str, changes: dict[str, Any]) -> dict:
    """
    Update an existing contact.

    Args:
        id: Contact ID
        changes: Dict of fields to update

    Returns:
        Dict with update status
    """
    try:
        logger.info("Updating contact %s: %s", id, changes)
        return {"success": True, "contact_id": id, "changes": changes, "updated_at": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Failed to update contact: %s", e)
        return {"success": False, "error": str(e), "contact_id": id}

@register_tool(name="create_task", description="Create a task in the CRM for follow-up or action items", category=ToolCategory.CRM, priority=ToolPriority.HIGH, examples=[{"title": "Follow up with VIP client", "due_date": "2024-04-16T10:00:00", "owner": "sales@company.com", "priority": "high", "related_to": "contact_123"}])
async def create_task(title: str, due_date: str, owner: str, priority: str="medium", related_to: str | None=None, description: str | None=None, task_type: str="follow_up") -> dict:
    """
    Create a CRM task.

    Args:
        title: Task title
        due_date: Due date/time (ISO format)
        owner: Task owner email/ID
        priority: Task priority (low, medium, high, critical)
        related_to: Optional related contact/booking ID
        description: Optional task description
        task_type: Task type (follow_up, call, email, meeting, etc.)

    Returns:
        Dict with task_id and details
    """
    try:
        task_id = f"task_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        logger.info("Creating task: %s (due: %s)", title, due_date)
        return {"success": True, "task_id": task_id, "title": title, "due_date": due_date, "owner": owner, "priority": priority, "related_to": related_to, "task_type": task_type, "created_at": datetime.now(UTC).isoformat(), "crm_link": f"https://crm.example.com/tasks/{task_id}"}
    except Exception as e:
        logger.exception("Failed to create task: %s", e)
        return {"success": False, "error": str(e), "title": title}

@register_tool(name="query_contacts", description="Query contacts in the CRM with filters", category=ToolCategory.CRM, priority=ToolPriority.MEDIUM, examples=[{"filters": {"company": "Acme Corp", "tags": ["vip", "enterprise"]}}])
async def query_contacts(filters: dict[str, Any], limit: int=10) -> dict:
    """
    Query contacts with filters.

    Args:
        filters: Dict with filter criteria (name, email, company, tags, etc.)
        limit: Max results to return

    Returns:
        Dict with matching contacts
    """
    try:
        logger.info("Querying contacts with filters: %s", filters)
        contacts = []
        return {"success": True, "filters": filters, "contacts": contacts, "total": len(contacts), "limit": limit, "queried_at": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Failed to query contacts: %s", e)
        return {"success": False, "error": str(e), "filters": filters}

@register_tool(name="get_contact_history", description="Get interaction history for a contact", category=ToolCategory.CRM, priority=ToolPriority.MEDIUM, examples=[{"id": "contact_123"}])
async def get_contact_history(id: str, start_date: str | None=None, end_date: str | None=None) -> dict:
    """
    Get interaction history for a contact.

    Args:
        id: Contact ID
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Dict with contact history
    """
    try:
        logger.info("Getting history for contact %s", id)
        history = {"meetings": [], "emails": [], "tasks": [], "notes": []}
        return {"success": True, "contact_id": id, "history": history, "total_interactions": sum(len(v) for v in history.values()), "queried_at": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.exception("Failed to get contact history: %s", e)
        return {"success": False, "error": str(e), "contact_id": id}
