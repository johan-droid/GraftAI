import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import html
import re
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, field_validator, validator
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
import pytz

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable, UserTokenTable
from backend.services.google_auth import get_google_auth_url
from backend.services.oauth_service import build_oauth_state
from backend.services.storage import storage


router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


class UserProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    time_format: Optional[str] = None
    theme: Optional[str] = None
    brand_color_light: Optional[str] = None
    brand_color_dark: Optional[str] = None
    booking_layout: Optional[str] = None
    default_calendar_id: Optional[str] = None
    preferences: Optional[dict] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "display_name",
        "full_name",
        "username",
        "bio",
        "phone",
        "timezone",
        "time_format",
        "theme",
        "brand_color_light",
        "brand_color_dark",
        "booking_layout",
        "default_calendar_id",
        mode="before",
    )
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return html.escape(v.strip())

    @validator("username")
    def username_must_be_valid(cls, value: Optional[str]):
        if value is None:
            return value
        if not re.fullmatch(r"[a-zA-Z0-9_-]{3,30}", value):
            raise ValueError(
                "Username must be 3-30 characters and contain only letters, numbers, hyphens, or underscores."
            )
        return value.lower()

    @validator("display_name")
    def display_name_must_be_valid(cls, value: Optional[str]):
        if value is None:
            return value
        normalized = value.strip()
        if len(normalized) < 1 or len(normalized) > 100:
            raise ValueError("Display name must be 1-100 characters")
        if not re.fullmatch(r"[A-Za-z0-9 '\-]+", normalized):
            raise ValueError(
                "Display name may only include letters, numbers, spaces, apostrophes, and hyphens"
            )
        return normalized

    @validator("bio")
    def bio_length(cls, value: Optional[str]):
        if value is None:
            return value
        if len(value.strip()) > 500:
            raise ValueError("Bio must be under 500 characters")
        return value.strip()

    @validator("phone")
    def validate_phone(cls, value: Optional[str]):
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not re.fullmatch(r"\+?[1-9]\d{1,14}", normalized):
            raise ValueError("Please enter a valid phone number")
        return normalized

    @validator("timezone")
    def validate_timezone(cls, value: Optional[str]):
        if value is None:
            return value
        if value not in pytz.all_timezones:
            raise ValueError("Invalid timezone selected")
        return value

    @validator("time_format")
    def validate_time_format(cls, value: Optional[str]):
        if value is None:
            return value
        if value not in {"12h", "24h"}:
            raise ValueError("Invalid time format")
        return value

    @validator("theme")
    def validate_theme(cls, value: Optional[str]):
        if value is None:
            return value
        if value not in {"light", "dark", "system"}:
            raise ValueError("Invalid theme")
        return value

    @validator("brand_color_light", "brand_color_dark")
    def validate_color(cls, value: Optional[str]):
        if value is None:
            return value
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("Please select a valid color")
        return value.lower()

    @validator("booking_layout")
    def validate_booking_layout(cls, value: Optional[str]):
        if value is None:
            return value
        if value not in {"monthly", "weekly", "daily"}:
            raise ValueError("Invalid booking layout")
        return value


class OutOfOfficeBlockCreateRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None

    @validator("end_time")
    def end_must_be_after_start(cls, value: datetime, values: Dict[str, Any]):
        start_time = values.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time must be after start_time")
        return value


def _normalize_preferences(user: UserTable) -> Dict[str, Any]:
    prefs = user.preferences or {}
    if not isinstance(prefs, dict):
        return {}
    return dict(prefs)


def _set_preferences(user: UserTable, preferences: Dict[str, Any]) -> None:
    user.preferences = preferences


def _profile_setup_completed(user: UserTable) -> bool:
    prefs = _normalize_preferences(user)
    completed_steps = prefs.get("completed_steps", [])
    if not isinstance(completed_steps, list):
        completed_steps = []

    # Normalize completed_steps to strings to avoid type errors
    try:
        completed_steps_set = set(str(x) for x in completed_steps if x is not None)
    except Exception:
        completed_steps_set = set()

    return bool(
        prefs.get("profile_setup_completed")
        or user.onboarding_completed
        or "profile" in completed_steps_set
    )


def _mark_profile_setup_completed(user: UserTable) -> None:
    prefs = _normalize_preferences(user)
    completed_steps = list(
        dict.fromkeys(list(prefs.get("completed_steps", [])) + ["profile"])
    )
    prefs["completed_steps"] = completed_steps
    prefs["profile_setup_completed"] = True
    _set_preferences(user, prefs)


def _serialize_profile(user: UserTable) -> Dict[str, Any]:
    prefs = _normalize_preferences(user)
    avatar_key = prefs.get("avatar_key")
    avatar_url = (
        storage.get_presigned_url(avatar_key) if avatar_key else prefs.get("avatar_url")
    )
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "display_name": prefs.get("display_name") or user.full_name,
        "avatar_url": avatar_url,
        "bio": prefs.get("bio"),
        "phone": prefs.get("phone"),
        "timezone": user.timezone or prefs.get("timezone") or "UTC",
        "time_format": prefs.get("time_format", "12h"),
        "theme": prefs.get("theme", "system"),
        "brand_color_light": prefs.get("brand_color_light", "#3b82f6"),
        "brand_color_dark": prefs.get("brand_color_dark", "#1e40af"),
        "booking_layout": prefs.get("booking_layout", "monthly"),
        "default_calendar_id": prefs.get("default_calendar_id"),
        "preferences": prefs,
        "profile_setup_completed": _profile_setup_completed(user),
        "onboarding_completed": bool(user.onboarding_completed),
        "completed_steps": prefs.get("completed_steps", []),
        "tier": user.tier,
        "subscription_status": user.subscription_status,
        "razorpay_subscription_id": user.razorpay_subscription_id,
        "daily_ai_count": user.daily_ai_count,
        "daily_ai_limit": user.daily_ai_limit,
        "daily_sync_count": user.daily_sync_count,
        "daily_sync_limit": user.daily_sync_limit,
        "quota_reset_at": user.quota_reset_at.isoformat()
        if user.quota_reset_at
        else None,
        "trial_expires_at": user.trial_expires_at.isoformat()
        if user.trial_expires_at
        else None,
        "total_ai_tokens": user.total_ai_tokens,
        "total_api_calls": user.total_api_calls,
        "total_scheduling_count": user.total_scheduling_count,
    }


def _build_profile_response(user: UserTable) -> Dict[str, Any]:
    return {
        "success": True,
        "message": "Profile retrieved successfully",
        "data": _serialize_profile(user),
    }


def _apply_profile_payload(
    user: UserTable, payload: UserProfileUpdateRequest
) -> UserTable:
    prefs = _normalize_preferences(user)

    if payload.preferences is not None:
        filtered = {
            k: v
            for k, v in payload.preferences.items()
            if k
            not in {
                "display_name",
                "full_name",
                "username",
                "bio",
                "phone",
                "timezone",
                "time_format",
                "theme",
                "brand_color_light",
                "brand_color_dark",
                "booking_layout",
                "default_calendar_id",
            }
        }
        prefs.update(filtered)

    if payload.display_name is not None:
        display_name = payload.display_name.strip()
        if display_name:
            prefs["display_name"] = display_name

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or user.full_name

    if payload.username is not None:
        username = payload.username.strip().lower()
        if username and username != user.username:
            user.username = username

    if payload.bio is not None:
        prefs["bio"] = payload.bio.strip() if payload.bio.strip() else None

    if payload.phone is not None:
        prefs["phone"] = payload.phone

    if payload.timezone is not None:
        prefs["timezone"] = payload.timezone
        user.timezone = payload.timezone

    if payload.time_format is not None:
        prefs["time_format"] = payload.time_format

    if payload.theme is not None:
        prefs["theme"] = payload.theme

    if payload.brand_color_light is not None:
        prefs["brand_color_light"] = payload.brand_color_light

    if payload.brand_color_dark is not None:
        prefs["brand_color_dark"] = payload.brand_color_dark

    if payload.booking_layout is not None:
        prefs["booking_layout"] = payload.booking_layout

    if payload.default_calendar_id is not None:
        prefs["default_calendar_id"] = payload.default_calendar_id

    _set_preferences(user, prefs)
    return user


def _to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat()


def _extract_out_of_office_blocks(user: UserTable) -> List[Dict[str, Any]]:
    prefs = _normalize_preferences(user)
    blocks = prefs.get("out_of_office") or []
    if not isinstance(blocks, list):
        return []
    normalized = [item for item in blocks if isinstance(item, dict)]
    normalized.sort(key=lambda item: item.get("start_time") or "")
    return normalized


def _set_out_of_office_blocks(user: UserTable, blocks: List[Dict[str, Any]]) -> None:
    prefs = _normalize_preferences(user)
    prefs["out_of_office"] = blocks
    user.preferences = prefs


@router.get("/me")
async def get_my_profile(current_user: UserTable = Depends(get_current_user)):
    """Fetch current user profile for the monolithic dashboard."""
    return _serialize_profile(current_user)


@router.get("/me/profile")
async def get_my_profile_details(current_user: UserTable = Depends(get_current_user)):
    """Fetch the authenticated user's profile data for onboarding."""
    return _build_profile_response(current_user)


@router.post("/me/profile")
@router.put("/me/profile")
async def create_or_update_profile(
    payload: UserProfileUpdateRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update user profile during onboarding."""
    try:
        # Use current_user directly to avoid session detachment issues
        user = current_user

        if payload.username is not None:
            username = payload.username.strip().lower()
            if username and username != user.username:
                stmt = select(UserTable).where(
                    UserTable.username == username, UserTable.id != user.id
                )
                existing = (await db.execute(stmt)).scalars().first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Username already taken",
                    )

        # Apply profile changes
        user = _apply_profile_payload(user, payload)
        _mark_profile_setup_completed(user)
        
        # Explicitly mark as modified so SQLAlchemy tracks changed payload fields
        db.add(user)
        if hasattr(user, "preferences"):
            flag_modified(user, "preferences")
        
        await db.commit()
        await db.refresh(user)

        logger.info(f"Profile updated for user {user.id[:8]}... (onboarding)")

        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": _serialize_profile(user),
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update profile (onboarding)")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save profile")


@router.get("/me/profile/setup-status")
async def get_profile_setup_status(current_user: UserTable = Depends(get_current_user)):
    prefs = _normalize_preferences(current_user)
    return {
        "success": True,
        "message": "Setup status loaded successfully",
        "data": {
            "completed_steps": prefs.get("completed_steps", []),
            "profile_setup_completed": _profile_setup_completed(current_user),
            "onboarding_completed": bool(current_user.onboarding_completed),
            "profile": _serialize_profile(current_user),
        },
    }


@router.get("/me/calendars/oauth/google/auth-url")
async def get_google_calendar_auth_url(
    current_user: UserTable = Depends(get_current_user),
):
    state = build_oauth_state(
        current_user.id, redirect_to="/profile/setup/calendar", provider="google"
    )
    try:
        auth_url = await get_google_auth_url(state)
    except ValueError as exc:
        logger.error("Google OAuth configuration error for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return {
        "success": True,
        "message": "Google authorization URL created",
        "data": {"auth_url": auth_url, "state": state},
    }


@router.post("/me/profile/avatar")
async def upload_profile_avatar(
    file: UploadFile = File(...),
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported avatar image type. Use JPEG, PNG, or WEBP.",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Avatar file must be 5MB or smaller.",
        )

    file.file.seek(0)
    header_sample = file.file.read(16)
    file.file.seek(0)

    magic_map = {
        "image/jpeg": b"\xff\xd8\xff",
        "image/png": b"\x89PNG",
        "image/webp": b"RIFF",
    }
    if file.content_type == "image/webp":
        if len(header_sample) < 12 or not (
            header_sample.startswith(b"RIFF") and header_sample[8:12] == b"WEBP"
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar content does not match declared file type.",
            )
    elif not header_sample.startswith(magic_map[file.content_type]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar content does not match declared file type.",
        )

    extension = Path(file.filename).suffix.lower() or ".png"
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        extension = ".png"
    upload_key = f"avatars/{current_user.id}/{uuid.uuid4().hex}{extension}"

    try:
        file.file.seek(0)
        storage_key = await storage.upload_file(
            file.file, upload_key, file.content_type
        )
        if not storage_key:
            raise ValueError("Storage upload failed")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not upload avatar at this time.",
        ) from exc

    avatar_url = storage.get_presigned_url(storage_key)
    prefs = _normalize_preferences(current_user)
    prefs["avatar_key"] = storage_key
    prefs.pop("avatar_url", None)
    _set_preferences(current_user, prefs)
    await db.commit()
    await db.refresh(current_user)

    return {
        "success": True,
        "message": "Avatar uploaded successfully",
        "data": {"avatar_url": avatar_url},
    }


@router.post("/me/profile/complete-step/{step_id}")
async def complete_profile_setup_step(
    step_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    valid_steps = ["profile", "calendar", "availability", "event_type"]
    if step_id not in valid_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid onboarding step"
        )

    prefs = _normalize_preferences(current_user)
    completed_steps = list(
        dict.fromkeys(list(prefs.get("completed_steps", [])) + [step_id])
    )
    prefs["completed_steps"] = completed_steps
    if step_id == "profile":
        prefs["profile_setup_completed"] = True
    _set_preferences(current_user, prefs)
    await db.commit()
    next_step = None
    current_index = valid_steps.index(step_id)
    if current_index < len(valid_steps) - 1:
        next_step = valid_steps[current_index + 1]
    return {
        "success": True,
        "message": "Onboarding step completed",
        "data": {"completed_steps": completed_steps, "next_step": next_step},
    }


@router.get("/me/onboarding/preview")
async def get_onboarding_preview(current_user: UserTable = Depends(get_current_user)):
    username = current_user.username or current_user.email.split("@")[0]
    return {
        "success": True,
        "message": "Onboarding preview loaded",
        "data": {
            "bookingPageUrl": f"/public/users/{username}",
            "isLive": bool(current_user.onboarding_completed),
        },
    }


@router.post("/me/onboarding/complete")
async def complete_onboarding_flow(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.onboarding_completed = True
    current_user.onboarding_completed_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "success": True,
        "message": "Onboarding completed successfully",
        "data": {"redirect_url": "/dashboard"},
    }


@router.get("/me/integrations")
async def get_my_integrations(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns a list of connected services (e.g., ['google', 'microsoft'])."""
    active_stmt = select(UserTokenTable.provider).where(
        and_(
            UserTokenTable.user_id == current_user.id, UserTokenTable.is_active == True
        )
    )
    inactive_stmt = select(UserTokenTable.provider).where(
        and_(
            UserTokenTable.user_id == current_user.id, UserTokenTable.is_active == False
        )
    )
    active_providers = (await db.execute(active_stmt)).scalars().all()
    inactive_providers = (await db.execute(inactive_stmt)).scalars().all()
    return {
        "active_providers": list(active_providers),
        "inactive_providers": list(
            sorted(set(inactive_providers) - set(active_providers))
        ),
    }


@router.delete("/me/integrations/{provider}")
async def disconnect_integration(
    provider: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes or deactivates the OAuth token for a specific provider."""
    stmt = select(UserTokenTable).where(
        and_(
            UserTokenTable.user_id == current_user.id,
            UserTokenTable.provider == provider,
        )
    )
    token = (await db.execute(stmt)).scalars().first()

    if not token:
        raise HTTPException(status_code=404, detail="Integration not found")

    await db.delete(token)
    await db.commit()
    return {"message": f"{provider} disconnected successfully"}


@router.patch("/me")
async def update_current_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile settings."""
    try:
        # Use the current_user directly - it's already attached to the session
        # No need to re-query which can cause session detachment issues
        user = current_user

        # Check username uniqueness if being changed
        if payload.username is not None:
            username = payload.username.strip().lower()
            if username and username != user.username:
                stmt = select(UserTable).where(
                    UserTable.username == username, UserTable.id != user.id
                )
                existing = (await db.execute(stmt)).scalars().first()
                if existing:
                    raise HTTPException(status_code=409, detail="Username already taken")

        # Apply all profile changes
        user = _apply_profile_payload(user, payload)
        _mark_profile_setup_completed(user)
        
        # Explicitly mark as modified so SQLAlchemy tracks changed payload fields
        db.add(user)
        if hasattr(user, "preferences"):
            flag_modified(user, "preferences")
        
        # Commit changes
        await db.commit()
        await db.refresh(user)

        logger.info(f"Profile updated for user {user.id[:8]}...")

        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": _serialize_profile(user),
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update profile")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save profile")


@router.get("/me/out-of-office")
async def list_current_user_out_of_office(
    current_user: UserTable = Depends(get_current_user),
):
    return {"items": _extract_out_of_office_blocks(current_user)}


@router.post("/me/out-of-office")
async def create_current_user_out_of_office(
    payload: OutOfOfficeBlockCreateRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    blocks = _extract_out_of_office_blocks(current_user)
    block = {
        "id": uuid.uuid4().hex,
        "start_time": _to_utc_iso(payload.start_time),
        "end_time": _to_utc_iso(payload.end_time),
        "reason": (payload.reason or "").strip() or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    blocks.append(block)
    _set_out_of_office_blocks(current_user, blocks)
    await db.commit()
    await db.refresh(current_user)
    return block


@router.delete("/me/out-of-office/{block_id}")
async def delete_current_user_out_of_office(
    block_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    blocks = _extract_out_of_office_blocks(current_user)
    filtered = [item for item in blocks if item.get("id") != block_id]
    if len(filtered) == len(blocks):
        raise HTTPException(status_code=404, detail="Out-of-office block not found")

    _set_out_of_office_blocks(current_user, filtered)
    await db.commit()
    await db.refresh(current_user)
    return {"status": "deleted", "id": block_id}


@router.delete("/me")
async def delete_current_user_account(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete user account (anonymize for data integrity)."""
    import uuid

    # Anonymize user instead of hard delete for data integrity
    current_user.email = (
        f"deleted_{current_user.id}_{uuid.uuid4().hex[:8]}@anonymized.com"
    )
    current_user.full_name = "Deleted User"
    current_user.is_active = False
    current_user.deleted_at = datetime.now(timezone.utc)

    # Clear sensitive data
    current_user.hashed_password = None  # Pure OAuth 2.0
    current_user.email_verification_code = None
    current_user.password_reset_token = None
    current_user.preferences = {}

    await db.commit()

    return {
        "status": "account_anonymized",
        "message": "Your account has been anonymized and deactivated. Access has been removed.",
    }
