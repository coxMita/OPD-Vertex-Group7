"""Inbound queue message handling for email-service."""

import json
import logging

import aio_pika
from pydantic import ValidationError

from src.models.dto.email_event import EmailEvent
from src.services.email_service import EmailService

logger = logging.getLogger(__name__)

_email_service = EmailService()


async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Process an incoming email message from RabbitMQ."""
    async with message.process(ignore_processed=True):
        try:
            body = message.body.decode()
            data = json.loads(body)
            event = EmailEvent(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error("Invalid message format: %s", e)
            await message.reject(requeue=False)
            return

        try:
            await _email_service.handle_event(event)
            await message.ack()
        except Exception as e:
            logger.error("Error sending email: %s", e)
            await message.nack(requeue=True)
