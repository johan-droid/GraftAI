"""API routes for email template management.

This module provides endpoints for:
- Listing and retrieving email templates
- Creating and updating custom templates
- Rendering templates with variables
- Sending test emails
- Email analytics and statistics
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.models.email_template import EmailTemplate
from backend.services.email_template_service import EmailTemplateService

router = APIRouter(prefix="/email-templates", tags=["email-templates"])


def _is_admin(user: UserTable) -> bool:
    tier = (getattr(user, "tier", "") or "").strip().lower()
    if tier in {"admin", "elite"}:
        return True

    preferences = getattr(user, "preferences", None)
    if isinstance(preferences, dict):
        role = str(preferences.get("role", "")).strip().lower()
        if role in {"admin", "elite", "owner"}:
            return True

    return False


# Pydantic Models


class EmailTemplateListItem(BaseModel):
    """Email template list item response."""

    id: str
    name: str
    slug: str
    description: Optional[str]
    is_system: bool
    subject: str
    is_active: bool
    language: str
    created_at: str
    updated_at: str


class EmailTemplateDetail(BaseModel):
    """Detailed email template response."""

    id: str
    name: str
    slug: str
    description: Optional[str]
    is_system: bool
    subject: str
    html_body: str
    text_body: str
    available_variables: List[str]
    primary_color: str
    is_active: bool
    language: str
    created_at: str
    updated_at: str


class EmailTemplateCreate(BaseModel):
    """Create email template request."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9_]+$")
    description: Optional[str] = Field(None, max_length=500)
    subject: str = Field(..., min_length=1, max_length=500)
    html_body: str = Field(..., min_length=1)
    text_body: Optional[str] = None
    available_variables: List[str] = Field(default_factory=list)
    primary_color: str = Field(default="#6366f1", pattern="^#[0-9a-fA-F]{6}$")
    language: str = Field(default="en", pattern="^[a-z]{2}$")


class EmailTemplateUpdate(BaseModel):
    """Update email template request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    html_body: Optional[str] = Field(None, min_length=1)
    text_body: Optional[str] = None
    available_variables: Optional[List[str]] = None
    primary_color: Optional[str] = Field(None, pattern="^#[0-9a-fA-F]{6}$")
    is_active: Optional[bool] = None


class RenderTemplateRequest(BaseModel):
    """Render template request."""

    variables: Dict[str, str] = Field(default_factory=dict)


class RenderTemplateResponse(BaseModel):
    """Rendered template response."""

    subject: str
    html_body: str
    text_body: str


class SendTestEmailRequest(BaseModel):
    """Send test email request."""

    to_email: str = Field(
        ..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    variables: Dict[str, str] = Field(default_factory=dict)


class EmailStatsResponse(BaseModel):
    """Email statistics response."""

    total: int
    sent: int
    delivered: int
    opened: int
    failed: int
    open_rate: float
    period_days: int


# Routes


@router.get("/", response_model=List[EmailTemplateListItem])
async def list_templates(
    include_system: bool = Query(default=True, description="Include system templates"),
    language: str = Query(default="en", description="Language code"),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """List all email templates available to the user.

    Returns both system templates and user-specific templates.
    User templates override system templates with the same slug.
    """
    service = EmailTemplateService(db)

    # Get user templates
    stmt = select(EmailTemplate).where(
        and_(
            EmailTemplate.user_id == current_user.id, EmailTemplate.language == language
        )
    )
    user_templates = (await db.execute(stmt)).scalars().all()

    # Get system templates
    if include_system:
        stmt = select(EmailTemplate).where(
            and_(EmailTemplate.is_system == True, EmailTemplate.language == language)
        )
        system_templates = (await db.execute(stmt)).scalars().all()

        # Filter out system templates that have user overrides
        user_slugs = {t.slug for t in user_templates}
        templates = list(user_templates) + [
            t for t in system_templates if t.slug not in user_slugs
        ]
    else:
        templates = list(user_templates)

    # Sort by name
    templates.sort(key=lambda t: t.name)

    return [
        EmailTemplateListItem(
            id=t.id,
            name=t.name,
            slug=t.slug,
            description=t.description,
            is_system=t.is_system,
            subject=t.subject,
            is_active=t.is_active,
            language=t.language,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=EmailTemplateDetail)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get detailed information about a specific template."""
    stmt = select(EmailTemplate).where(
        and_(
            EmailTemplate.id == template_id,
            EmailTemplate.is_system == False,
            EmailTemplate.user_id == current_user.id,
        )
    )
    template = (await db.execute(stmt)).scalars().first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return EmailTemplateDetail(
        id=template.id,
        name=template.name,
        slug=template.slug,
        description=template.description,
        is_system=template.is_system,
        subject=template.subject,
        html_body=template.html_body,
        text_body=template.text_body,
        available_variables=template.available_variables,
        primary_color=template.primary_color,
        is_active=template.is_active,
        language=template.language,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat(),
    )


@router.post("/", response_model=EmailTemplateDetail)
async def create_template(
    template: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Create a new custom email template.

    User templates can override system templates by using the same slug.
    """
    # Check for duplicate slug
    stmt = select(EmailTemplate).where(
        and_(
            EmailTemplate.slug == template.slug,
            EmailTemplate.user_id == current_user.id,
        )
    )
    existing = (await db.execute(stmt)).scalars().first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Template with slug '{template.slug}' already exists",
        )

    # Generate text body if not provided
    service = EmailTemplateService(db)
    text_body = template.text_body or service._html_to_text(template.html_body)

    new_template = EmailTemplate(
        user_id=current_user.id,
        name=template.name,
        slug=template.slug,
        description=template.description,
        is_system=False,
        subject=template.subject,
        html_body=template.html_body,
        text_body=text_body,
        available_variables=template.available_variables,
        primary_color=template.primary_color,
        language=template.language,
    )

    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    return EmailTemplateDetail(
        id=new_template.id,
        name=new_template.name,
        slug=new_template.slug,
        description=new_template.description,
        is_system=new_template.is_system,
        subject=new_template.subject,
        html_body=new_template.html_body,
        text_body=new_template.text_body,
        available_variables=new_template.available_variables,
        primary_color=new_template.primary_color,
        is_active=new_template.is_active,
        language=new_template.language,
        created_at=new_template.created_at.isoformat(),
        updated_at=new_template.updated_at.isoformat(),
    )


@router.put("/{template_id}", response_model=EmailTemplateDetail)
async def update_template(
    template_id: str,
    update: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Update a custom email template.

    System templates cannot be modified. Create a custom template
    with the same slug to override system templates.
    """
    stmt = select(EmailTemplate).where(
        and_(
            EmailTemplate.id == template_id,
            EmailTemplate.user_id == current_user.id,
            EmailTemplate.is_system == False,
        )
    )
    template = (await db.execute(stmt)).scalars().first()

    if not template:
        raise HTTPException(
            status_code=404, detail="Template not found or cannot be modified"
        )

    # Update fields
    if update.name is not None:
        template.name = update.name
    if update.description is not None:
        template.description = update.description
    if update.subject is not None:
        template.subject = update.subject
    if update.html_body is not None:
        template.html_body = update.html_body
        # Regenerate text body if HTML changed
        if update.text_body is None:
            service = EmailTemplateService(db)
            template.text_body = service._html_to_text(update.html_body)
    if update.text_body is not None:
        template.text_body = update.text_body
    if update.available_variables is not None:
        template.available_variables = update.available_variables
    if update.primary_color is not None:
        template.primary_color = update.primary_color
    if update.is_active is not None:
        template.is_active = update.is_active

    await db.commit()
    await db.refresh(template)

    return EmailTemplateDetail(
        id=template.id,
        name=template.name,
        slug=template.slug,
        description=template.description,
        is_system=template.is_system,
        subject=template.subject,
        html_body=template.html_body,
        text_body=template.text_body,
        available_variables=template.available_variables,
        primary_color=template.primary_color,
        is_active=template.is_active,
        language=template.language,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat(),
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Delete a custom email template.

    System templates cannot be deleted.
    """
    stmt = select(EmailTemplate).where(
        and_(
            EmailTemplate.id == template_id,
            EmailTemplate.user_id == current_user.id,
            EmailTemplate.is_system == False,
        )
    )
    template = (await db.execute(stmt)).scalars().first()

    if not template:
        raise HTTPException(
            status_code=404, detail="Template not found or cannot be deleted"
        )

    await db.delete(template)
    await db.commit()

    return {"status": "success", "message": "Template deleted"}


@router.post("/{template_id}/render", response_model=RenderTemplateResponse)
async def render_template(
    template_id: str,
    request: RenderTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Render a template with variables and return the result.

    This is useful for previewing templates before sending.
    """
    service = EmailTemplateService(db)

    # Get template (user or system)
    template = await service.get_template(slug=template_id, user_id=current_user.id)

    if not template:
        # Try by ID for user templates
        stmt = select(EmailTemplate).where(
            and_(
                EmailTemplate.id == template_id,
                EmailTemplate.user_id == current_user.id,
            )
        )
        template = (await db.execute(stmt)).scalars().first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        subject, html_body, text_body = service.render_template(
            template=template, variables=request.variables
        )

        return RenderTemplateResponse(
            subject=subject, html_body=html_body, text_body=text_body
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Template rendering failed: {str(e)}"
        )


@router.post("/{template_id}/send-test")
async def send_test_email(
    template_id: str,
    request: SendTestEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Send a test email using a template.

    The email will be sent to the specified address with the
    provided variables substituted into the template.
    """
    service = EmailTemplateService(db)

    # Get template
    template = await service.get_template(slug=template_id, user_id=current_user.id)

    if not template:
        stmt = select(EmailTemplate).where(
            and_(
                EmailTemplate.id == template_id,
                EmailTemplate.user_id == current_user.id,
            )
        )
        template = (await db.execute(stmt)).scalars().first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Add default variables
    variables = {
        "user_name": current_user.full_name or "Test User",
        **request.variables,
    }

    try:
        subject, html_body, text_body = service.render_template(
            template=template, variables=variables
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Template rendering failed: {str(e)}"
        )

    # Send email
    log = await service.send_email(
        to_email=request.to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        template_id=template.id,
        user_id=current_user.id,
    )

    return {
        "status": "sent",
        "log_id": log.id,
        "to": request.to_email,
        "subject": subject,
    }


@router.get("/stats/overview", response_model=EmailStatsResponse)
async def get_email_stats(
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to analyze"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get email sending statistics for the current user."""
    service = EmailTemplateService(db)
    stats = await service.get_email_stats(user_id=current_user.id, days=days)

    return EmailStatsResponse(**stats)


@router.get("/system/initialize")
async def initialize_system_templates(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Initialize default system email templates.

    This endpoint is primarily for admin use. System templates
    are created automatically when needed.
    """
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    service = EmailTemplateService(db)
    await service.initialize_system_templates()

    return {"status": "success", "message": "System templates initialized"}
