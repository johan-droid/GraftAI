import re

with open("backend/worker.py", "r") as f:
    content = f.read()

# Fix the exact indentation errors from lines 215-240
fixed_content = content.replace(
"""        try:
                if email_type == "confirmation":
                await notify_event_created([booking.email], [], payload)
            elif email_type == "new_booking":
                organizer_email = payload.get("organizer_email")
                if organizer_email:
                    await send_custom_notification(
                        [organizer_email],
                        [],
                        subject=f"New Booking: {event.title}",
                        html_body=f"<p>A new booking has been scheduled for <strong>{event.title}</strong> on {payload['start_time']}.</p>",
                    )
                    else:
                        logger.warning(
                            "Missing organizer_email for new_booking job %s", booking_id
                        )
            elif email_type == "reminder":
                await notify_event_updated([booking.email], [], payload)
            elif email_type == "cancellation":
                await notify_event_deleted([booking.email], [], payload)
            else:
                logger.warning(
                    "Unknown email_type '%s' for booking %s", email_type, booking_id
                )
        except Exception as e:  # noqa: BLE001 - log failures in background email tasks
            logger.exception("Failed to send %s email for booking %s", email_type, booking_id)""",
"""        try:
            if email_type == "confirmation":
                await notify_event_created([booking.email], [], payload)
            elif email_type == "new_booking":
                organizer_email = payload.get("organizer_email")
                if organizer_email:
                    await send_custom_notification(
                        [organizer_email],
                        [],
                        subject=f"New Booking: {event.title}",
                        html_body=f"<p>A new booking has been scheduled for <strong>{event.title}</strong> on {payload['start_time']}.</p>",
                    )
                else:
                    logger.warning(
                        "Missing organizer_email for new_booking job %s", booking_id
                    )
            elif email_type == "reminder":
                await notify_event_updated([booking.email], [], payload)
            elif email_type == "cancellation":
                await notify_event_deleted([booking.email], [], payload)
            else:
                logger.warning(
                    "Unknown email_type '%s' for booking %s", email_type, booking_id
                )
        except Exception as e:  # noqa: BLE001 - log failures in background email tasks
            logger.exception("Failed to send %s email for booking %s", email_type, booking_id)""")

with open("backend/worker.py", "w") as f:
    f.write(fixed_content)
