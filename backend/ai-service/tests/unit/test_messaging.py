"""Unit tests for messaging_manager, pubsub_facade, and abstract_message."""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.rag.vector_store as vs
from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_facade import PubSubFacade
from src.models.msg.ai_completed_message import AICompletedMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_facade(exchange: str = "test.exchange") -> MagicMock:
    """Return a mock PubSubFacade with the given exchange_name."""
    facade = MagicMock(spec=PubSubFacade)
    facade.exchange_name = exchange
    facade.connect = AsyncMock()
    facade.close = AsyncMock()
    return facade


# ---------------------------------------------------------------------------
# AbstractMessage
# ---------------------------------------------------------------------------


class TestAbstractMessage:
    """Unit tests for AbstractMessage serialisation helpers."""

    def _make_message(self) -> AICompletedMessage:
        return AICompletedMessage(
            filename="test.mp3",
            summary="Patient has fever.",
            prescription={"medication_name": "Amoxicillin"},
            consultation_id=uuid.uuid4(),
        )

    def test_to_bytes_returns_json_encoded_bytes(self) -> None:
        """to_bytes() should return a valid JSON-encoded byte string."""
        msg = self._make_message()
        raw = msg.to_bytes()
        assert isinstance(raw, bytes)
        parsed = json.loads(raw)
        assert parsed["filename"] == "test.mp3"
        assert parsed["summary"] == "Patient has fever."

    def test_from_bytes_round_trips_correctly(self) -> None:
        """from_bytes(to_bytes()) should return an equivalent message."""
        msg = self._make_message()
        restored = AICompletedMessage.from_bytes(msg.to_bytes())
        assert restored.filename == msg.filename
        assert restored.summary == msg.summary
        assert restored.prescription == msg.prescription
        assert restored.consultation_id == msg.consultation_id

    def test_str_includes_class_name(self) -> None:
        """__str__() should include the class name in the output."""
        msg = self._make_message()
        result = str(msg)
        assert "AICompletedMessage" in result


# ---------------------------------------------------------------------------
# MessagingManager
# ---------------------------------------------------------------------------


class TestMessagingManager:
    """Unit tests for MessagingManager."""

    def test_add_pubsub_stores_facade(self) -> None:
        """add_pubsub should store the facade and allow get_pubsub to retrieve it."""
        mgr = MessagingManager()
        facade = _make_facade("exchange.a")
        mgr.add_pubsub(facade)
        assert mgr.get_pubsub("exchange.a") is facade

    def test_add_pubsub_raises_on_duplicate_exchange(self) -> None:
        """add_pubsub should raise ValueError when the same exchange is added twice."""
        mgr = MessagingManager()
        facade = _make_facade("exchange.a")
        mgr.add_pubsub(facade)
        with pytest.raises(ValueError, match="already exists"):
            mgr.add_pubsub(_make_facade("exchange.a"))

    def test_get_pubsub_raises_when_exchange_not_found(self) -> None:
        """get_pubsub should raise ValueError for an unknown exchange name."""
        mgr = MessagingManager()
        with pytest.raises(ValueError, match="No PubSubFacade found"):
            mgr.get_pubsub("nonexistent.exchange")

    @pytest.mark.asyncio
    async def test_start_all_calls_connect_on_each_facade(self) -> None:
        """start_all() should call connect() on every registered facade."""
        mgr = MessagingManager()
        fa = _make_facade("exchange.a")
        fb = _make_facade("exchange.b")
        mgr.add_pubsub(fa)
        mgr.add_pubsub(fb)
        await mgr.start_all()
        fa.connect.assert_awaited_once()
        fb.connect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_all_calls_close_on_each_facade(self) -> None:
        """stop_all() should call close() on every registered facade."""
        mgr = MessagingManager()
        fa = _make_facade("exchange.a")
        fb = _make_facade("exchange.b")
        mgr.add_pubsub(fa)
        mgr.add_pubsub(fb)
        await mgr.stop_all()
        fa.close.assert_awaited_once()
        fb.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_all_with_no_facades_does_not_raise(self) -> None:
        """start_all() on an empty manager should complete without error."""
        mgr = MessagingManager()
        await mgr.start_all()  # should not raise

    @pytest.mark.asyncio
    async def test_stop_all_with_no_facades_does_not_raise(self) -> None:
        """stop_all() on an empty manager should complete without error."""
        mgr = MessagingManager()
        await mgr.stop_all()  # should not raise


# ---------------------------------------------------------------------------
# PubSubFacade
# ---------------------------------------------------------------------------


class TestPubSubFacadeInit:
    """Tests for PubSubFacade.__init__ loop-detection branches."""

    def test_exchange_name_property(self) -> None:
        """exchange_name property should return the value passed to __init__."""
        facade = PubSubFacade("amqp://localhost", "my.exchange")
        assert facade.exchange_name == "my.exchange"

    def test_init_uses_running_loop_when_available(self) -> None:
        """When a running loop exists, __init__ should capture it."""

        async def _inner() -> None:
            loop = asyncio.get_running_loop()
            facade = PubSubFacade("amqp://localhost", "test.exchange")
            assert facade._loop is loop  # noqa: SLF001

        asyncio.run(_inner())

    def test_init_creates_new_loop_when_none_running(self) -> None:
        """When no loop is running, __init__ should create a new event loop."""
        facade = PubSubFacade("amqp://localhost", "test.exchange")
        assert facade._loop is not None  # noqa: SLF001


class TestPubSubFacadeIsConnected:
    """Tests for the is_connected property."""

    def test_is_connected_false_when_not_connected(self) -> None:
        """Should return False before connect() is called."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        assert facade.is_connected is False

    def test_is_connected_true_when_all_components_set(self) -> None:
        """Should return True when connection, channel, and exchange are set."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        mock_conn = MagicMock()
        mock_conn.is_closed = False
        mock_channel = MagicMock()
        mock_channel.is_closed = False
        mock_exchange = MagicMock()
        facade._connection = mock_conn  # noqa: SLF001
        facade._channel = mock_channel  # noqa: SLF001
        facade._exchange = mock_exchange  # noqa: SLF001
        assert facade.is_connected is True

    def test_is_connected_false_when_connection_closed(self) -> None:
        """Should return False when connection reports is_closed=True."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        mock_conn = MagicMock()
        mock_conn.is_closed = True
        facade._connection = mock_conn  # noqa: SLF001
        facade._channel = MagicMock()
        facade._exchange = MagicMock()
        assert facade.is_connected is False


class TestPubSubFacadePublish:
    """Tests for PubSubFacade.publish()."""

    @pytest.mark.asyncio
    async def test_publish_raises_when_exchange_not_set(self) -> None:
        """Should raise RuntimeError when exchange has not been declared."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        msg = AICompletedMessage(
            filename="f.mp3",
            summary="s",
            prescription={},
            consultation_id=uuid.uuid4(),
        )
        with pytest.raises(RuntimeError, match="call 'connect' first"):
            await facade.publish(msg)

    @pytest.mark.asyncio
    async def test_publish_calls_exchange_publish(self) -> None:
        """Should call exchange.publish() with an aio_pika.Message."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        mock_exchange = AsyncMock()
        facade._exchange = mock_exchange  # noqa: SLF001

        msg = AICompletedMessage(
            filename="f.mp3",
            summary="s",
            prescription={},
            consultation_id=uuid.uuid4(),
        )
        with patch("src.messaging.pubsub_facade.aio_pika.Message") as mock_msg_cls:
            mock_msg_cls.return_value = MagicMock()
            await facade.publish(msg)

        mock_exchange.publish.assert_awaited_once()


class TestPubSubFacadeCancelConsumerTask:
    """Tests for _cancel_consumer_task."""

    @pytest.mark.asyncio
    async def test_cancel_consumer_task_when_none(self) -> None:
        """Should do nothing when no consumer task exists."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        await facade._cancel_consumer_task()  # noqa: SLF001  — should not raise

    @pytest.mark.asyncio
    async def test_cancel_consumer_task_cancels_running_task(self) -> None:
        """Should cancel and await a running consumer task."""
        facade = PubSubFacade("amqp://localhost", "exchange")

        async def _long_running() -> None:
            await asyncio.sleep(999)

        task = asyncio.ensure_future(_long_running())
        facade._consumer_task = task  # noqa: SLF001
        await facade._cancel_consumer_task()  # noqa: SLF001
        assert task.cancelled()
        assert facade._consumer_task is None  # noqa: SLF001


class TestPubSubFacadeClose:
    """Tests for PubSubFacade.close()."""

    @pytest.mark.asyncio
    async def test_close_skips_already_closed_channel(self) -> None:
        """Should not call close() on a channel that is already closed."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        mock_channel = AsyncMock()
        mock_channel.is_closed = True
        mock_conn = AsyncMock()
        mock_conn.is_closed = True
        facade._channel = mock_channel  # noqa: SLF001
        facade._connection = mock_conn  # noqa: SLF001
        await facade.close()
        mock_channel.close.assert_not_awaited()
        mock_conn.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_calls_close_on_open_channel_and_connection(self) -> None:
        """Should close both channel and connection when they are open."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        mock_channel = AsyncMock()
        mock_channel.is_closed = False
        mock_conn = AsyncMock()
        mock_conn.is_closed = False
        facade._channel = mock_channel  # noqa: SLF001
        facade._connection = mock_conn  # noqa: SLF001
        await facade.close()
        mock_channel.close.assert_awaited_once()
        mock_conn.close.assert_awaited_once()


class TestPubSubFacadeSubscribe:
    """Tests for PubSubFacade.subscribe()."""

    def test_subscribe_raises_when_not_connected(self) -> None:
        """Should raise RuntimeError when exchange/channel are not set."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        with pytest.raises(RuntimeError, match="call 'connect' first"):
            facade.subscribe("queue", AsyncMock(), None)

    def test_subscribe_does_not_create_second_task_if_running(self) -> None:
        """Should not replace a still-running consumer task."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        facade._exchange = MagicMock()  # noqa: SLF001
        facade._channel = MagicMock()  # noqa: SLF001

        # Simulate an existing running task
        existing_task = MagicMock()
        existing_task.done.return_value = False
        facade._consumer_task = existing_task  # noqa: SLF001

        facade.subscribe("queue", AsyncMock(), None)
        # Task should be unchanged
        assert facade._consumer_task is existing_task  # noqa: SLF001

    def test_subscribe_creates_task_when_no_existing_task(self) -> None:
        """Should create a consumer task when none is running."""
        facade = PubSubFacade("amqp://localhost", "exchange")
        facade._exchange = MagicMock()  # noqa: SLF001

        mock_channel = MagicMock()
        facade._channel = mock_channel  # noqa: SLF001

        mock_loop = MagicMock()
        mock_loop.create_task.return_value = MagicMock()
        facade._loop = mock_loop  # noqa: SLF001

        facade.subscribe("queue", AsyncMock(), None)
        mock_loop.create_task.assert_called_once()


class TestPubSubFacadeConnect:
    """Tests for PubSubFacade.connect()."""

    @pytest.mark.asyncio
    async def test_connect_sets_connection_channel_exchange(self) -> None:
        """After connect(), connection, channel, and exchange should be set."""
        facade = PubSubFacade("amqp://localhost", "test.exchange")

        mock_exchange = AsyncMock()
        mock_channel = AsyncMock()
        mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
        mock_connection = AsyncMock()
        mock_connection.channel = AsyncMock(return_value=mock_channel)

        with patch(
            "src.messaging.pubsub_facade.aio_pika.connect_robust",
            new=AsyncMock(return_value=mock_connection),
        ):
            await facade.connect()

        assert facade._connection is mock_connection  # noqa: SLF001
        assert facade._channel is mock_channel  # noqa: SLF001
        assert facade._exchange is mock_exchange  # noqa: SLF001


class TestPubSubFacadeVectorStore:
    """Tests for get_pool creation path in vector_store."""

    @pytest.mark.asyncio
    async def test_get_pool_creates_pool_on_first_call(self) -> None:
        """get_pool() creates a new pool when none exists."""
        original_pool = vs._pool  # noqa: SLF001
        vs._pool = None  # noqa: SLF001
        mock_pool = MagicMock()

        try:
            with patch(
                "src.rag.vector_store.asyncpg.create_pool",
                new=AsyncMock(return_value=mock_pool),
            ):
                result = await vs.get_pool()
            assert result is mock_pool
        finally:
            vs._pool = original_pool  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_get_pool_returns_existing_pool_on_second_call(self) -> None:
        """get_pool() returns the cached pool without creating a new one."""
        original_pool = vs._pool  # noqa: SLF001
        mock_pool = MagicMock()
        vs._pool = mock_pool  # noqa: SLF001

        try:
            with patch(
                "src.rag.vector_store.asyncpg.create_pool",
                new=AsyncMock(),
            ) as mock_create:
                result = await vs.get_pool()
            mock_create.assert_not_awaited()
            assert result is mock_pool
        finally:
            vs._pool = original_pool  # noqa: SLF001
