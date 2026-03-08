"""PubSub facade for ai-service — mirrors the transcription-service pattern."""

import asyncio
import logging
from asyncio import AbstractEventLoop
from contextlib import suppress
from typing import Any, Awaitable, Callable, TypeVar

import aio_pika
from aio_pika.abc import AbstractRobustQueue

from src.models.msg.abstract_message import AbstractMessage

MessageType = TypeVar("MessageType", bound=AbstractMessage)

logger = logging.getLogger(__name__)


class PubSubFacade:
    """Facade for publishing and subscribing to messages via a fanout exchange."""

    def __init__(self, amqp_url: str, exchange_name: str) -> None:
        """Initialise the facade with AMQP URL and exchange name."""
        self._amqp_url = amqp_url
        self._exchange_name = exchange_name
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None
        self._exchange: aio_pika.Exchange | None = None
        try:
            self._loop: AbstractEventLoop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
        self._consumer_task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Establish connection to the AMQP broker and declare a fanout exchange."""
        self._loop = asyncio.get_running_loop()
        self._connection = await aio_pika.connect_robust(
            self._amqp_url,
            loop=self._loop,
        )
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
        )

    async def close(self) -> None:
        """Close connections and cancel running consumer task."""
        await self._cancel_consumer_task()
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def _cancel_consumer_task(self) -> None:
        """Cancel the consumer task if it is running."""
        if self._consumer_task is not None:
            self._consumer_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._consumer_task
            self._consumer_task = None

    async def publish(self, message: AbstractMessage) -> None:
        """Publish a message to all subscribers.

        Args:
            message: The message to publish.

        Raises:
            RuntimeError: If the exchange is not initialised.

        """
        if not self._exchange:
            raise RuntimeError("Exchange not declared; call 'connect' first.")
        amqp_message = aio_pika.Message(
            body=message.to_bytes(), content_type="application/json"
        )
        await self._exchange.publish(amqp_message, routing_key="")
        logger.info("Published message: %s", amqp_message.body)

    def subscribe(
        self,
        queue_name: str,
        on_message: Callable[[Any], Awaitable[Any]],
        message_class: type[MessageType] | None,
    ) -> None:
        """Subscribe to messages broadcasted on the fanout exchange.

        Args:
            queue_name: Durable queue name for this consumer.
            on_message: Async callback invoked for each message.
            message_class: Message type for deserialisation (or None for raw bytes).

        Raises:
            RuntimeError: If connect() has not been called yet.

        """
        if not self._exchange or not self._channel:
            raise RuntimeError(
                "Exchange or channel not declared; call 'connect' first."
            )
        if self._consumer_task is not None and not self._consumer_task.done():
            return

        self._consumer_task = self._loop.create_task(
            self._consume(queue_name, on_message, message_class)
        )

    async def _consume(
        self,
        queue_name: str,
        on_message: Callable[[Any], Awaitable[Any]],
        message_class: type[AbstractMessage] | None,
    ) -> None:
        """Consume messages from the specified queue."""
        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(self._exchange)
        await self._consume_messages(message_class, on_message, queue)

    @staticmethod
    async def _consume_messages(
        message_class: type[AbstractMessage] | None,
        on_message: Callable[[Any], Awaitable[Any]],
        queue: AbstractRobustQueue,
    ) -> None:
        """Process messages from the queue."""
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        logger.info("Received message: %s", message.body)
                        if message_class is not None:
                            event = message_class.from_bytes(message.body)
                        else:
                            event = message.body
                        await on_message(event)
                    except Exception as exc:
                        logger.exception("Error processing message: %s", exc)

    @property
    def exchange_name(self) -> str:
        """Return the exchange name."""
        return self._exchange_name

    @property
    def is_connected(self) -> bool:
        """Return True if connected to the broker."""
        return (
            self._connection is not None
            and not self._connection.is_closed
            and self._channel is not None
            and not self._channel.is_closed
            and self._exchange is not None
        )
