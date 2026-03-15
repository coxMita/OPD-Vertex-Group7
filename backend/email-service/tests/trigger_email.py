import asyncio
import json
import logging

import aio_pika

from src.config import settings

logging.basicConfig(level=logging.INFO)

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
            "subject": "System Test: RabbitMQ Integration works!",
            "message": (
                "Hello! If you are reading this, the RabbitMQ message broker "
                "successfully routed the event to the email-service container, "
                "which then sent this real email."
            ),
            "is_html": False
        }

        message_body = json.dumps(email_event).encode()

        # 4. Publish the message directly to the "email_queue"
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key="email_queue",
        )

        print("✅ Successfully published test message to RabbitMQ 'email_queue'!")
        print(
            f"Waiting for the email-service container to pick it up and email "
            f"{settings.SMTP_FROM_EMAIL}..."
        )

if __name__ == "__main__":
    asyncio.run(main())
