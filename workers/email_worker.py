import smtplib
from email.mime.text import MIMEText
from workers.celery_app import celery_app
from config.settings import settings


@celery_app.task(name="workers.send_email_task", bind=True, max_retries=3)
def send_email_task(self, recipient: str, subject: str, body: str) -> dict:
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        return {"status": "skipped", "reason": "SMTP credentials not set in .env"}

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = recipient

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return {"status": "sent", "recipient": recipient}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=15)
