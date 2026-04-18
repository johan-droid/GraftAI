"""GDPR compliance API routes for Data Subject Requests."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.auth.schemes import get_current_user_id, require_admin
from backend.utils.db import get_db
from backend.models.dsr import DSRRecord, DSRType, DSRStatus, ConsentRecord
from backend.utils.dsr_workflow import dsr_workflow

router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR Compliance"])


# Request models
class DSRSubmitRequest(BaseModel):
    """Submit a Data Subject Request."""

    request_type: DSRType
    details: Optional[Dict[str, Any]] = {}
    requester_email: Optional[EmailStr] = None


class DSRVerifyRequest(BaseModel):
    """Verify identity for DSR."""

    verification_code: str


class ConsentUpdateRequest(BaseModel):
    """Update consent preferences."""

    analytics: bool = False
    marketing: bool = False
    ai_training: bool = False
    third_party_sharing: bool = False


class ConsentWithdrawRequest(BaseModel):
    """Withdraw consent for specific category."""

    category: str  # analytics, marketing, ai_training, third_party_sharing
    reason: Optional[str] = None


# Response models
class DSRResponse(BaseModel):
    """DSR response model."""

    request_id: str
    status: str
    deadline: Optional[str] = None
    message: Optional[str] = None


class DSRStatusResponse(BaseModel):
    """DSR status response."""

    request_id: str
    request_type: str
    status: str
    submitted_at: str
    deadline_at: str
    completed_at: Optional[str] = None
    identity_verified: bool
    is_overdue: bool
    days_remaining: int


class ConsentStatusResponse(BaseModel):
    """Consent status response."""

    essential: bool
    analytics: bool
    marketing: bool
    ai_training: bool
    third_party_sharing: bool
    consented_at: Optional[str] = None
    is_valid: bool


@router.post("/dsr/submit", response_model=DSRResponse)
async def submit_dsr(
    request: DSRSubmitRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new Data Subject Request (GDPR Articles 15-22)."""
    try:
        result = await dsr_workflow.submit_request(
            db=db,
            user_id=user_id,
            request_type=request.request_type,
            details=request.details,
            requester_email=request.requester_email,
        )
        return DSRResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dsr/anonymous")
async def submit_anonymous_dsr(
    request: DSRSubmitRequest,
    requester_ip: str = None,
    requester_user_agent: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Submit a DSR without authentication (requires email verification)."""
    if not request.requester_email:
        raise HTTPException(
            status_code=400, detail="requester_email required for anonymous requests"
        )

    try:
        result = await dsr_workflow.submit_request(
            db=db,
            user_id=None,
            request_type=request.request_type,
            details=request.details,
            requester_email=request.requester_email,
            requester_ip=requester_ip,
            requester_user_agent=requester_user_agent,
        )
        return DSRResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dsr/verify", response_model=DSRResponse)
async def verify_dsr_identity(
    request: DSRVerifyRequest,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Verify identity for anonymous DSR."""
    try:
        result = await dsr_workflow.verify_identity(
            db, request_id, request.verification_code
        )
        return DSRResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dsr/status/{request_id}", response_model=DSRStatusResponse)
async def get_dsr_status(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get status of a DSR."""
    stmt = select(DSRRecord).where(
        DSRRecord.id == request_id, DSRRecord.user_id == user_id
    )
    dsr = (await db.execute(stmt)).scalars().first()

    if not dsr:
        raise HTTPException(status_code=404, detail="Request not found")

    return DSRStatusResponse(
        request_id=dsr.id,
        request_type=dsr.request_type.value,
        status=dsr.status.value,
        submitted_at=dsr.submitted_at.isoformat() if dsr.submitted_at else None,
        deadline_at=dsr.deadline_at.isoformat() if dsr.deadline_at else None,
        completed_at=dsr.completed_at.isoformat() if dsr.completed_at else None,
        identity_verified=dsr.identity_verified,
        is_overdue=dsr.is_overdue,
        days_remaining=dsr.days_remaining,
    )


@router.get("/dsr/my-requests", response_model=List[DSRStatusResponse])
async def list_my_dsrs(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all DSRs for the current user."""
    stmt = (
        select(DSRRecord)
        .where(DSRRecord.user_id == user_id)
        .order_by(DSRRecord.submitted_at.desc())
    )
    dsrs = (await db.execute(stmt)).scalars().all()

    return [
        DSRStatusResponse(
            request_id=dsr.id,
            request_type=dsr.request_type.value,
            status=dsr.status.value,
            submitted_at=dsr.submitted_at.isoformat() if dsr.submitted_at else None,
            deadline_at=dsr.deadline_at.isoformat() if dsr.deadline_at else None,
            completed_at=dsr.completed_at.isoformat() if dsr.completed_at else None,
            identity_verified=dsr.identity_verified,
            is_overdue=dsr.is_overdue,
            days_remaining=dsr.days_remaining,
        )
        for dsr in dsrs
    ]


@router.get("/consent/status", response_model=ConsentStatusResponse)
async def get_consent_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current consent status."""
    stmt = select(ConsentRecord).where(ConsentRecord.user_id == user_id)
    consent = (await db.execute(stmt)).scalars().first()

    if not consent:
        # Create default consent record
        consent = ConsentRecord(user_id=user_id, essential=True)
        db.add(consent)
        await db.commit()

    return ConsentStatusResponse(
        essential=consent.essential,
        analytics=consent.analytics,
        marketing=consent.marketing,
        ai_training=consent.ai_training,
        third_party_sharing=consent.third_party_sharing,
        consented_at=consent.consented_at.isoformat() if consent.consented_at else None,
        is_valid=consent.is_valid,
    )


@router.post("/consent/update", response_model=ConsentStatusResponse)
async def update_consent(
    request: ConsentUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update consent preferences (GDPR Article 6/7)."""
    stmt = select(ConsentRecord).where(ConsentRecord.user_id == user_id)
    consent = (await db.execute(stmt)).scalars().first()

    if not consent:
        consent = ConsentRecord(user_id=user_id)
        db.add(consent)

    # Update consent fields
    consent.analytics = request.analytics
    consent.marketing = request.marketing
    consent.ai_training = request.ai_training
    consent.third_party_sharing = request.third_party_sharing

    # If first time consenting, set consented_at
    if not consent.consented_at:
        consent.consented_at = datetime.utcnow()

    # Reset withdrawal dates for newly consented categories
    if request.analytics:
        consent.analytics_withdrawn_at = None
    if request.marketing:
        consent.marketing_withdrawn_at = None
    if request.ai_training:
        consent.ai_training_withdrawn_at = None
    if request.third_party_sharing:
        consent.third_party_sharing_withdrawn_at = None

    await db.commit()

    return ConsentStatusResponse(
        essential=consent.essential,
        analytics=consent.analytics,
        marketing=consent.marketing,
        ai_training=consent.ai_training,
        third_party_sharing=consent.third_party_sharing,
        consented_at=consent.consented_at.isoformat() if consent.consented_at else None,
        is_valid=consent.is_valid,
    )


@router.post("/consent/withdraw")
async def withdraw_consent(
    request: ConsentWithdrawRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw consent for a specific category (GDPR Article 7.3)."""
    stmt = select(ConsentRecord).where(ConsentRecord.user_id == user_id)
    consent = (await db.execute(stmt)).scalars().first()

    if not consent:
        raise HTTPException(status_code=404, detail="No consent record found")

    category = request.category.lower()
    valid_categories = ["analytics", "marketing", "ai_training", "third_party_sharing"]

    if category not in valid_categories:
        raise HTTPException(
            status_code=400, detail=f"Invalid category. Valid: {valid_categories}"
        )

    # Set withdrawal timestamp
    withdrawal_attr = f"{category}_withdrawn_at"
    setattr(consent, withdrawal_attr, datetime.utcnow())

    # If all categories withdrawn, mark full withdrawal
    if all(
        [
            consent.analytics_withdrawn_at,
            consent.marketing_withdrawn_at,
            consent.ai_training_withdrawn_at,
            consent.third_party_sharing_withdrawn_at,
        ]
    ):
        consent.withdrawn_at = datetime.utcnow()
        consent.withdrawal_reason = request.reason

    await db.commit()

    return {"status": "withdrawn", "category": category}


# Admin-only endpoints
@router.get("/admin/dsr/all")
async def list_all_dsrs(
    status: Optional[DSRStatus] = None,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all DSRs (admin only)."""
    stmt = select(DSRRecord)

    if status:
        stmt = stmt.where(DSRRecord.status == status)

    stmt = stmt.order_by(DSRRecord.submitted_at.desc())
    dsrs = (await db.execute(stmt)).scalars().all()

    return [
        {
            "request_id": dsr.id,
            "user_id": dsr.user_id,
            "request_type": dsr.request_type.value,
            "status": dsr.status.value,
            "submitted_at": dsr.submitted_at.isoformat() if dsr.submitted_at else None,
            "deadline_at": dsr.deadline_at.isoformat() if dsr.deadline_at else None,
            "is_overdue": dsr.is_overdue,
            "days_remaining": dsr.days_remaining,
        }
        for dsr in dsrs
    ]


@router.post("/admin/dsr/process/{request_id}")
async def process_dsr(
    request_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually process a DSR (admin only)."""
    try:
        result = await dsr_workflow.process_request(db, request_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
