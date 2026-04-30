import asyncio
from backend.ai.decision_engine import DecisionEngine, AttendeeAnalysis, VIPLevel

async def main():
    engine = DecisionEngine()
    attendee = AttendeeAnalysis(
        email="test@example.com",
        vip_level=VIPLevel.STANDARD,
        is_new=False,
        booking_frequency=5,
        no_show_rate=0.1,
        avg_response_time_hours=1.5,
        preferred_communication=["email"],
        engagement_score=0.8,
        timezone="America/New_York",
    )
    booking = {"id": "123"}
    timing = await engine._analyze_timing(booking, attendee)
    print("NY offset:", timing.timezone_offset_hours)

    attendee.timezone = "Asia/Kolkata"
    timing = await engine._analyze_timing(booking, attendee)
    print("IST offset:", timing.timezone_offset_hours)

    attendee.timezone = "Invalid/Timezone"
    timing = await engine._analyze_timing(booking, attendee)
    print("Invalid offset:", timing.timezone_offset_hours)

asyncio.run(main())
