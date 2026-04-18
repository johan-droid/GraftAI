"""
Email sending tasks for transactional emails.
"""

import asyncio
from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger
from backend.services.mail_service import send_email

logger = get_logger(__name__)


def _run_email_send(to_email: str, subject: str, html_body: str, text_body: str = None):
    try:
        asyncio.run(send_email(to_email, subject, html_body, text_body))
    except RuntimeError:
        # If there is already a running event loop, fallback to a synchronous no-op.
        logger.warning(
            "Async email send skipped because event loop is already running."
        )


def _build_email_message(subject: str, body: str) -> tuple[str, str]:
    html_body = f"<html><body><p>{body.replace('\n', '<br>')}</p></body></html>"
    text_body = body
    return subject, html_body, text_body


class EmailService:
    def send_booking_confirmation(
        self,
        to_email: str,
        to_name: str,
        meeting_title: str,
        start_time: str,
        end_time: str,
        meeting_url: str = None,
        location: str = None,
    ):
        subject = f"Booking confirmed: {meeting_title}"
        body = (
            f"Hello {to_name},\n\n"
            f"Your booking '{meeting_title}' is confirmed for {start_time}"
            f" to {end_time}.\n"
            f"Location: {location or 'N/A'}\n"
            f"Join at: {meeting_url or 'TBD'}\n"
        )
        subject, html_body, text_body = _build_email_message(subject, body)
        _run_email_send(to_email, subject, html_body, text_body)
        return {"success": True, "message_id": None}

    def send_cancellation_notice(
        self,
        to_email: str,
        to_name: str,
        meeting_title: str,
        start_time: str,
        reason: str = None,
    ):
        subject = f"Booking cancelled: {meeting_title}"
        body = (
            f"Hello {to_name},\n\n"
            f"Your booking '{meeting_title}' scheduled for {start_time} has been cancelled.\n"
            f"Reason: {reason or 'No reason provided'}\n"
        )
        subject, html_body, text_body = _build_email_message(subject, body)
        _run_email_send(to_email, subject, html_body, text_body)
        return {"success": True, "message_id": None}

    def send_reminder(
        self,
        to_email: str,
        to_name: str,
        meeting_title: str,
        start_time: str,
        meeting_url: str = None,
    ):
        subject = f"Reminder: {meeting_title}"
        body = (
            f"Hello {to_name},\n\n"
            f"This is a reminder that your booking '{meeting_title}' starts at {start_time}.\n"
            f"Join at: {meeting_url or 'TBD'}\n"
        )
        subject, html_body, text_body = _build_email_message(subject, body)
        _run_email_send(to_email, subject, html_body, text_body)
        return {"success": True, "message_id": None}

    def send_team_invitation(
        self,
        to_email: str,
        inviter_name: str,
        team_name: str,
        invite_token: str,
        to_name: str = None,
    ):
        subject = f"You're invited to join {team_name}"
        body = (
            f"Hello {to_name or 'there'},\n\n"
            f"{inviter_name} invited you to join {team_name}.\n"
            f"Accept invite using token: {invite_token}\n"
        )
        subject, html_body, text_body = _build_email_message(subject, body)
        _run_email_send(to_email, subject, html_body, text_body)
        return {"success": True, "message_id": None}

    def send_password_reset(
        self, to_email: str, reset_token: str, user_name: str = None
    ):
        subject = "Password reset request"
        body = (
            f"Hello {user_name or 'there'},\n\n"
            f"Use this token to reset your password: {reset_token}\n"
        )
        subject, html_body, text_body = _build_email_message(subject, body)
        _run_email_send(to_email, subject, html_body, text_body)
        return {"success": True, "message_id": None}


email_service = EmailService()


@celery_app.task(bind=True, max_retries=3)
def send_booking_confirmation(
    self,
    booking_id: str,
    attendee_email: str,
    attendee_name: str,
    meeting_title: str,
    start_time: str,
    end_time: str,
    meeting_url: str = None,
    location: str = None,
):
    """Send booking confirmation email."""
    try:
        logger.info(f"Sending booking confirmation to {attendee_email}")

        result = email_service.send_booking_confirmation(
            to_email=attendee_email,
            to_name=attendee_name,
            meeting_title=meeting_title,
            start_time=start_time,
            end_time=end_time,
            meeting_url=meeting_url,
            location=location,
        )

        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send booking confirmation: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_booking_cancellation(
    self,
    booking_id: str,
    attendee_email: str,
    attendee_name: str,
    meeting_title: str,
    start_time: str,
    cancellation_reason: str = None,
):
    """Send booking cancellation email."""
    try:
        logger.info(f"Sending cancellation notice to {attendee_email}")

        result = email_service.send_cancellation_notice(
            to_email=attendee_email,
            to_name=attendee_name,
            meeting_title=meeting_title,
            start_time=start_time,
            reason=cancellation_reason,
        )

        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send cancellation notice: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_reminder_email(
    self,
    booking_id: str,
    attendee_email: str,
    attendee_name: str,
    meeting_title: str,
    start_time: str,
    meeting_url: str = None,
):
    """Send reminder email before meeting."""
    try:
        logger.info(f"Sending reminder to {attendee_email}")

        result = email_service.send_reminder(
            to_email=attendee_email,
            to_name=attendee_name,
            meeting_title=meeting_title,
            start_time=start_time,
            meeting_url=meeting_url,
        )

        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send reminder: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_team_invitation(
    self,
    team_id: str,
    invitee_email: str,
    invitee_name: str,
    inviter_name: str,
    team_name: str,
    invite_token: str,
):
    """Send team invitation email."""
    try:
        logger.info(f"Sending team invitation to {invitee_email}")

        result = email_service.send_team_invitation(
            to_email=invitee_email,
            to_name=invitee_name,
            inviter_name=inviter_name,
            team_name=team_name,
            invite_token=invite_token,
        )

        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send team invitation: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_password_reset(self, email: str, reset_token: str, user_name: str = None):
    """Send password reset email."""
    try:
        logger.info(f"Sending password reset to {email}")

        result = email_service.send_password_reset(
            to_email=email, user_name=user_name, reset_token=reset_token
        )

        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send password reset: {exc}")
        raise self.retry(exc=exc, countdown=60)
