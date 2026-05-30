from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import BookingTable
from backend.models.team import TeamMember
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def select_team_member(db: AsyncSession, team_id: str) -> str | None:
    """
    Select a team member using weighted round-robin and basic availability checks.

    Algorithm:
    - Load active members for the team
    - Exclude members who exceeded `max_daily_bookings` (if set)
    - Compute a score = (last_assigned_at timestamp or epoch) / weight
    - Choose the member with smallest score (least recently assigned adjusted by weight)
    - Update `last_assigned_at` for chosen member
    Returns the `user_id` of the assigned member or None if no active/available members.
    """
    stmt = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.is_active)
    result = await db.execute(stmt)
    members = result.scalars().all()
    if not members:
        return None
    candidates = []
    now = datetime.now(UTC)
    for m in members:
        if getattr(m, "max_daily_bookings", None) is not None:
            start_of_day = datetime(now.year, now.month, now.day, tzinfo=UTC)
            count_stmt = select(func.count()).where(and_(BookingTable.user_id == m.user_id, BookingTable.start_time >= start_of_day, BookingTable.start_time < start_of_day + timedelta(days=1)))
            booked_count = (await db.execute(count_stmt)).scalar() or 0
            if booked_count >= (m.max_daily_bookings or 0):
                continue
        weight = getattr(m, "weight", None) or getattr(m, "round_robin_weight", None) or 1
        last_ts = 0
        if m.last_assigned_at:
            last_ts = int(m.last_assigned_at.timestamp())
        score = (last_ts or 0) / weight
        candidates.append((score, m))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    chosen = candidates[0][1]
    try:
        chosen.last_assigned_at = now
        db.add(chosen)
        await db.flush()
        logger.info("Team routing: assigned member %s for team %s", chosen.user_id, team_id)
        return chosen.user_id
    except Exception as e:
        logger.exception("Failed to persist assignment for team %s: %s", team_id, e)
        return chosen.user_id
