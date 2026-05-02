"""SMTP email delivery (transport layer)."""

import logging
from email.message import EmailMessage

import aiosmtplib

from src.config import settings

logger = logging.getLogger(__name__)

SMTP_SSL_PORT = 465


async def send_email(
    to_email: str,
    subject: str,
    message: str,
    is_html: bool = False,
    attachments: list[tuple[str, bytes]] | None = None,
) -> None:
    """Send an email using configured SMTP settings."""
    email_msg = EmailMessage()
    email_msg["From"] = settings.SMTP_FROM_EMAIL
    email_msg["To"] = to_email
    email_msg["Subject"] = subject

    if is_html:
        email_msg.set_content("Please enable HTML viewing to see this email.")
        email_msg.add_alternative(message, subtype="html")
    else:
        email_msg.set_content(message)

    if attachments:
        for filename, content in attachments:
            email_msg.add_attachment(
                content, maintype="application", subtype="pdf", filename=filename
            )

    use_tls = settings.SMTP_USE_TLS and settings.SMTP_PORT == SMTP_SSL_PORT
    start_tls = settings.SMTP_USE_TLS and settings.SMTP_PORT != SMTP_SSL_PORT

    smtp_kwargs: dict = {
        "hostname": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "use_tls": use_tls,
        "start_tls": start_tls,
    }
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        smtp_kwargs["username"] = settings.SMTP_USER
        smtp_kwargs["password"] = settings.SMTP_PASSWORD

    try:
        await aiosmtplib.send(email_msg, **smtp_kwargs)
        logger.info("Email sent to %s with subject '%s'", to_email, subject)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        raise
