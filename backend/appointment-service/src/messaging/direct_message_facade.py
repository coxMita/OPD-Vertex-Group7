import asyncio
import logging
from asyncio import AbstractEventLoop
from contextlib import suppress
from typing import Awaitable, Callable, TypeVar

import aio_pika
from aio_pika.abc import AbstractRobustQueue

from src.models.msg.abstract_message import AbstractMessage

MessageType = TypeVar("MessageType", bound=AbstractMessage)

logger = logging.getLogger(__name__)


class DirectMessageFacade:
    """Facade for sending and receiving messages via a direct exchange."""

    def __init__(self, amqp_url: str, exchange_name: str) -> None:
        """Initialize the DirectMessageFacade with connection parameters.

        Args:
            amqp_url (str): The AMQP broker URL.
            exchange_name (str): The name of the direct exchange.

        """
        self._amqp_url = amqp_url
        self._exchange_name = exchange_name
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None
        self._exchange: aio_pika.Exchange | None = None
        try:
            self._loop: AbstractEventLoop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop: AbstractEventLoop = asyncio.new_event_loop()
        self._consumer_task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Establish connection to the AMQP broker and declare a direct exchange.

        Raises:
            aio_pika.exceptions.AMQPConnectionError: Connection to the broker failed.

        """
        self._connection = await aio_pika.connect_robust(
            self._amqp_url, loop=self._loop
        )
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.DIRECT, durable=True
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
        """Send a message to the direct exchange with the specified routing key.

        Args:
            message (AbstractMessage): The message to send.
            routing_key (str): The routing key to use for the message.

        Raises:
            RuntimeError: If the messaging infrastructure is not properly initialized.

        """
        if not self._exchange:
            raise RuntimeError("Exchange is not initialized. Call connect() first.")
        msg = aio_pika.Message(
            body=message.to_bytes(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self._exchange.publish(msg, routing_key=routing_key)

    def receive_messages(
        self,
        routing_key: str,
        queue_name: str,
        on_message: Callable[[MessageType], Awaitable],
        message_type: type[MessageType],
    ) -> None:
        """Subscribe to messages from the direct exchange with a specific routing key.

        Args:
            routing_key (str): The routing key to bind the queue to.
            queue_name (str): The name of the queue to bind to the exchange.
            on_message (Callable[[MessageType], Awaitable]): Async callback to process received messages.
            message_type (Type[MessageType]): The class type of the message for deserialization.

        Raises:
            RuntimeError: If the messaging infrastructure is not properly initialized.

        """  # noqa: E501
        if not self._channel or not self._exchange:
            raise RuntimeError(
                "Channel or exchange is not initialized. Call connect() first."
            )
        if self._consumer_task is not None and not self._consumer_task.done():
            return  # Already consuming

        self._consumer_task = self._loop.create_task(
            self._consume(routing_key, queue_name, on_message, message_type)
        )

    async def _consume(
        self,
        routing_key: str,
        queue_name: str,
        on_message: Callable[[MessageType], Awaitable],
        message_class: type[AbstractMessage],
    ) -> None:
        """Consume messages from the specified queue and process them.

        Args:
            routing_key (str): The routing key to bind the queue to.
            queue_name (str): The name of the queue to bind to the exchange.
            on_message (Callable[[MessageType], Awaitable]): Async callback to process received messages.
            message_class (Type[AbstractMessage]): The class type of the message for deserialization.

        """  # noqa: E501
        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(self._exchange, routing_key=routing_key)

        await self._consume_messages(message_class, on_message, queue)

    @staticmethod
    async def _consume_messages(
        message_class: type[AbstractMessage],
        on_message: Callable[[MessageType], Awaitable],
        queue: AbstractRobustQueue,
    ) -> None:
        """Process messages from the queue using the provided callback.

        Args:
            message_class (Type[AbstractMessage]): The class type of the message for deserialization.
            on_message (Callable[[MessageType], Awaitable]): Async callback to process received messages.
            queue (AbstractRobustQueue): The queue to consume messages from.

        """  # noqa: E501
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        logger.info("Received message: %s", message.body)
                        event = message_class.from_bytes(message.body)
                        await on_message(event)
                    except Exception as e:
                        logger.exception("Error processing message: %s", e)

    @property
    def exchange_name(self) -> str:
        """Get the name of the exchange used by this facade."""
        return self._exchange_name

    @property
    def is_connected(self) -> bool:
        """Check if the facade is connected to the AMQP broker.

        Returns:
            bool: True if connected, False otherwise.

        """
        return (
            self._connection is not None
            and not self._connection.is_closed
            and self._channel is not None
            and not self._channel.is_closed
            and self._exchange is not None
        )
