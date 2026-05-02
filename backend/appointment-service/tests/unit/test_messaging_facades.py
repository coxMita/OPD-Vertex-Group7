"""Unit tests for messaging facade behavior."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.messaging.direct_message_facade import DirectMessageFacade
from src.messaging.pubsub_facade import PubSubFacade
from src.models.msg.appointment_message import AppointmentMessage


def _message() -> MagicMock:
    """Create a mock message with bytes serialization."""
    message = MagicMock(spec=AppointmentMessage)
    message.to_bytes.return_value = b"{}"
    return message


def _open_connection() -> MagicMock:
    """Create a connected aio-pika connection mock."""
    exchange = MagicMock()
    exchange.publish = AsyncMock()
    channel = MagicMock()
    channel.is_closed = False
    channel.close = AsyncMock()
    channel.declare_exchange = AsyncMock(return_value=exchange)
    connection = MagicMock()
    connection.is_closed = False
    connection.channel = AsyncMock(return_value=channel)
    connection.close = AsyncMock()
    return connection


@pytest.mark.asyncio
async def test_pubsub_connect_publish_and_close() -> None:
    """PubSubFacade should connect, publish serialized messages and close."""
    connection = _open_connection()
    with patch(
        "src.messaging.pubsub_facade.aio_pika.connect_robust",
        new=AsyncMock(return_value=connection),
    ):
        facade = PubSubFacade("amqp://example", "exchange")
        await facade.connect()
        await facade.publish(_message())
        await facade.close()

    assert facade.exchange_name == "exchange"
    assert facade.is_connected is True
    connection.channel.assert_awaited_once()
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_pubsub_publish_requires_exchange() -> None:
    """Publishing before connect should raise RuntimeError."""
    facade = PubSubFacade("amqp://example", "exchange")

    with pytest.raises(RuntimeError, match="Exchange not declared"):
        await facade.publish(_message())


def test_pubsub_subscribe_requires_connection() -> None:
    """Subscribing before connect should raise RuntimeError."""
    facade = PubSubFacade("amqp://example", "exchange")

    with pytest.raises(RuntimeError, match="Exchange or channel"):
        facade.subscribe("queue", AsyncMock(), AppointmentMessage)


def test_pubsub_subscribe_starts_consumer_task() -> None:
    """Subscribing after connect should create one consumer task."""
    facade = PubSubFacade("amqp://example", "exchange")
    facade._channel = MagicMock()
    facade._exchange = MagicMock()
    facade._loop = MagicMock()
    task = MagicMock()
    task.done.return_value = False
    facade._loop.create_task.return_value = task
    facade._consume = MagicMock(return_value=object())

    facade.subscribe("queue", AsyncMock(), AppointmentMessage)
    facade.subscribe("queue", AsyncMock(), AppointmentMessage)

    facade._loop.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_pubsub_close_cancels_running_consumer_task() -> None:
    """Closing should cancel a running pubsub consumer task."""
    facade = PubSubFacade("amqp://example", "exchange")
    facade._consumer_task = asyncio.create_task(asyncio.sleep(60))

    await facade.close()

    assert facade._consumer_task is None


@pytest.mark.asyncio
async def test_direct_connect_send_and_close() -> None:
    """DirectMessageFacade should connect, send serialized messages and close."""
    connection = _open_connection()
    with patch(
        "src.messaging.direct_message_facade.aio_pika.connect_robust",
        new=AsyncMock(return_value=connection),
    ):
        facade = DirectMessageFacade("amqp://example", "exchange")
        await facade.connect()
        await facade.send_message(_message(), "key")
        await facade.close()

    assert facade.exchange_name == "exchange"
    assert facade.is_connected is True
    connection.channel.assert_awaited_once()
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_direct_send_requires_exchange() -> None:
    """Sending before connect should raise RuntimeError."""
    facade = DirectMessageFacade("amqp://example", "exchange")

    with pytest.raises(RuntimeError, match="Exchange is not initialized"):
        await facade.send_message(_message(), "key")


def test_direct_receive_requires_connection() -> None:
    """Receiving before connect should raise RuntimeError."""
    facade = DirectMessageFacade("amqp://example", "exchange")

    with pytest.raises(RuntimeError, match="Channel or exchange"):
        facade.receive_messages("key", "queue", AsyncMock(), AppointmentMessage)


def test_direct_receive_starts_consumer_task() -> None:
    """Receiving after connect should create one consumer task."""
    facade = DirectMessageFacade("amqp://example", "exchange")
    facade._channel = MagicMock()
    facade._exchange = MagicMock()
    facade._loop = MagicMock()
    task = MagicMock()
    task.done.return_value = False
    facade._loop.create_task.return_value = task
    facade._consume = MagicMock(return_value=object())

    facade.receive_messages("key", "queue", AsyncMock(), AppointmentMessage)
    facade.receive_messages("key", "queue", AsyncMock(), AppointmentMessage)

    facade._loop.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_direct_close_cancels_running_consumer_task() -> None:
    """Closing should cancel a running direct consumer task."""
    facade = DirectMessageFacade("amqp://example", "exchange")
    facade._consumer_task = asyncio.create_task(asyncio.sleep(60))

    await facade.close()

    assert facade._consumer_task is None
