import asyncio
import json
import sys
import argparse
from pathlib import Path

import aio_pika

# Add the parent directory to sys.path so 'src' can be imported when running as a script
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings


async def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger test emails via RabbitMQ.")
    parser.add_argument(
        "--email", 
        type=str, 
        help="The destination email address to verify delivery.",
        required=True
    )
    args = parser.parse_args()
    target_email = args.email

    print(f"Connecting to RabbitMQ at {settings.RABBITMQ_URL}...")

    # 1. Connect to RabbitMQ
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    async with connection:
        # 2. Open a channel
        channel = await connection.channel()

        # 3. Define the Appointment Booking Email Event
        appointment_event = {
            "to_email": target_email,
            "subject": "Appointment Confirmation",
            "message": (
                "Hello!\n\n"
                "Your appointment has been successfully booked.\n"
                "This message verifies that the email service processes plain text "
                "emails correctly after the refactoring."
            ),
            "is_html": False,
        }

        # 4. Define the Prescription PDF Email Event
        prescription_event = {
            "to_email": target_email,
            "subject": "Your Prescription Details",
            "message": (
                "Hello! If you are reading this and see a PDF attached, "
                "the RabbitMQ message broker successfully routed the event to "
                "the email-service container, generated the PDF on the fly, "
                "and sent it."
            ),
            "is_html": False,
            "document_title": "Mock Prescription",
            "document_content": {
                "Patient Name": "Jane Doe",
                "Medication": "Amoxicillin 500mg",
                "Dosage": "1 capsule three times a day for 7 days",
                "Doctor Notes": "Take with food.",
            },
        }

        # 5. Publish the messages to the configured email queue
        print(f"Publishing Appointment message to {target_email}...")
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(appointment_event).encode()),
            routing_key=settings.EMAIL_QUEUE_NAME,
        )

        print(f"Publishing Prescription (PDF) message to {target_email}...")
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(prescription_event).encode()),
            routing_key=settings.EMAIL_QUEUE_NAME,
        )

        print("Successfully published both test messages to RabbitMQ!")
        print("Waiting for the email-service container to process them...")

        # Add a short delay to allow the network buffer to flush to RabbitMQ
        await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(main())
