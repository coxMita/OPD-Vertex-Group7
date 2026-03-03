"""Unit tests for src/messaging/pubsub_facade.py."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aio_pika
import pytest
from pydantic import Field

from src.messaging.pubsub_facade import PubSubFacade
from src.models.msg.abstract_message import AbstractMessage


class DummyMessage(AbstractMessage):
    """Minimal concrete message for testing."""

    content: str = Field(...)

    def to_bytes(self) -> bytes:
        """Serialize the message to bytes."""
        return self.content.encode()

    @classmethod
    def from_bytes(cls, body: bytes) -> "DummyMessage":
        """Deserialize bytes to an instance of DummyMessage."""
        return cls(content=body.decode())


@pytest.fixture
def facade() -> PubSubFacade:
    """Return a fresh PubSubFacade instance for testing."""
    return PubSubFacade("amqp://guest:guest@localhost/", "test_exchange")


class TestInitialState:
    """Tests for PubSubFacade initial state."""

    def test_is_not_connected_before_connect(self, facade: PubSubFacade) -> None:
        """is_connected is False before connect() is called."""
        assert not facade.is_connected

    def test_exchange_name_property(self, facade: PubSubFacade) -> None:
        """exchange_name returns the value passed to __init__."""
        assert facade.exchange_name == "test_exchange"


class TestConnect:
    """Tests for PubSubFacade.connect()."""

    @pytest.mark.asyncio
    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_connect_declares_fanout_exchange(
        self, mock_connect: AsyncMock, facade: PubSubFacade
    ) -> None:
        """connect() declares a durable FANOUT exchange."""
        mock_conn = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connect.return_value = mock_conn
        mock_conn.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange

        await facade.connect()

        mock_channel.declare_exchange.assert_awaited_once_with(
            "test_exchange", aio_pika.ExchangeType.FANOUT, durable=True
        )

    @pytest.mark.asyncio
    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_is_connected_after_connect(
        self, mock_connect: AsyncMock, facade: PubSubFacade
    ) -> None:
        """is_connected returns True after a successful connect()."""
        mock_conn = MagicMock()
        mock_conn.is_closed = False
        mock_channel = MagicMock()
        mock_channel.is_closed = False
        mock_channel.declare_exchange = AsyncMock(return_value=MagicMock())
        mock_conn.channel = AsyncMock(return_value=mock_channel)
        mock_connect.return_value = mock_conn

        await facade.connect()
        assert facade.is_connected


class TestPublish:
    """Tests for PubSubFacade.publish()."""

    @pytest.mark.asyncio
    async def test_publish_raises_without_connect(self, facade: PubSubFacade) -> None:
        """publish() raises RuntimeError if connect() was never called."""
        with pytest.raises(RuntimeError, match="connect"):
            await facade.publish(DummyMessage(content="hello"))

    @pytest.mark.asyncio
    @patch("aio_pika.Message")
    async def test_publish_sends_to_exchange_with_empty_routing_key(
        self, mock_msg_cls: MagicMock, facade: PubSubFacade
    ) -> None:
        """publish() calls exchange.publish with routing_key=''."""
        mock_exchange = AsyncMock()
        facade._exchange = mock_exchange
        mock_msg_instance = MagicMock()
        mock_msg_cls.return_value = mock_msg_instance

        await facade.publish(DummyMessage(content="hello"))

        mock_exchange.publish.assert_awaited_once_with(
            mock_msg_instance, routing_key=""
        )

    @pytest.mark.asyncio
    @patch("aio_pika.Message")
    async def test_publish_uses_json_content_type(
        self, mock_msg_cls: MagicMock, facade: PubSubFacade
    ) -> None:
        """publish() passes the serialised message bytes to aio_pika.Message."""
        facade._exchange = AsyncMock()
        msg = DummyMessage(content="test")
        await facade.publish(msg)

        mock_msg_cls.assert_called_once_with(
            body=msg.to_bytes(), content_type="application/json"
        )


class TestSubscribe:
    """Tests for PubSubFacade.subscribe()."""

    def test_subscribe_raises_without_connect(self, facade: PubSubFacade) -> None:
        """subscribe() raises RuntimeError if connect() was never called."""
        with pytest.raises(RuntimeError, match="connect"):
            facade.subscribe("queue", AsyncMock(), DummyMessage)

    def test_subscribe_creates_consumer_task(self, facade: PubSubFacade) -> None:
        """subscribe() creates a consumer task when exchange and channel exist."""
        facade._exchange = MagicMock()
        facade._channel = MagicMock()
        mock_loop = MagicMock()
        mock_task = MagicMock()
        mock_loop.create_task.return_value = mock_task
        facade._loop = mock_loop

        facade.subscribe("queue", AsyncMock(), DummyMessage)

        mock_loop.create_task.assert_called_once()
        assert facade._consumer_task is mock_task

    def test_subscribe_no_duplicate_task_when_running(
        self, facade: PubSubFacade
    ) -> None:
        """subscribe() is a no-op if a consumer task is already running."""
        facade._exchange = MagicMock()
        facade._channel = MagicMock()
        mock_loop = MagicMock()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_loop.create_task.return_value = mock_task
        facade._loop = mock_loop

        facade.subscribe("queue", AsyncMock(), DummyMessage)
        facade.subscribe("queue", AsyncMock(), DummyMessage)

        mock_loop.create_task.assert_called_once()


class TestClose:
    """Tests for PubSubFacade.close()."""

    @pytest.mark.asyncio
    async def test_close_closes_channel_and_connection(
        self, facade: PubSubFacade
    ) -> None:
        """close() closes both channel and connection."""
        facade._cancel_consumer_task = AsyncMock()
        facade._channel = AsyncMock()
        facade._channel.is_closed = False
        facade._connection = AsyncMock()
        facade._connection.is_closed = False

        await facade.close()

        facade._channel.close.assert_awaited_once()
        facade._connection.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_skips_already_closed(self, facade: PubSubFacade) -> None:
        """close() does not call close() on already-closed channel/connection."""
        facade._cancel_consumer_task = AsyncMock()
        facade._channel = AsyncMock()
        facade._channel.is_closed = True
        facade._connection = AsyncMock()
        facade._connection.is_closed = True

        await facade.close()

        facade._channel.close.assert_not_awaited()
        facade._connection.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_cancels_consumer_task(self, facade: PubSubFacade) -> None:
        """close() cancels a running consumer task and sets it to None."""
        facade._channel = AsyncMock()
        facade._channel.is_closed = False
        facade._connection = AsyncMock()
        facade._connection.is_closed = False

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        future.cancel()
        facade._consumer_task = future

        await facade.close()

        assert facade._consumer_task is None
