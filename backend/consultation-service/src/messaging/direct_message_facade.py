"""Direct message facade for sending direct messages to RabbitMQ."""

import logging

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractExchange
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DirectMessageFacade:
    """Facade for sending direct messages to a RabbitMQ exchange."""

    def __init__(self, amqp_url: str, exchange_name: str) -> None:
        """Initialize the DirectMessageFacade.

        Args:
            amqp_url (str): The AMQP URL for connecting to RabbitMQ.
            exchange_name (str): The name of the exchange to send to.

        """
        self._amqp_url = amqp_url
        self.exchange_name = exchange_name
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._exchange: AbstractExchange | None = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ and declare the exchange."""
        logger.info("Connecting to RabbitMQ at '%s'", self._amqp_url)
        self._connection = await aio_pika.connect_robust(self._amqp_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self.exchange_name,
            ExchangeType.DIRECT,
            durable=True,
        )
        logger.info("Connected to exchange '%s'", self.exchange_name)

    async def close(self) -> None:
        """Close the connection to RabbitMQ."""
        if self._connection:
            await self._connection.close()
            logger.info("Closed connection to exchange '%s'", self.exchange_name)

    async def send(self, message: BaseModel, routing_key: str) -> None:
        """Send a message to the exchange with a specific routing key.

        Args:
            message (BaseModel): The message to send.
            routing_key (str): The routing key for the message.

        """
        if not self._exchange:
            raise RuntimeError(
                f"Cannot send to exchange '{self.exchange_name}'. "
                "Not connected. Call connect() first."
            )
        message_json = message.model_dump_json()
        await self._exchange.publish(
            aio_pika.Message(
                body=message_json.encode(),
                content_type="application/json",
            ),
            routing_key=routing_key,
        )
        logger.info(
            "Sent message to exchange '%s' with routing key '%s'",
            self.exchange_name,
            routing_key,
        )
