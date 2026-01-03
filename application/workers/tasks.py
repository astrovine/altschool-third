from application.workers.celery_app import celery_app
from application.utilities.logging import logger


@celery_app.task(bind=True, max_retries=3)
def send_invitation_email(self, email: str, event_title: str, organizer_name: str) -> dict:
    try:
        logger.info(
            "Sending invitation email",
            extra={
                "email": email,
                "event_title": event_title,
                "organizer_name": organizer_name,
            },
        )
        return {
            "status": "sent",
            "email": email,
            "event_title": event_title,
        }
    except Exception as exc:
        logger.error(f"Failed to send invitation email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_rsvp_confirmation(self, email: str, event_title: str, status: str) -> dict:
    try:
        logger.info(
            "Sending RSVP confirmation",
            extra={
                "email": email,
                "event_title": event_title,
                "status": status,
            },
        )
        return {
            "status": "sent",
            "email": email,
            "event_title": event_title,
            "rsvp_status": status,
        }
    except Exception as exc:
        logger.error(f"Failed to send RSVP confirmation: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_event_reminder(self, emails: list[str], event_title: str, event_date: str) -> dict:
    try:
        logger.info(
            "Sending event reminder",
            extra={
                "recipient_count": len(emails),
                "event_title": event_title,
                "event_date": event_date,
            },
        )
        return {
            "status": "sent",
            "recipient_count": len(emails),
            "event_title": event_title,
        }
    except Exception as exc:
        logger.error(f"Failed to send event reminder: {exc}")
        raise self.retry(exc=exc, countdown=60)
