"""Application service: turn queue events into sent mail."""

import logging

from src.models.dto.email_event import EmailEvent
from src.services.pdf_generator import generate_pdf
from src.services.smtp_delivery import send_email

logger = logging.getLogger(__name__)


class EmailService:
    """Orchestrates optional PDF attachments and SMTP delivery."""

    async def handle_event(self, event: EmailEvent) -> None:
        """Process a validated email event: attachments, then send."""
        attachments = None
        if event.document_title and event.document_content:
            pdf_bytes = generate_pdf(event.document_title, event.document_content)
            filename = f"{event.document_title.replace(' ', '_')}.pdf"
            attachments = [(filename, pdf_bytes)]

        await send_email(
            to_email=event.to_email,
            subject=event.subject,
            message=event.message,
            is_html=event.is_html,
            attachments=attachments,
        )
        logger.info("Successfully processed email request for %s", event.to_email)
