"""Facade for subscribing to appointment status changes."""

import logging

import aio_pika

from src.messaging.appointment_handler import process_appointment_message

logger = logging.getLogger(__name__)


class AppointmentSubscriberFacade:
    """Connect to AMQP, bind a queue to the fanout exchange, and consume."""

    def __init__(self, amqp_url: str) -> None:
        """Store broker URL."""
        self._amqp_url = amqp_url
        self._connection: aio_pika.RobustConnection | None = None
        self._queue_name = "email_service_appointment_status"
        self._exchange_name = "appointment.status_changed"

    @property
    def queue_name(self) -> str:
        """Return the queue name."""
        return self._queue_name

    async def connect_and_consume(self) -> aio_pika.RobustConnection:
        """Open connection, declare exchange, bind queue, and consume."""
        self._connection = await aio_pika.connect_robust(self._amqp_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
        )
        created_exchange = await channel.declare_exchange(
            "appointment.created", aio_pika.ExchangeType.FANOUT, durable=True
        )

        queue = await channel.declare_queue(self._queue_name, durable=True)
        await queue.bind(exchange)
        await queue.bind(created_exchange)

        await queue.consume(process_appointment_message)
        logger.info(
            "Started RabbitMQ consumer on exchanges '%s' and "
            "'appointment.created' via queue '%s'",
            self._exchange_name,
            self._queue_name,
        )
        return self._connection

    async def close(self) -> None:
        """Close the broker connection."""
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
