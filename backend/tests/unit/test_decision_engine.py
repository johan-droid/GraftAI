"""
Unit tests for DecisionEngine changes introduced in this PR:
- TimingAnalysis.timezone_offset_hours changed from float to int
- _analyze_timing now always returns timezone_offset_hours=0 (hardcoded)
- zoneinfo import removed
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from backend.ai.decision_engine import (
    AttendeeAnalysis,
    DecisionEngine,
    TimingAnalysis,
    VIPLevel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_attendee(timezone_str: str = "UTC", avg_response_time_hours: float = 2.0) -> AttendeeAnalysis:
    return AttendeeAnalysis(
        email="attendee@example.com",
        vip_level=VIPLevel.STANDARD,
        is_new=False,
        booking_frequency=2,
        no_show_rate=0.0,
        avg_response_time_hours=avg_response_time_hours,
        preferred_communication=["email"],
        engagement_score=0.5,
        timezone=timezone_str,
    )


# ---------------------------------------------------------------------------
# TimingAnalysis dataclass tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTimingAnalysisDataclass:
    """Tests for the TimingAnalysis dataclass shape after the PR change."""

    def test_timezone_offset_hours_is_int(self):
        """timezone_offset_hours field must accept and store an int."""
        analysis = TimingAnalysis(
            optimal_send_time=datetime.now(timezone.utc).isoformat(),
            timezone_offset_hours=0,
            expected_response_time_hours=1.0,
            urgency_level="medium",
            business_hours_aligned=True,
        )
        assert isinstance(analysis.timezone_offset_hours, int)

    def test_timezone_offset_hours_positive_int(self):
        """Positive integer offsets are valid."""
        analysis = TimingAnalysis(
            optimal_send_time=datetime.now(timezone.utc).isoformat(),
            timezone_offset_hours=5,
            expected_response_time_hours=1.0,
            urgency_level="medium",
            business_hours_aligned=True,
        )
        assert analysis.timezone_offset_hours == 5
        assert isinstance(analysis.timezone_offset_hours, int)

    def test_timezone_offset_hours_negative_int(self):
        """Negative integer offsets are valid (west of UTC)."""
        analysis = TimingAnalysis(
            optimal_send_time=datetime.now(timezone.utc).isoformat(),
            timezone_offset_hours=-8,
            expected_response_time_hours=2.0,
            urgency_level="low",
            business_hours_aligned=False,
        )
        assert analysis.timezone_offset_hours == -8
        assert isinstance(analysis.timezone_offset_hours, int)

    def test_timezone_offset_zero(self):
        """Zero offset (UTC) is the expected default after the PR."""
        analysis = TimingAnalysis(
            optimal_send_time=datetime.now(timezone.utc).isoformat(),
            timezone_offset_hours=0,
            expected_response_time_hours=1.0,
            urgency_level="medium",
            business_hours_aligned=True,
        )
        assert analysis.timezone_offset_hours == 0


# ---------------------------------------------------------------------------
# DecisionEngine._analyze_timing tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAnalyzeTiming:
    """Tests for DecisionEngine._analyze_timing after the PR change."""

    @pytest.fixture
    def engine(self):
        return DecisionEngine()

    async def test_timezone_offset_is_always_zero(self, engine):
        """After the PR, timezone_offset_hours is always 0 regardless of attendee timezone."""
        attendee = make_attendee(timezone_str="America/New_York")
        booking = {"id": "booking-1"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.timezone_offset_hours == 0

    async def test_timezone_offset_is_int_not_float(self, engine):
        """timezone_offset_hours must be an int, not a float."""
        attendee = make_attendee(timezone_str="Asia/Tokyo")
        booking = {"id": "booking-2"}

        result = await engine._analyze_timing(booking, attendee)

        assert isinstance(result.timezone_offset_hours, int)

    async def test_non_utc_timezone_still_returns_zero(self, engine):
        """Timezones that previously had non-zero offsets now return 0."""
        for tz in ("Asia/Kolkata", "America/Los_Angeles", "Europe/London", "Pacific/Auckland"):
            attendee = make_attendee(timezone_str=tz)
            booking = {"id": "booking-tz"}
            result = await engine._analyze_timing(booking, attendee)
            assert result.timezone_offset_hours == 0, f"Expected 0 for {tz}, got {result.timezone_offset_hours}"

    async def test_invalid_timezone_returns_zero(self, engine):
        """Invalid timezone strings used to trigger a zoneinfo exception; now return 0 cleanly."""
        attendee = make_attendee(timezone_str="Invalid/Timezone")
        booking = {"id": "booking-invalid-tz"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.timezone_offset_hours == 0

    async def test_empty_timezone_returns_zero(self, engine):
        """Empty timezone string should not raise and returns offset 0."""
        attendee = make_attendee(timezone_str="")
        booking = {"id": "booking-empty-tz"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.timezone_offset_hours == 0

    async def test_optimal_send_time_is_iso_string(self, engine):
        """optimal_send_time should be a valid ISO 8601 timestamp string."""
        attendee = make_attendee()
        booking = {"id": "booking-time"}

        result = await engine._analyze_timing(booking, attendee)

        # Should parse without raising
        parsed = datetime.fromisoformat(result.optimal_send_time)
        assert parsed is not None

    async def test_expected_response_time_matches_attendee(self, engine):
        """expected_response_time_hours must mirror the attendee's avg_response_time_hours."""
        attendee = make_attendee(avg_response_time_hours=4.5)
        booking = {"id": "booking-response"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.expected_response_time_hours == 4.5

    async def test_urgency_level_is_medium(self, engine):
        """urgency_level is hardcoded to 'medium' after the PR."""
        attendee = make_attendee()
        booking = {"id": "booking-urgency"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.urgency_level == "medium"

    async def test_business_hours_aligned_is_true(self, engine):
        """business_hours_aligned is hardcoded to True after the PR."""
        attendee = make_attendee()
        booking = {"id": "booking-biz"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.business_hours_aligned is True

    async def test_returns_timing_analysis_instance(self, engine):
        """_analyze_timing must return a TimingAnalysis dataclass instance."""
        attendee = make_attendee()
        booking = {"id": "booking-type"}

        result = await engine._analyze_timing(booking, attendee)

        assert isinstance(result, TimingAnalysis)

    async def test_empty_booking_dict(self, engine):
        """_analyze_timing must not raise when booking dict is empty."""
        attendee = make_attendee()
        booking = {}

        result = await engine._analyze_timing(booking, attendee)

        assert result.timezone_offset_hours == 0

    async def test_none_avg_response_time_propagated(self, engine):
        """avg_response_time_hours=0 (boundary) propagates correctly."""
        attendee = make_attendee(avg_response_time_hours=0.0)
        booking = {"id": "booking-zero-response"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.expected_response_time_hours == 0.0