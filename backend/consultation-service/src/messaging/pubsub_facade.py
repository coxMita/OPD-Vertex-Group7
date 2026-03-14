"""PubSub facade for publishing messages to RabbitMQ."""

import logging

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractExchange
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PubSubFacade:
    """Facade for publishing messages to a RabbitMQ exchange."""

    def __init__(self, amqp_url: str, exchange_name: str) -> None:
        """Initialize the PubSubFacade.

        Args:
            amqp_url (str): The AMQP URL for connecting to RabbitMQ.
            exchange_name (str): The name of the exchange to publish to.

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
            ExchangeType.FANOUT,
            durable=True,
        )
        logger.info("Connected to exchange '%s'", self.exchange_name)

    async def close(self) -> None:
        """Close the connection to RabbitMQ."""
        if self._connection:
            await self._connection.close()
            logger.info("Closed connection to exchange '%s'", self.exchange_name)

    async def publish(self, message: BaseModel) -> None:
        """Publish a message to the exchange.

        Args:
            message (BaseModel): The message to publish.

        """
        if not self._exchange:
            raise RuntimeError(
                f"Cannot publish to exchange '{self.exchange_name}'. "
                "Not connected. Call connect() first."
            )
        message_json = message.model_dump_json()
        await self._exchange.publish(
            aio_pika.Message(
                body=message_json.encode(),
                content_type="application/json",
            ),
            routing_key="",
        )
        logger.info("Published message to exchange '%s'", self.exchange_name)
