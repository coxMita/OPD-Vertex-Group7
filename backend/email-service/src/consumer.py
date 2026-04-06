import json
import logging

import aio_pika
from pydantic import BaseModel, ValidationError

from src.config import settings
from src.email_sender import send_email
from src.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)


class EmailEvent(BaseModel):
    """Event model for incoming email messages."""

    to_email: str
    subject: str
    message: str
    is_html: bool = False
    document_title: str | None = None
    document_content: dict | str | None = None


async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Process an incoming email message from RabbitMQ."""
    async with message.process(ignore_processed=True):
        try:
            body = message.body.decode()
            data = json.loads(body)
            event = EmailEvent(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Invalid message format: {e}")
            await message.reject(requeue=False)
            return

        try:
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
            logger.info(f"Successfully processed email request for {event.to_email}")
            await message.ack()
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            await message.nack(requeue=True)


async def start_consumer() -> aio_pika.RobustConnection:
    """Start the RabbitMQ consumer and return the connection."""
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()

    # Set prefetch count for fair dispatch
    await channel.set_qos(prefetch_count=10)

    # Declare queue
    queue = await channel.declare_queue("email_queue", durable=True)

    # Start consuming
    await queue.consume(process_message)
    logger.info("Started RabbitMQ consumer on queue 'email_queue'")

    return connection
