import sys
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import unittest
from dataclasses import dataclass

# Mocking modules
sys.modules['dotenv'] = MagicMock()
sys.modules['backend.utils.db'] = MagicMock()
sys.modules['backend.utils.logger'] = MagicMock()
sys.modules['backend.ai.tools.registry'] = MagicMock()

class RiskLevel(unittest.mock.MagicMock): pass
class VIPLevel(unittest.mock.MagicMock): pass

@dataclass
class AttendeeAnalysis:
    email: str
    vip_level: any
    is_new: bool
    booking_frequency: int
    no_show_rate: float
    avg_response_time_hours: float
    preferred_communication: list
    engagement_score: float
    timezone: str

@dataclass
class TimingAnalysis:
    optimal_send_time: str
    timezone_offset_hours: int
    expected_response_time_hours: float
    urgency_level: str
    business_hours_aligned: bool

class DecisionEngine:
    def __init__(self):
        self.risk_thresholds = {"timezone_diff": 6}

    def _get_timezone_offset(self, timezone_name: str) -> int:
        try:
            tz = ZoneInfo(timezone_name)
            now = datetime.now(tz)
            offset_seconds = now.utcoffset().total_seconds()
            return int(offset_seconds / 3600)
        except Exception:
            return 0

    def _calculate_optimal_send_time(self, current_time: datetime, timezone_offset: int) -> datetime:
        local_time = current_time + timedelta(hours=timezone_offset)
        business_start = 9
        business_end = 17
        optimal_local = local_time
        if local_time.hour < business_start:
            optimal_local = local_time.replace(hour=business_start, minute=0, second=0)
        elif local_time.hour >= business_end:
            optimal_local = (local_time + timedelta(days=1)).replace(hour=business_start, minute=0, second=0)
        return optimal_local - timedelta(hours=timezone_offset)

    async def _analyze_timing(self, booking: dict, attendee: AttendeeAnalysis) -> TimingAnalysis:
        now_utc = datetime.now(timezone.utc)
        timezone_offset_hours = self._get_timezone_offset(attendee.timezone)
        optimal_send_dt = self._calculate_optimal_send_time(now_utc, timezone_offset_hours)
        optimal_time = optimal_send_dt.isoformat()
        local_now = now_utc + timedelta(hours=timezone_offset_hours)
        business_hours_aligned = 9 <= local_now.hour < 17
        return TimingAnalysis(
            optimal_send_time=optimal_time,
            timezone_offset_hours=timezone_offset_hours,
            expected_response_time_hours=attendee.avg_response_time_hours,
            urgency_level="medium",
            business_hours_aligned=business_hours_aligned,
        )

class TestLogic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = DecisionEngine()

    async def test_analyze_timing_logic(self):
        attendee = AttendeeAnalysis(
            email="test@example.com",
            vip_level=None,
            is_new=False,
            booking_frequency=5,
            no_show_rate=0.1,
            avg_response_time_hours=1.5,
            preferred_communication=["email"],
            engagement_score=0.8,
            timezone="Asia/Kolkata",
        )
        result = await self.engine._analyze_timing({}, attendee)
        self.assertEqual(result.timezone_offset_hours, 5)

        # Test business hours alignment
        now_utc = datetime.now(timezone.utc)
        local_now = now_utc + timedelta(hours=5)
        expected_biz = 9 <= local_now.hour < 17
        self.assertEqual(result.business_hours_aligned, expected_biz)

if __name__ == "__main__":
    unittest.main()
