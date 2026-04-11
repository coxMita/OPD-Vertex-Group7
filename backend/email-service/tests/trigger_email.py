import asyncio
import json
import sys
from pathlib import Path

import aio_pika

# Add the parent directory to sys.path so 'src' can be imported when running as a script
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings


async def main() -> None:
    """Trigger an email via RabbitMQ."""
    print(f"Connecting to RabbitMQ at {settings.RABBITMQ_URL}...")

    # 1. Connect to RabbitMQ
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    async with connection:
        # 2. Open a channel
        channel = await connection.channel()

        # 3. Define the event data matching what the other services will send
        # We'll send it to the FROM email address just to test that it arrives
        email_event = {
            "to_email": settings.SMTP_FROM_EMAIL,
            "subject": "System Test: PDF Generation & Attachment Works!",
            "message": (
                "Hello! If you are reading this and see a PDF attached, "
                "the RabbitMQ message broker successfully routed the event to "
                "the email-service container, generated the PDF on the fly, "
                "and sent it."
            ),
            "is_html": False,
            "document_title": "Mock Prescription",
            "document_content": {
                "Patient Name": "John Doe",
                "Medication": "Amoxicillin 500mg",
                "Dosage": "1 capsule three times a day for 7 days",
                "Doctor Notes": "Take with food.",
            },
        }

        message_body = json.dumps(email_event).encode()

        # 4. Publish the message to the configured email queue
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key=settings.EMAIL_QUEUE_NAME,
        )

        print(
            "Successfully published test message to RabbitMQ "
            f"'{settings.EMAIL_QUEUE_NAME}'!"
        )
        print(
            f"Waiting for the email-service container to pick it up and email "
            f"{settings.SMTP_FROM_EMAIL}..."
        )

        # Add a short delay to allow the network buffer to flush to RabbitMQ
        # before the async with context manager closes the connection immediately.
        await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(main())
