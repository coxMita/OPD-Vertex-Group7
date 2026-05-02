"""Facade for the email work queue (default exchange → durable queue)."""

import logging

import aio_pika

from src.messaging.email_queue_handler import process_message

logger = logging.getLogger(__name__)


class EmailQueueFacade:
    """Connect to AMQP, declare the email queue, and run the consumer."""

    def __init__(self, amqp_url: str, queue_name: str) -> None:
        """Store broker URL and queue name."""
        self._amqp_url = amqp_url
        self._queue_name = queue_name
        self._connection: aio_pika.RobustConnection | None = None

    @property
    def queue_name(self) -> str:
        """Return the durable queue name (parallel to exchange_name on PubSub)."""
        return self._queue_name

    async def connect_and_consume(self) -> aio_pika.RobustConnection:
        """Open a connection, declare the queue, attach consumer; return connection."""
        self._connection = await aio_pika.connect_robust(self._amqp_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(self._queue_name, durable=True)
        await queue.consume(process_message)
        logger.info("Started RabbitMQ consumer on queue '%s'", self._queue_name)
        return self._connection

    async def close(self) -> None:
        """Close the broker connection."""
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
