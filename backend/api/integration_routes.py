"""Integration management routes for Zapier, Slack, Teams."""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.models.integration import Integration, IntegrationLog
from backend.services.integrations.webhook_service import (
    WebhookService,
    WebhookPayload,
    WebhookEventType,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


# Pydantic Models


class IntegrationCreate(BaseModel):
    provider: str = Field(..., pattern="^(zapier|slack|teams|custom)$")
    name: str = Field(..., min_length=1, max_length=100)
    webhook_url: HttpUrl
    events: List[str] = Field(default=["booking.created", "booking.updated"])
    config: Optional[dict] = None


class IntegrationResponse(BaseModel):
    id: str
    provider: str
    name: str
    webhook_url: str
    events: List[str]
    is_active: bool
    created_at: str
    last_success_at: Optional[str] = None
    last_error_at: Optional[str] = None


class IntegrationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    webhook_url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    config: Optional[dict] = None


class IntegrationLogResponse(BaseModel):
    id: str
    event_type: str
    status: str
    status_code: Optional[int]
    error_message: Optional[str]
    sent_at: str
    response_time_ms: Optional[int]


class TestWebhookRequest(BaseModel):
    event_type: str = "booking.created"
    payload: Optional[dict] = None


# Routes


@router.post("/", response_model=IntegrationResponse)
async def create_integration(
    integration: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Create a new integration (Zapier, Slack, Teams)."""

    new_integration = Integration(
        user_id=current_user.id,
        provider=integration.provider,
        name=integration.name,
        webhook_url=str(integration.webhook_url),
        events=integration.events,
        config=integration.config or {},
    )

    db.add(new_integration)
    await db.commit()
    await db.refresh(new_integration)

    return IntegrationResponse(
        id=new_integration.id,
        provider=new_integration.provider,
        name=new_integration.name,
        webhook_url=new_integration.webhook_url,
        events=new_integration.events,
        is_active=new_integration.is_active,
        created_at=new_integration.created_at.isoformat(),
        last_success_at=new_integration.last_success_at.isoformat()
        if new_integration.last_success_at
        else None,
        last_error_at=new_integration.last_error_at.isoformat()
        if new_integration.last_error_at
        else None,
    )


@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """List all integrations for the current user."""

    stmt = select(Integration).where(Integration.user_id == current_user.id)

    if provider:
        stmt = stmt.where(Integration.provider == provider)

    stmt = stmt.order_by(desc(Integration.created_at))
    integrations = (await db.execute(stmt)).scalars().all()

    return [
        IntegrationResponse(
            id=i.id,
            provider=i.provider,
            name=i.name,
            webhook_url=i.webhook_url,
            events=i.events,
            is_active=i.is_active,
            created_at=i.created_at.isoformat(),
            last_success_at=i.last_success_at.isoformat()
            if i.last_success_at
            else None,
            last_error_at=i.last_error_at.isoformat() if i.last_error_at else None,
        )
        for i in integrations
    ]


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get details of a specific integration."""

    stmt = select(Integration).where(
        and_(Integration.id == integration_id, Integration.user_id == current_user.id)
    )
    integration = (await db.execute(stmt)).scalars().first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    return IntegrationResponse(
        id=integration.id,
        provider=integration.provider,
        name=integration.name,
        webhook_url=integration.webhook_url,
        events=integration.events,
        is_active=integration.is_active,
        created_at=integration.created_at.isoformat(),
        last_success_at=integration.last_success_at.isoformat()
        if integration.last_success_at
        else None,
        last_error_at=integration.last_error_at.isoformat()
        if integration.last_error_at
        else None,
    )


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    update: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Update an integration."""

    stmt = select(Integration).where(
        and_(Integration.id == integration_id, Integration.user_id == current_user.id)
    )
    integration = (await db.execute(stmt)).scalars().first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if update.name is not None:
        integration.name = update.name
    if update.webhook_url is not None:
        integration.webhook_url = str(update.webhook_url)
    if update.events is not None:
        integration.events = update.events
    if update.is_active is not None:
        integration.is_active = update.is_active
    if update.config is not None:
        integration.config = update.config

    integration.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(integration)

    return IntegrationResponse(
        id=integration.id,
        provider=integration.provider,
        name=integration.name,
        webhook_url=integration.webhook_url,
        events=integration.events,
        is_active=integration.is_active,
        created_at=integration.created_at.isoformat(),
        last_success_at=integration.last_success_at.isoformat()
        if integration.last_success_at
        else None,
        last_error_at=integration.last_error_at.isoformat()
        if integration.last_error_at
        else None,
    )


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Delete an integration."""

    stmt = select(Integration).where(
        and_(Integration.id == integration_id, Integration.user_id == current_user.id)
    )
    integration = (await db.execute(stmt)).scalars().first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    await db.delete(integration)
    await db.commit()

    return {"status": "success", "message": "Integration deleted"}


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    test_request: TestWebhookRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Send a test webhook to an integration."""

    stmt = select(Integration).where(
        and_(Integration.id == integration_id, Integration.user_id == current_user.id)
    )
    integration = (await db.execute(stmt)).scalars().first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Build test payload
    payload = WebhookPayload(
        event_type=WebhookEventType(test_request.event_type),
        data=test_request.payload
        or {
            "test": True,
            "message": "This is a test webhook from GraftAI",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ).build()

    # Send webhook
    webhook_service = WebhookService()
    result = await webhook_service.send_webhook(
        url=integration.webhook_url, payload=payload, provider=integration.provider
    )

    # Log the test
    log = IntegrationLog(
        integration_id=integration_id,
        event_type=test_request.event_type,
        payload=payload,
        status="success" if result["success"] else "failed",
        status_code=result.get("status_code"),
        error_message=result.get("error") or result.get("response_body"),
        response_time_ms=None,
    )
    db.add(log)
    await db.commit()

    # Update integration status
    if result["success"]:
        integration.last_success_at = datetime.now(timezone.utc)
    else:
        integration.last_error_at = datetime.now(timezone.utc)
        integration.last_error_message = result.get("error") or result.get(
            "response_body"
        )

    await db.commit()

    return {
        "success": result["success"],
        "status_code": result.get("status_code"),
        "message": "Test webhook sent successfully"
        if result["success"]
        else f"Failed: {result.get('error', 'Unknown error')}",
    }


@router.get("/{integration_id}/logs", response_model=List[IntegrationLogResponse])
async def get_integration_logs(
    integration_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Get webhook delivery logs for an integration."""

    # Verify ownership
    stmt = select(Integration).where(
        and_(Integration.id == integration_id, Integration.user_id == current_user.id)
    )
    integration = (await db.execute(stmt)).scalars().first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Get logs
    stmt = (
        select(IntegrationLog)
        .where(IntegrationLog.integration_id == integration_id)
        .order_by(desc(IntegrationLog.sent_at))
        .limit(limit)
    )

    logs = (await db.execute(stmt)).scalars().all()

    return [
        IntegrationLogResponse(
            id=log.id,
            event_type=log.event_type,
            status=log.status,
            status_code=log.status_code,
            error_message=log.error_message,
            sent_at=log.sent_at.isoformat(),
            response_time_ms=log.response_time_ms,
        )
        for log in logs
    ]


@router.get("/providers/available")
async def get_available_providers():
    """Get list of available integration providers."""
    return {
        "providers": [
            {
                "id": "zapier",
                "name": "Zapier",
                "description": "Connect with 5000+ apps via Zapier",
                "icon": "zapier",
                "events": [
                    "booking.created",
                    "booking.updated",
                    "booking.cancelled",
                    "booking.completed",
                    "user.registered",
                    "payment.received",
                ],
            },
            {
                "id": "slack",
                "name": "Slack",
                "description": "Get notifications in your Slack channels",
                "icon": "slack",
                "events": [
                    "booking.created",
                    "booking.updated",
                    "booking.cancelled",
                    "booking.completed",
                    "team.member_joined",
                    "team.member_left",
                ],
            },
            {
                "id": "teams",
                "name": "Microsoft Teams",
                "description": "Get notifications in Microsoft Teams",
                "icon": "microsoft-teams",
                "events": [
                    "booking.created",
                    "booking.updated",
                    "booking.cancelled",
                    "booking.completed",
                ],
            },
            {
                "id": "custom",
                "name": "Custom Webhook",
                "description": "Send webhooks to any endpoint",
                "icon": "webhook",
                "events": [
                    "booking.created",
                    "booking.updated",
                    "booking.cancelled",
                    "booking.completed",
                    "user.registered",
                    "user.updated",
                    "payment.received",
                    "payment.failed",
                    "team.member_joined",
                    "team.member_left",
                ],
            },
        ]
    }
