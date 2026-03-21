"""Facade for publishing and subscribing to fanout RabbitMQ exchanges."""

import asyncio
import logging
from asyncio import AbstractEventLoop
from contextlib import suppress
from typing import Any, Awaitable, Callable, TypeVar, cast

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractExchange,
    AbstractQueue,
)

from src.models.msg.abstract_message import AbstractMessage

MessageType = TypeVar("MessageType", bound=AbstractMessage)

logger = logging.getLogger(__name__)


class PubSubFacade:
    """Facade for publishing and subscribing to messages via a fanout exchange."""

    def __init__(self, amqp_url: str, exchange_name: str) -> None:
        """Initialize the PubSubFacade with connection parameters."""
        self._amqp_url = amqp_url
        self._exchange_name = exchange_name
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._exchange: AbstractExchange | None = None
        try:
            self._loop: AbstractEventLoop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
        self._consumer_task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Establish connection to AMQP broker and declare a fanout exchange."""
        self._connection = await aio_pika.connect_robust(
            self._amqp_url, loop=self._loop
        )
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name,
            aio_pika.ExchangeType.FANOUT,
            durable=True,
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
        """Publish a message to all subscribers (fanout pub-sub)."""
        if not self._exchange:
            raise RuntimeError("Exchange not declared; call 'connect' first.")

        outgoing = aio_pika.Message(
            body=message.to_bytes(),
            content_type="application/json",
        )
        await self._exchange.publish(outgoing, routing_key="")
        logger.info("Published message to '%s'", self._exchange_name)

    def subscribe(
        self,
        queue_name: str,
        on_message: Callable[[MessageType], Awaitable[Any]],
        message_class: type[MessageType],
    ) -> None:
        """Subscribe to messages broadcast on this fanout exchange."""
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
        on_message: Callable[[MessageType], Awaitable[Any]],
        message_class: type[MessageType],
    ) -> None:
        """Consume messages from a queue bound to this fanout exchange."""
        if not self._channel or not self._exchange:
            raise RuntimeError(
                "Exchange or channel not declared; call 'connect' first."
            )

        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(self._exchange)
        await self._consume_messages(message_class, on_message, queue)

    @staticmethod
    async def _consume_messages(
        message_class: type[MessageType],
        on_message: Callable[[MessageType], Awaitable[Any]],
        queue: AbstractQueue,
    ) -> None:
        """Iterate queue messages, deserialize, and pass to callback."""
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        event = cast(
                            MessageType,
                            message_class.from_bytes(message.body),
                        )
                        await on_message(event)
                    except Exception as error:
                        logger.exception("Error processing incoming message: %s", error)

    @property
    def exchange_name(self) -> str:
        """Get the name of the exchange used by this facade."""
        return self._exchange_name
