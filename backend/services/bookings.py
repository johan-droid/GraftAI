import asyncio
import hashlib
import logging
import pytz
from datetime import datetime, timedelta, date as date_cls
from urllib.parse import quote_plus
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from dateutil.rrule import rrulestr

from backend.models.tables import (
    BookingTable,
    EventTable,
    EventTypeTable,
    UserTable,
)
from backend.services.scheduler import get_events_for_range, create_event
from backend.services.sync_engine import sync_user_calendar
from backend.services.jobs import enqueue_calendar_job, enqueue_analytics_job
from backend.services.webhook_subscriptions import enqueue_webhook_notifications_for_event
from backend.utils.errors import BookingConflictError, TimezoneError, ValidationError
from backend.utils.cache import (
    acquire_lock,
    get_cache,
    invalidate_user_cache_pattern,
    set_cache,
)


DEFAULT_AVAILABILITY = {
    "monday": ["09:00-17:00"],
    "tuesday": ["09:00-17:00"],
    "wednesday": ["09:00-17:00"],
    "thursday": ["09:00-17:00"],
    "friday": ["09:00-17:00"],
    "saturday": [],
    "sunday": [],
}

ASSIGNMENT_METHODS = {"host_only"}
SUPPORTED_QUESTION_TYPES = {"text", "textarea", "select", "checkbox"}
SINGLE_ASSIGNMENT_METHOD = "host_only"

logger = logging.getLogger(__name__)


def _weekday_name(dt: datetime) -> str:
    return dt.strftime("%A").lower()


def _parse_range_slot(range_value: str) -> Optional[tuple[str, str]]:
    parts = [part.strip() for part in range_value.split("-") if part.strip()]
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def _localize_datetime(day: date_cls, time_str: str, tz: pytz.BaseTzInfo) -> datetime:
    hour, minute = map(int, time_str.split(":"))
    return tz.localize(datetime(day.year, day.month, day.day, hour, minute))


def _date_is_exception(day: date_cls, exceptions: Optional[List[Union[str, Dict[str, Any]]]]) -> bool:
    if not exceptions:
        return False
    for item in exceptions:
        if isinstance(item, str) and item == day.isoformat():
            return True
        if isinstance(item, dict) and item.get("date") == day.isoformat():
            return True
    return False


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    normalized = (value or "").strip()
    if not normalized:
        return None

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = pytz.UTC.localize(parsed)

    return parsed.astimezone(pytz.UTC)


def _get_out_of_office_windows(user: UserTable) -> List[tuple[datetime, datetime]]:
    preferences = user.preferences or {}
    if not isinstance(preferences, dict):
        return []

    blocks = preferences.get("out_of_office") or []
    if not isinstance(blocks, list):
        return []

    windows: List[tuple[datetime, datetime]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        start_dt = _parse_iso_datetime(str(block.get("start_time") or ""))
        end_dt = _parse_iso_datetime(str(block.get("end_time") or ""))
        if not start_dt or not end_dt or end_dt <= start_dt:
            continue
        windows.append((start_dt, end_dt))

    return _merge_overlapping_windows(windows)


def _expand_recurring_availability(
    event_type: EventTypeTable,
    start_date: datetime,
    end_date: datetime,
    limit_slots: int = 100,
) -> List[datetime]:
    """Expand RFC5545 recurrence occurrences for the provided date range."""
    rule_text = (event_type.recurrence_rule or "").strip()
    if not rule_text:
        return []

    if start_date.tzinfo is None:
        start_date = pytz.UTC.localize(start_date)
    if end_date.tzinfo is None:
        end_date = pytz.UTC.localize(end_date)

    dt_start = event_type.created_at or start_date
    if dt_start.tzinfo is None:
        dt_start = pytz.UTC.localize(dt_start)

    try:
        rule = rrulestr(rule_text, dtstart=dt_start)
    except Exception as exc:
        logger.warning(
            "Invalid recurrence_rule for event_type=%s (%s): %s",
            event_type.id,
            rule_text,
            exc,
        )
        return []

    occurrences = rule.between(start_date, end_date, inc=True)
    if len(occurrences) > limit_slots:
        return occurrences[:limit_slots]
    return occurrences


async def validate_custom_questions(
    questions: Optional[Dict[str, Any]],
    event_type: EventTypeTable,
) -> bool:
    definitions = event_type.custom_questions or []
    if not definitions:
        return True

    provided = questions or {}
    if not isinstance(provided, dict):
        raise ValidationError("questions", "Booking questions payload must be an object.")

    for item in definitions:
        if not isinstance(item, dict):
            continue

        question_id = str(item.get("id") or "").strip()
        question_text = str(item.get("question") or question_id or "question").strip()
        question_type = str(item.get("type") or "text").strip().lower()
        required = bool(item.get("required", False))

        if question_type not in SUPPORTED_QUESTION_TYPES:
            raise ValidationError("questions", f"Unsupported question type '{question_type}'.")
        if not question_id:
            raise ValidationError("questions", "Each custom question must have an id.")

        value = provided.get(question_id)
        if required:
            if value is None:
                raise ValidationError("questions", f"Missing required answer for '{question_text}'.")
            if isinstance(value, str) and not value.strip():
                raise ValidationError("questions", f"Missing required answer for '{question_text}'.")
            if isinstance(value, list) and not value:
                raise ValidationError("questions", f"Missing required answer for '{question_text}'.")

        if value is None:
            continue

        if question_type in {"text", "textarea"} and not isinstance(value, str):
            raise ValidationError("questions", f"'{question_text}' expects a text answer.")
        if question_type == "checkbox" and not isinstance(value, bool):
            raise ValidationError("questions", f"'{question_text}' expects a boolean answer.")

        if question_type == "select":
            options = item.get("options") or []
            if options and value not in options:
                raise ValidationError("questions", f"'{question_text}' has an invalid selected option.")

    return True


def _get_availability_windows(event_type: EventTypeTable, day: datetime, tz: pytz.BaseTzInfo) -> List[tuple[datetime, datetime]]:
    day_name = _weekday_name(day)
    raw_availability = event_type.availability or DEFAULT_AVAILABILITY
    daily_ranges = raw_availability.get(day_name, []) or []
    slots: List[tuple[datetime, datetime]] = []

    if _date_is_exception(day.date(), event_type.exceptions):
        return []

    recurrence_rule = (event_type.recurrence_rule or "").strip()
    if recurrence_rule:
        start_of_day = tz.localize(datetime(day.year, day.month, day.day, 0, 0)).astimezone(pytz.UTC)
        end_of_day = start_of_day + timedelta(days=1)
        try:
            occurrences = _expand_recurring_availability(event_type, start_of_day, end_of_day, limit_slots=10)
        except Exception:
            occurrences = []
        if not occurrences:
            return []

    for window in daily_ranges:
        parsed = _parse_range_slot(window)
        if not parsed:
            continue
        start_str, end_str = parsed
        start_dt = _localize_datetime(day.date(), start_str, tz)
        end_dt = _localize_datetime(day.date(), end_str, tz)
        if end_dt <= start_dt:
            continue
        slots.append((start_dt.astimezone(pytz.UTC), end_dt.astimezone(pytz.UTC)))

    return slots


def _slot_to_local_display(slot_dt: datetime, tz: pytz.BaseTzInfo) -> str:
    return slot_dt.astimezone(tz).strftime("%Y-%m-%d %I:%M %p")


def _slots_from_windows(windows: List[tuple[datetime, datetime]], duration_minutes: int, step_minutes: int) -> List[tuple[datetime, datetime]]:
    slots: List[tuple[datetime, datetime]] = []
    for window_start, window_end in windows:
        current = window_start
        while current + timedelta(minutes=duration_minutes) <= window_end:
            slots.append((current, current + timedelta(minutes=duration_minutes)))
            current += timedelta(minutes=step_minutes)
    return slots


def _normalize_datetime_for_overlap(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=pytz.UTC)
    return value


def _overlaps(start: datetime, end: datetime, busy_start: datetime, busy_end: datetime) -> bool:
    start = _normalize_datetime_for_overlap(start)
    end = _normalize_datetime_for_overlap(end)
    busy_start = _normalize_datetime_for_overlap(busy_start)
    busy_end = _normalize_datetime_for_overlap(busy_end)
    return start < busy_end and busy_start < end


def _apply_busy_windows(slots: List[tuple[datetime, datetime]], busy: List[tuple[datetime, datetime]]) -> List[tuple[datetime, datetime]]:
    available: List[tuple[datetime, datetime]] = []
    for slot_start, slot_end in slots:
        if any(_overlaps(slot_start, slot_end, busy_start, busy_end) for busy_start, busy_end in busy):
            continue
        available.append((slot_start, slot_end))
    return available


def _apply_buffer_to_windows(windows: List[tuple[datetime, datetime]], buffer_before: Optional[int], buffer_after: Optional[int]) -> List[tuple[datetime, datetime]]:
    busy: List[tuple[datetime, datetime]] = []
    before = timedelta(minutes=buffer_before or 0)
    after = timedelta(minutes=buffer_after or 0)
    for start, end in windows:
        busy.append((start - before, end + after))
    return _merge_overlapping_windows(busy)


def _merge_overlapping_windows(windows: List[tuple[datetime, datetime]]) -> List[tuple[datetime, datetime]]:
    if not windows:
        return []

    sorted_windows = sorted(windows, key=lambda w: w[0])
    merged: List[tuple[datetime, datetime]] = [sorted_windows[0]]

    for start, end in sorted_windows[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


async def _get_busy_windows_for_range(
    db: AsyncSession,
    user: UserTable,
    start: datetime,
    end: datetime,
) -> List[tuple[datetime, datetime]]:
    cache_key = f"busy_windows:{user.id}:{start.isoformat()}:{end.isoformat()}"
    cached = await get_cache(cache_key)
    if cached is not None:
        return cached

    await _refresh_calendar_events_if_needed(db, user)

    busy_windows: List[tuple[datetime, datetime]] = []

    events = await get_events_for_range(db, user.id, start, end)
    for event in events:
        busy_windows.append((event["start_time"], event["end_time"]))

    booking_stmt = select(BookingTable).where(
        and_(
            BookingTable.user_id == user.id,
            BookingTable.status.in_(["confirmed", "accepted"]),
            BookingTable.start_time < end,
            BookingTable.end_time > start,
        )
    )
    booking_rows = (await db.execute(booking_stmt)).scalars().all()
    for booking in booking_rows:
        busy_windows.append((booking.start_time, booking.end_time))

    merged = _merge_overlapping_windows(busy_windows)
    await set_cache(cache_key, merged, expire_seconds=600)
    return merged


async def _refresh_calendar_events_if_needed(db: AsyncSession, user: UserTable) -> None:
    lock_key = f"calendar:refresh:{user.id}"
    if not await acquire_lock(lock_key, ttl_seconds=30):
        return

    try:
        await sync_user_calendar(db, user.id)
    except Exception as exc:
        print(f"[Calendar Refresh] failed for {user.id}: {exc}")


def _minimum_notice_cutoff(minimum_notice_minutes: Optional[int]) -> datetime:
    return datetime.now(pytz.UTC) + timedelta(minutes=minimum_notice_minutes or 0)


async def _build_available_slots(
    db: AsyncSession,
    user: UserTable,
    event_type: EventTypeTable,
    day: datetime,
    inviter_tz: Optional[str] = None,
    busy_windows: Optional[List[tuple[datetime, datetime]]] = None,
) -> List[Dict[str, Any]]:
    organizer_tz = pytz.timezone(user.timezone or "UTC")

    if event_type.recurrence_rule:
        day_start_local = organizer_tz.localize(datetime(day.year, day.month, day.day, 0, 0))
        day_end_local = day_start_local + timedelta(days=1)
        recurring_occurrences = await _expand_recurring_availability(
            event_type,
            day_start_local.astimezone(pytz.UTC),
            day_end_local.astimezone(pytz.UTC),
            limit_slots=512,
        )
        if not recurring_occurrences:
            return []

    availability_windows = _get_availability_windows(event_type, day, organizer_tz)
    if not availability_windows:
        return []

    if busy_windows is None:
        busy_windows = await _get_busy_windows_for_range(
            db,
            user,
            min(start for start, _ in availability_windows),
            max(end for _, end in availability_windows),
        )

    step = 15
    base_slots = _slots_from_windows(availability_windows, event_type.duration_minutes, step)

    total_before = (event_type.buffer_before_minutes or 0) + (event_type.travel_time_before_minutes or 0)
    total_after = (event_type.buffer_after_minutes or 0) + (event_type.travel_time_after_minutes or 0)
    busy_windows = _apply_buffer_to_windows(busy_windows, total_before, total_after)
    out_of_office_windows = _get_out_of_office_windows(user)
    if out_of_office_windows:
        busy_windows = _merge_overlapping_windows([*busy_windows, *out_of_office_windows])
    available_slots = _apply_busy_windows(base_slots, busy_windows)

    minimum_cutoff = _minimum_notice_cutoff(event_type.minimum_notice_minutes)
    available_slots = [
        (start, end)
        for start, end in available_slots
        if start > minimum_cutoff
    ]

    display_tz = pytz.timezone(inviter_tz) if inviter_tz else organizer_tz
    result: List[Dict[str, Any]] = []
    for start, end in available_slots:
        result.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "organizer_start": start.astimezone(organizer_tz).strftime("%Y-%m-%d %I:%M %p"),
            "organizer_end": end.astimezone(organizer_tz).strftime("%Y-%m-%d %I:%M %p"),
            "invitee_start": start.astimezone(display_tz).strftime("%Y-%m-%d %I:%M %p"),
            "invitee_end": end.astimezone(display_tz).strftime("%Y-%m-%d %I:%M %p"),
            "invitee_zone": str(display_tz),
        })

    return result


async def _build_availability_for_month(
    db: AsyncSession,
    user: UserTable,
    event_type: EventTypeTable,
    year: int,
    month: int,
    inviter_tz: Optional[str] = None,
) -> Dict[str, List[str]]:
    start_day = datetime(year, month, 1)
    end_day = (start_day.replace(day=28) + timedelta(days=4)).replace(day=1)

    organizer_tz = pytz.timezone(user.timezone or "UTC")
    range_start = organizer_tz.localize(datetime(year, month, 1, 0, 0)).astimezone(pytz.UTC)
    range_end = organizer_tz.localize(datetime(end_day.year, end_day.month, end_day.day, 0, 0)).astimezone(pytz.UTC)

    busy_windows = await _get_busy_windows_for_range(db, user, range_start, range_end)

    availability: Dict[str, List[str]] = {}
    day = start_day

    while day < end_day:
        slots = await _build_available_slots(db, user, event_type, day, inviter_tz, busy_windows=busy_windows)
        availability[day.strftime("%Y-%m-%d")] = [slot["invitee_start"] for slot in slots]
        day += timedelta(days=1)

    return availability


def _slugify(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum() or ch in {"-", "_"}).strip("-_ ")


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserTable]:
    stmt = select(UserTable).where(UserTable.username == username.lower())
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_event_type(db: AsyncSession, user_id: str, slug: str) -> Optional[EventTypeTable]:
    stmt = select(EventTypeTable).where(
        and_(EventTypeTable.user_id == user_id, EventTypeTable.slug == slug)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_event_type_config(db: AsyncSession, user_id: str, slug: str) -> Optional[Dict[str, Any]]:
    cache_key = f"event_type_config:{user_id}:{slug}"
    cached = await get_cache(cache_key)
    if cached is not None:
        return cached

    event_type = await get_event_type(db, user_id, slug)
    if not event_type:
        return None

    config = {
        "id": event_type.id,
        "name": event_type.name,
        "duration_minutes": event_type.duration_minutes,
        "meeting_provider": event_type.meeting_provider,
        "timezone": event_type.user.timezone if event_type.user else event_type.user_id,
        "buffer_before_minutes": event_type.buffer_before_minutes,
        "buffer_after_minutes": event_type.buffer_after_minutes,
        "minimum_notice_minutes": event_type.minimum_notice_minutes,
        "availability": event_type.availability,
        "exceptions": event_type.exceptions,
        "recurrence_rule": event_type.recurrence_rule,
        "custom_questions": event_type.custom_questions,
        "requires_attendee_confirmation": event_type.requires_attendee_confirmation,
        "travel_time_before_minutes": event_type.travel_time_before_minutes,
        "travel_time_after_minutes": event_type.travel_time_after_minutes,
        "requires_payment": event_type.requires_payment,
        "payment_amount": event_type.payment_amount,
        "payment_currency": event_type.payment_currency,
        "team_assignment_method": SINGLE_ASSIGNMENT_METHOD,
        "is_public": event_type.is_public,
    }
    await set_cache(cache_key, config, expire_seconds=300)
    return config


async def list_event_types(db: AsyncSession, user_id: str) -> List[EventTypeTable]:
    stmt = select(EventTypeTable).where(EventTypeTable.user_id == user_id)
    result = await db.execute(stmt)
    event_types = result.scalars().all()
    for event_type in event_types:
        event_type.team_assignment_method = SINGLE_ASSIGNMENT_METHOD
    return event_types


async def create_event_type(db: AsyncSession, user_id: str, payload: Dict[str, Any]) -> EventTypeTable:
    slug = payload.get("slug") or _slugify(payload["name"])
    slug = slug.lower()

    stmt = select(EventTypeTable).where(
        and_(EventTypeTable.user_id == user_id, EventTypeTable.slug == slug)
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise ValueError("Event type slug already exists")

    event_type = EventTypeTable(
        user_id=user_id,
        name=payload["name"],
        slug=slug,
        description=payload.get("description"),
        duration_minutes=payload.get("duration_minutes", 60),
        meeting_provider=payload.get("meeting_provider"),
        is_public=payload.get("is_public", True),
        buffer_before_minutes=payload.get("buffer_before_minutes"),
        buffer_after_minutes=payload.get("buffer_after_minutes"),
        minimum_notice_minutes=payload.get("minimum_notice_minutes"),
        availability=payload.get("availability"),
        exceptions=payload.get("exceptions"),
        recurrence_rule=payload.get("recurrence_rule"),
        custom_questions=payload.get("custom_questions"),
        requires_attendee_confirmation=payload.get("requires_attendee_confirmation", False),
        travel_time_before_minutes=payload.get("travel_time_before_minutes", 0),
        travel_time_after_minutes=payload.get("travel_time_after_minutes", 0),
        requires_payment=payload.get("requires_payment", False),
        payment_amount=payload.get("payment_amount"),
        payment_currency=payload.get("payment_currency") or "USD",
        team_assignment_method=SINGLE_ASSIGNMENT_METHOD,
    )
    db.add(event_type)
    await db.commit()
    await db.refresh(event_type)
    return event_type


async def update_event_type(db: AsyncSession, user_id: str, event_type_id: str, payload: Dict[str, Any]) -> Optional[EventTypeTable]:
    event_type = await db.get(EventTypeTable, event_type_id)
    if not event_type or event_type.user_id != user_id:
        return None

    if "name" in payload:
        event_type.name = payload["name"]
    if "description" in payload:
        event_type.description = payload.get("description")
    if "duration_minutes" in payload:
        event_type.duration_minutes = payload.get("duration_minutes")
    if "meeting_provider" in payload:
        event_type.meeting_provider = payload.get("meeting_provider")
    if "is_public" in payload:
        event_type.is_public = payload.get("is_public")
    if "buffer_before_minutes" in payload:
        event_type.buffer_before_minutes = payload.get("buffer_before_minutes")
    if "buffer_after_minutes" in payload:
        event_type.buffer_after_minutes = payload.get("buffer_after_minutes")
    if "minimum_notice_minutes" in payload:
        event_type.minimum_notice_minutes = payload.get("minimum_notice_minutes")
    if "availability" in payload:
        event_type.availability = payload.get("availability")
    if "exceptions" in payload:
        event_type.exceptions = payload.get("exceptions")
    if "recurrence_rule" in payload:
        event_type.recurrence_rule = payload.get("recurrence_rule")
    if "custom_questions" in payload:
        event_type.custom_questions = payload.get("custom_questions")
    if "requires_attendee_confirmation" in payload:
        event_type.requires_attendee_confirmation = bool(payload.get("requires_attendee_confirmation"))
    if "travel_time_before_minutes" in payload:
        event_type.travel_time_before_minutes = max(0, int(payload.get("travel_time_before_minutes") or 0))
    if "travel_time_after_minutes" in payload:
        event_type.travel_time_after_minutes = max(0, int(payload.get("travel_time_after_minutes") or 0))
    if "requires_payment" in payload:
        event_type.requires_payment = bool(payload.get("requires_payment"))
    if "payment_amount" in payload:
        event_type.payment_amount = payload.get("payment_amount")
    if "payment_currency" in payload:
        event_type.payment_currency = (payload.get("payment_currency") or "USD").upper()
    if "team_assignment_method" in payload and payload.get("team_assignment_method"):
        method = str(payload.get("team_assignment_method")).strip().lower()
        if method != SINGLE_ASSIGNMENT_METHOD:
            raise ValueError("Only one-to-one host-only assignment is supported.")

    event_type.team_assignment_method = SINGLE_ASSIGNMENT_METHOD
    if "slug" in payload and payload.get("slug"):
        slug = _slugify(payload["slug"])
        if slug != event_type.slug:
            stmt = select(EventTypeTable).where(
                and_(EventTypeTable.user_id == user_id, EventTypeTable.slug == slug)
            )
            existing = (await db.execute(stmt)).scalars().first()
            if existing:
                raise ValueError("Event type slug already exists")
            event_type.slug = slug

    event_type.updated_at = datetime.now(pytz.UTC)
    await db.commit()
    await db.refresh(event_type)
    return event_type


async def delete_event_type(db: AsyncSession, user_id: str, event_type_id: str) -> bool:
    event_type = await db.get(EventTypeTable, event_type_id)
    if not event_type or event_type.user_id != user_id:
        return False
    await db.delete(event_type)
    await db.commit()
    return True


async def list_event_type_team_members(db: AsyncSession, user_id: str, event_type_id: str) -> List[Dict[str, Any]]:
    return []


async def add_event_type_team_member(
    db: AsyncSession,
    user_id: str,
    event_type_id: str,
    username: str,
    assignment_method: str = "round_robin",
    priority: int = 0,
) -> Dict[str, Any]:
    raise ValueError("Team scheduling is disabled. Only one-to-one host-only booking is supported.")


async def update_event_type_team_member(
    db: AsyncSession,
    user_id: str,
    event_type_id: str,
    member_id: str,
    assignment_method: Optional[str] = None,
    priority: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    raise ValueError("Team scheduling is disabled. Only one-to-one host-only booking is supported.")


async def delete_event_type_team_member(db: AsyncSession, user_id: str, event_type_id: str, member_id: str) -> bool:
    return False


def _localize_window(date: datetime, tz: pytz.BaseTzInfo) -> (datetime, datetime):
    local_start = tz.localize(datetime(date.year, date.month, date.day, 9, 0))
    local_end = tz.localize(datetime(date.year, date.month, date.day, 18, 0))
    return local_start.astimezone(pytz.UTC), local_end.astimezone(pytz.UTC)


async def list_available_slots(
    db: AsyncSession,
    user: UserTable,
    event_type: EventTypeTable,
    date: datetime,
    target_timezone: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return await _build_available_slots(db, user, event_type, date, target_timezone)


async def list_monthly_availability(
    db: AsyncSession,
    user: UserTable,
    event_type: EventTypeTable,
    month: str,
    time_zone: Optional[str] = None,
) -> Dict[str, List[str]]:
    try:
        year, month_number = map(int, month.split("-"))
    except ValueError:
        raise ValueError("Invalid month format. Use YYYY-MM.")

    cache_key = f"availability:{user.id}:{event_type.slug or event_type.id}:{month}:{time_zone or 'default'}"
    cached = await get_cache(cache_key)
    if cached is not None:
        # Warm the calendar sync in the background when a cached result is reused.
        asyncio.create_task(_refresh_calendar_events_if_needed(db, user))
        return cached

    availability = await _build_availability_for_month(db, user, event_type, year, month_number, time_zone)
    await set_cache(cache_key, availability, expire_seconds=300)
    return availability


async def generate_meeting_url(
    meeting_provider: Optional[str],
    organizer_id: str,
    booking_details: Dict[str, Any],
) -> Optional[str]:
    """Generate a provider-specific fallback meeting URL for booking creation."""
    provider = (meeting_provider or "").strip().lower()
    if not provider:
        return None

    attendee_email = str(booking_details.get("attendee_email") or "guest")
    booking_seed = str(booking_details.get("booking_id") or datetime.now(pytz.UTC).timestamp())
    digest = hashlib.sha1(f"{organizer_id}:{attendee_email}:{booking_seed}".encode("utf-8")).hexdigest()

    if provider == "google":
        return f"https://meet.google.com/{digest[:3]}-{digest[3:7]}-{digest[7:10]}"
    if provider == "zoom":
        meeting_number = int(digest[:12], 16) % 10_000_000_000
        return f"https://zoom.us/j/{meeting_number:010d}"
    if provider in {"microsoft", "teams"}:
        return f"https://teams.microsoft.com/l/meetup-join/{digest[:32]}"

    return f"https://meet.graftai.tech/{quote_plus(provider)}/{digest[:24]}"


async def _is_user_available_for_range(
    db: AsyncSession,
    user: UserTable,
    booking_start: datetime,
    booking_end: datetime,
) -> bool:
    out_of_office_windows = _get_out_of_office_windows(user)
    if any(_overlaps(booking_start, booking_end, ooo_start, ooo_end) for ooo_start, ooo_end in out_of_office_windows):
        return False

    windows = await _get_busy_windows_for_range(db, user, booking_start, booking_end)
    return not any(_overlaps(booking_start, booking_end, busy_start, busy_end) for busy_start, busy_end in windows)


async def assign_booking_to_team_member(
    db: AsyncSession,
    event_type: EventTypeTable,
    booking_start: datetime,
    booking_end: datetime,
) -> str:
    """Always assign booking to the event type owner in one-to-one mode."""
    return event_type.user_id


async def create_public_booking(
    db: AsyncSession,
    user: UserTable,
    event_type: EventTypeTable,
    payload: Dict[str, Any],
) -> BookingTable:
    logger.info(
        "Public booking request received: organizer=%s event_type=%s attendee=%s",
        user.id,
        event_type.id,
        payload.get("email"),
    )

    if payload["end_time"] <= payload["start_time"]:
        raise ValidationError("end_time", "End time must be after start time.")

    expected_end = payload["start_time"] + timedelta(minutes=event_type.duration_minutes)
    if payload["end_time"] != expected_end:
        raise ValidationError("end_time", "Booking duration does not match event type configuration.")

    await validate_custom_questions(payload.get("questions"), event_type)

    metadata = payload.get("metadata") or {}
    if event_type.requires_payment:
        is_paid = bool(metadata.get("payment_verified")) or str(metadata.get("payment_status") or "").lower() in {"paid", "captured"}
        if not is_paid:
            raise ValidationError("payment", "Payment is required before booking this event.")

    try:
        user_tz = pytz.timezone(payload.get("time_zone") or user.timezone or "UTC")
    except Exception as exc:
        raise TimezoneError(
            f"Invalid timezone: {payload.get('time_zone') or user.timezone or 'UTC'}"
        ) from exc

    booking_start = payload["start_time"]
    booking_end = payload["end_time"]

    if booking_start.tzinfo is None:
        booking_start = user_tz.localize(booking_start)
    if booking_end.tzinfo is None:
        booking_end = user_tz.localize(booking_end)

    await _refresh_calendar_events_if_needed(db, user)

    booking_start_utc = booking_start.astimezone(pytz.UTC)
    booking_end_utc = booking_end.astimezone(pytz.UTC)
    now_utc = datetime.now(pytz.UTC)
    if booking_start_utc < now_utc:
        raise ValidationError("start_time", "Cannot book a time in the past.")

    out_of_office_windows = _get_out_of_office_windows(user)
    if any(
        _overlaps(booking_start_utc, booking_end_utc, ooo_start, ooo_end)
        for ooo_start, ooo_end in out_of_office_windows
    ):
        raise ValidationError("start_time", "Organizer is out of office during this time.")

    assigned_user_id = await assign_booking_to_team_member(db, event_type, booking_start_utc, booking_end_utc)
    organizer_user = user
    if assigned_user_id and assigned_user_id != user.id:
        assigned_user = await db.get(UserTable, assigned_user_id)
        if assigned_user:
            organizer_user = assigned_user
            logger.info(
                "Booking assigned to team member: event_type=%s assigned_user=%s",
                event_type.id,
                organizer_user.id,
            )

    try:
        organizer_tz = pytz.timezone(organizer_user.timezone or "UTC")
    except Exception as exc:
        raise TimezoneError(
            f"Invalid organizer timezone: {organizer_user.timezone or 'UTC'}"
        ) from exc

    local_start = booking_start_utc.astimezone(organizer_tz)
    day_slots = await _build_available_slots(db, organizer_user, event_type, local_start, payload.get("time_zone"))
    requested_start = booking_start_utc.isoformat()
    requested_end = booking_end_utc.isoformat()
    if not any(slot["start"] == requested_start and slot["end"] == requested_end for slot in day_slots):
        raise ValueError("Requested slot is outside the organizer's available booking windows.")

    booking_status = "pending" if event_type.requires_attendee_confirmation else "confirmed"
    new_event: Optional[EventTable] = None

    # Use SERIALIZABLE isolation for booking creation to prevent phantom reads,
    # dirty reads, and other anomalies on critical booking flow.
    transaction_ctx = db.begin_nested() if db.in_transaction() else db.begin()
    async with transaction_ctx:
        bind = db.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            await db.execute(text("SET LOCAL statement_timeout = 30000"))
            await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))

        user_lock_stmt = select(UserTable).where(UserTable.id == organizer_user.id).with_for_update()
        await db.execute(user_lock_stmt)

        lock_key = int(hashlib.sha256(
            f"booking:{organizer_user.id}:{booking_start_utc.isoformat()}".encode("utf-8")
        ).hexdigest()[:16], 16)

        if bind is not None and bind.dialect.name == "postgresql":
            await db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key})

        booking_conflict_stmt = select(BookingTable).where(
            and_(
                BookingTable.user_id == organizer_user.id,
                BookingTable.status.in_(["pending", "confirmed", "accepted", "rescheduled"]),
                BookingTable.start_time < booking_end_utc,
                BookingTable.end_time > booking_start_utc,
            )
        ).with_for_update()

        existing_booking = (await db.execute(booking_conflict_stmt)).scalars().first()
        if existing_booking:
            raise BookingConflictError("Requested slot is no longer available.")

        event_conflict_stmt = select(EventTable).where(
            and_(
                EventTable.user_id == organizer_user.id,
                EventTable.start_time < booking_end_utc,
                EventTable.end_time > booking_start_utc,
            )
        )
        if (await db.execute(event_conflict_stmt)).scalars().first():
            raise ValueError("Requested slot conflicts with an existing event.")

        booking = BookingTable(
            user_id=organizer_user.id,
            event_type_id=event_type.id,
            full_name=payload["full_name"],
            email=payload["email"],
            time_zone=str(user_tz),
            start_time=booking_start_utc,
            end_time=booking_end_utc,
            status=booking_status,
            questions=payload.get("questions"),
            metadata_payload={
                "source": "public_booking",
                "requested_owner_id": user.id,
                "assigned_owner_id": organizer_user.id,
                "payment": metadata if metadata else None,
            },
        )
        db.add(booking)
        await db.flush()

        fallback_meeting_url = await generate_meeting_url(
            event_type.meeting_provider,
            organizer_user.id,
            {
                "booking_id": booking.id,
                "attendee_email": booking.email,
                "start_time": booking.start_time.isoformat(),
                "duration_minutes": event_type.duration_minutes,
            },
        )

        event_data = {
            "user_id": organizer_user.id,
            "title": event_type.name,
            "description": event_type.description,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "source": "public_booking",
            "fingerprint": f"booking-{datetime.now(pytz.UTC).timestamp()}",
            "is_meeting": bool(event_type.meeting_provider),
            "meeting_provider": event_type.meeting_provider,
            "meeting_url": fallback_meeting_url,
            "attendees": [booking.email],
            "metadata_payload": {
                "customer_name": booking.full_name,
                "customer_email": booking.email,
                "event_type_id": event_type.id,
                "booking_id": booking.id,
            },
            "event_type_id": event_type.id,
        }

        new_event = await create_event(
            db,
            event_data,
            commit=False,
            perform_external=False,
            notify=False,
        )
        booking.event_id = new_event.id
        booking_meta = dict(booking.metadata_payload or {})

        if event_type.travel_time_before_minutes:
            before_minutes = max(0, int(event_type.travel_time_before_minutes))
            before_event = await create_event(
                db,
                {
                    "user_id": organizer_user.id,
                    "title": f"Travel time before {event_type.name}",
                    "description": "Auto-created travel block",
                    "start_time": booking.start_time - timedelta(minutes=before_minutes),
                    "end_time": booking.start_time,
                    "source": "travel_block",
                    "fingerprint": f"travel-before-{booking.id}",
                    "is_meeting": False,
                    "event_type_id": event_type.id,
                    "metadata_payload": {"booking_id": booking.id, "kind": "travel_before"},
                },
                commit=False,
                perform_external=False,
                notify=False,
            )
            booking_meta["travel_before_event_id"] = before_event.id

        if event_type.travel_time_after_minutes:
            after_minutes = max(0, int(event_type.travel_time_after_minutes))
            after_event = await create_event(
                db,
                {
                    "user_id": organizer_user.id,
                    "title": f"Travel time after {event_type.name}",
                    "description": "Auto-created travel block",
                    "start_time": booking.end_time,
                    "end_time": booking.end_time + timedelta(minutes=after_minutes),
                    "source": "travel_block",
                    "fingerprint": f"travel-after-{booking.id}",
                    "is_meeting": False,
                    "event_type_id": event_type.id,
                    "metadata_payload": {"booking_id": booking.id, "kind": "travel_after"},
                },
                commit=False,
                perform_external=False,
                notify=False,
            )
            booking_meta["travel_after_event_id"] = after_event.id

        booking.metadata_payload = booking_meta
        booking.updated_at = datetime.now(pytz.UTC)

    await db.refresh(booking)

    await invalidate_user_cache_pattern(organizer_user.id, "availability")
    await invalidate_user_cache_pattern(organizer_user.id, "busy_windows")

    if booking.status != "pending":
        await enqueue_calendar_job(booking.id, "create")
    await enqueue_analytics_job(
        "booking_created",
        {
            "userId": organizer_user.id,
            "eventTypeId": event_type.id,
            "duration": event_type.duration_minutes,
            "status": booking.status,
        },
    )

    try:
        await enqueue_webhook_notifications_for_event(
            db,
            organizer_user.id,
            "booking.created",
            {
                "booking_id": booking.id,
                "booking_code": booking.booking_code,
                "event_id": new_event.id if new_event else None,
                "event_type_id": event_type.id,
                "user_id": organizer_user.id,
                "customer_name": booking.full_name,
                "customer_email": booking.email,
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "meeting_provider": event_type.meeting_provider,
                "is_meeting": bool(event_type.meeting_provider),
                "status": booking.status,
                "metadata_payload": booking.metadata_payload or {},
            },
        )
    except Exception as exc:
        logger.error(
            "Booking created but webhook notification enqueue failed for booking=%s user=%s: %s",
            booking.id,
            organizer_user.id,
            exc,
            exc_info=True,
        )

    logger.info(
        "Public booking created: booking=%s organizer=%s status=%s",
        booking.id,
        organizer_user.id,
        booking.status,
    )

    return booking
