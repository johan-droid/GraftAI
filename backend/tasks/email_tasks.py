"""
Email sending tasks for transactional emails.
"""
from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger
from backend.services.email_service import EmailService

logger = get_logger(__name__)
email_service = EmailService()


@celery_app.task(bind=True, max_retries=3)
def send_booking_confirmation(self, booking_id: str, attendee_email: str, attendee_name: str, 
                               meeting_title: str, start_time: str, end_time: str, 
                               meeting_url: str = None, location: str = None):
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
            location=location
        )
        
        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send booking confirmation: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_booking_cancellation(self, booking_id: str, attendee_email: str, attendee_name: str,
                               meeting_title: str, start_time: str, cancellation_reason: str = None):
    """Send booking cancellation email."""
    try:
        logger.info(f"Sending cancellation notice to {attendee_email}")
        
        result = email_service.send_cancellation_notice(
            to_email=attendee_email,
            to_name=attendee_name,
            meeting_title=meeting_title,
            start_time=start_time,
            reason=cancellation_reason
        )
        
        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send cancellation notice: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_reminder_email(self, booking_id: str, attendee_email: str, attendee_name: str,
                         meeting_title: str, start_time: str, meeting_url: str = None):
    """Send reminder email before meeting."""
    try:
        logger.info(f"Sending reminder to {attendee_email}")
        
        result = email_service.send_reminder(
            to_email=attendee_email,
            to_name=attendee_name,
            meeting_title=meeting_title,
            start_time=start_time,
            meeting_url=meeting_url
        )
        
        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send reminder: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_team_invitation(self, team_id: str, invitee_email: str, invitee_name: str,
                          inviter_name: str, team_name: str, invite_token: str):
    """Send team invitation email."""
    try:
        logger.info(f"Sending team invitation to {invitee_email}")
        
        result = email_service.send_team_invitation(
            to_email=invitee_email,
            to_name=invitee_name,
            inviter_name=inviter_name,
            team_name=team_name,
            invite_token=invite_token
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
            to_email=email,
            user_name=user_name,
            reset_token=reset_token
        )
        
        return {"success": True, "message_id": result}
    except Exception as exc:
        logger.error(f"Failed to send password reset: {exc}")
        raise self.retry(exc=exc, countdown=60)
