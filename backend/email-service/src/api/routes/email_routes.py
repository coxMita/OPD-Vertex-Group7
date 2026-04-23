"""HTTP routes for email-service."""

import json

import aio_pika
from fastapi import APIRouter, Request

from src.config import settings
from src.models.dto.email_event import EmailEvent

router = APIRouter(prefix="/api", tags=["email"])


@router.post("/send", status_code=202)
async def send_test_email(request: Request, event: EmailEvent) -> dict[str, str]:
    """Test endpoint: publish an email event to the queue (same path as worker)."""
    connection = request.app.state.rabbitmq_connection
    channel = await connection.channel()

    message_body = json.dumps(event.model_dump()).encode()

    await channel.default_exchange.publish(
        aio_pika.Message(body=message_body),
        routing_key=settings.EMAIL_QUEUE_NAME,
    )
    return {"status": "accepted", "message": "Email event published to queue."}
