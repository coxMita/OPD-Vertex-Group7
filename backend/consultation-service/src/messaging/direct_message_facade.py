"""Facade for direct RabbitMQ message exchange communication."""

import asyncio
from asyncio import AbstractEventLoop
from contextlib import suppress
from typing import Awaitable, Callable, TypeVar, cast

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractExchange

from src.models.msg.abstract_message import AbstractMessage

MessageType = TypeVar("MessageType", bound=AbstractMessage)


class DirectMessageFacade:
    """Facade for sending and receiving messages via a direct exchange."""

    def __init__(self, amqp_url: str, exchange_name: str) -> None:
        """Initialize the DirectMessageFacade with connection parameters."""
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
        """Establish connection to the AMQP broker and declare a direct exchange."""
        self._connection = await aio_pika.connect_robust(
            self._amqp_url,
            loop=self._loop,
        )
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name,
            aio_pika.ExchangeType.DIRECT,
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

    async def send_message(self, message: AbstractMessage, routing_key: str) -> None:
        """Send a message to the direct exchange with the provided routing key."""
        if not self._exchange:
            raise RuntimeError("Exchange is not initialized. Call connect() first.")

        outgoing = aio_pika.Message(
            body=message.to_bytes(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self._exchange.publish(outgoing, routing_key=routing_key)

    def receive_messages(
        self,
        routing_key: str,
        queue_name: str,
        on_message: Callable[[MessageType], Awaitable],
        message_type: type[MessageType],
    ) -> None:
        """Subscribe to messages from the direct exchange."""
        if not self._channel or not self._exchange:
            raise RuntimeError(
                "Channel or exchange is not initialized. Call connect() first."
            )
        if self._consumer_task is not None and not self._consumer_task.done():
            return

        self._consumer_task = self._loop.create_task(
            self._consume(routing_key, queue_name, on_message, message_type)
        )

    async def _consume(
        self,
        routing_key: str,
        queue_name: str,
        on_message: Callable[[MessageType], Awaitable],
        message_class: type[MessageType],
    ) -> None:
        """Consume messages from the specified routing key and queue."""
        if not self._channel or not self._exchange:
            raise RuntimeError(
                "Channel or exchange is not initialized. Call connect() first."
            )

        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(self._exchange, routing_key=routing_key)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    event = cast(MessageType, message_class.from_bytes(message.body))
                    await on_message(event)

    @property
    def exchange_name(self) -> str:
        """Get the name of the exchange used by this facade."""
        return self._exchange_name
