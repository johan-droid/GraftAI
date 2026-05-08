"""
Unit tests for DecisionEngine changes introduced in this PR:
- TimingAnalysis.timezone_offset_hours changed from float to int
- _analyze_timing now uses dynamic timezone calculation
- zoneinfo import used for modern timezone handling
"""

import pytest
from datetime import datetime, timezone

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

    async def test_timezone_offset_is_calculated(self, engine):
        """Test that timezone_offset_hours is correctly calculated for attendees."""
        attendee = make_attendee(timezone_str="America/New_York")
        booking = {"id": "booking-1"}

        result = await engine._analyze_timing(booking, attendee)

        assert result.timezone_offset_hours in [-5, -4]

    async def test_timezone_offset_is_int_not_float(self, engine):
        """timezone_offset_hours must be an int, not a float."""
        attendee = make_attendee(timezone_str="Asia/Tokyo")
        booking = {"id": "booking-2"}

        result = await engine._analyze_timing(booking, attendee)

        assert isinstance(result.timezone_offset_hours, int)

    async def test_non_utc_timezone_returns_correct_offset(self, engine):
        """Timezones should return their actual offsets."""
        test_cases = [
            ("Asia/Kolkata", 5),
            ("UTC", 0),
        ]
        for tz, expected in test_cases:
            attendee = make_attendee(timezone_str=tz)
            booking = {"id": "booking-tz"}
            result = await engine._analyze_timing(booking, attendee)
            assert result.timezone_offset_hours == expected, f"Expected {expected} for {tz}, got {result.timezone_offset_hours}"

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

    async def test_business_hours_aligned_reflects_current_time(self, engine):
        """business_hours_aligned should reflect if current time is within business hours."""
        attendee = make_attendee(timezone_str="UTC")
        booking = {"id": "booking-biz"}

        result = await engine._analyze_timing(booking, attendee)

        from datetime import datetime, timezone
        now_hour = datetime.now(timezone.utc).hour
        expected = 9 <= now_hour < 17
        assert result.business_hours_aligned is expected

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