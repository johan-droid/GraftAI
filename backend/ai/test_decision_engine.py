import asyncio

from backend.ai.decision_engine import AttendeeAnalysis, DecisionEngine, VIPLevel


async def main():
    engine = DecisionEngine()
    attendee = AttendeeAnalysis(email="test@example.com", vip_level=VIPLevel.STANDARD, is_new=False, booking_frequency=5, no_show_rate=0.1, avg_response_time_hours=1.5, preferred_communication=["email"], engagement_score=0.8, timezone="America/New_York")
    booking = {"id": "123"}
    await engine._analyze_timing(booking, attendee)
    attendee.timezone = "Asia/Kolkata"
    await engine._analyze_timing(booking, attendee)
    attendee.timezone = "Invalid/Timezone"
    await engine._analyze_timing(booking, attendee)
asyncio.run(main())
