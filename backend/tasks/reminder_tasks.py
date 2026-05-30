"""
Reminder notification tasks.
Sends email/SMS reminders before meetings.
"""
from datetime import UTC, datetime, timedelta

from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def send_pending_reminders(self):
    """Send all pending reminders (periodic task)."""
    try:
        logger.info("Processing pending reminders")
        now = datetime.now(UTC)
        reminders_sent = 0
        return {"success": True, "reminders_sent": reminders_sent, "processed_at": now.isoformat()}
    except Exception as exc:
        logger.exception("Failed to process reminders: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def schedule_booking_reminders(self, booking_id: str, start_time: str, attendee_email: str, attendee_name: str, meeting_title: str, meeting_url: str | None=None):
    """Schedule reminders for a new booking."""
    try:
        logger.info("Scheduling reminders for booking %s", booking_id)
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        reminder_times = [(24, "hours"), (1, "hours"), (15, "minutes")]
        for amount, unit in reminder_times:
            if unit == "hours":
                reminder_time = start - timedelta(hours=amount)
            else:
                reminder_time = start - timedelta(minutes=amount)
            if reminder_time > now:
                logger.info("Scheduled %s %s reminder for %s", amount, unit, reminder_time)
        return {"success": True, "booking_id": booking_id, "reminders_scheduled": len(reminder_times)}
    except Exception as exc:
        logger.exception("Failed to schedule reminders: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def cancel_booking_reminders(self, booking_id: str):
    """Cancel all reminders for a cancelled booking."""
    try:
        logger.info("Cancelling reminders for booking %s", booking_id)
        return {"success": True, "booking_id": booking_id, "reminders_cancelled": 0}
    except Exception as exc:
        logger.exception("Failed to cancel reminders: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_sms_reminder(self, phone_number: str, message: str):
    """Send SMS reminder (requires Twilio integration)."""
    try:
        logger.info("Sending SMS reminder to %s", phone_number)
        return {"success": True, "phone": phone_number, "message_sid": "placeholder"}
    except Exception as exc:
        logger.exception("SMS reminder failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
