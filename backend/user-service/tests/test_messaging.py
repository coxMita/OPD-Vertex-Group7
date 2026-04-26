"""Tests for messaging facades, manager, and message helpers."""

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.messaging.direct_message_facade import DirectMessageFacade
from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_exchanges import USER_CREATED
from src.messaging.pubsub_facade import PubSubFacade
from src.models.msg.abstract_message import AbstractMessage


class SampleMessage(AbstractMessage):
    """Concrete message used to test serialization and messaging flow."""

    value: str


class AsyncContextManager:
    """Tiny async context manager helper for mocked queue/message contexts."""

    def __init__(self, value: object) -> None:
        """Store the value returned by the async context manager."""
        self._value = value

    async def __aenter__(self) -> object:
        """Return the wrapped context value."""
        return self._value

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        """Exit the async context manager without suppressing exceptions."""
        return False


class OneMessageIterator:
    """Async iterator that yields a single message."""

    def __init__(self, message: object) -> None:
        """Store the single message that will be yielded."""
        self._message = message
        self._done = False

    async def __aenter__(self) -> "OneMessageIterator":
        """Return the iterator when entering the async context."""
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        """Exit the iterator context without suppressing exceptions."""
        return False

    def __aiter__(self) -> "OneMessageIterator":
        """Return the iterator instance."""
        return self

    async def __anext__(self) -> object:
        """Yield the stored message once, then stop iteration."""
        if self._done:
            raise StopAsyncIteration
        self._done = True
        return self._message


def make_processed_message(body: bytes) -> MagicMock:
    """Build a fake aio-pika message with an async process context."""
    message = MagicMock()
    message.body = body
    message.process.return_value = AsyncContextManager(message)
    return message


class FakeTask:
    """Simple awaitable task double used for cancellation tests."""

    def __init__(self, done: bool = False) -> None:
        """Initialize the task with a done-state flag."""
        self._done = done
        self.cancelled = False

    def cancel(self) -> None:
        """Mark the task as cancelled."""
        self.cancelled = True

    def done(self) -> bool:
        """Return whether the task is already complete."""
        return self._done

    def __await__(self) -> Generator[None, None, None]:
        """Provide awaitable behavior for the fake task."""

        async def _awaitable() -> None:
            return None

        return _awaitable().__await__()


@pytest.mark.asyncio
async def test_abstract_message_roundtrip_and_string_representation() -> None:
    """AbstractMessage helpers should serialize and deserialize cleanly."""
    message = SampleMessage(value="hello")
    payload = message.to_bytes()

    restored = SampleMessage.from_bytes(payload)

    assert restored == message
    assert "SampleMessage" in str(message)
    assert USER_CREATED == "user.created"


@pytest.mark.asyncio
async def test_messaging_manager_start_stop_and_lookup() -> None:
    """MessagingManager should start, stop, and retrieve registered facades."""
    manager = MessagingManager()
    pubsub = MagicMock()
    pubsub.exchange_name = "users"
    pubsub.connect = AsyncMock()
    pubsub.close = AsyncMock()
    direct = MagicMock()
    direct.exchange_name = "emails"
    direct.connect = AsyncMock()
    direct.close = AsyncMock()

    manager.add_pubsub(pubsub)
    manager.add_direct(direct)
    await manager.start_all()
    await manager.stop_all()

    assert manager.get_pubsub("users") is pubsub
    assert manager.get_direct("emails") is direct
    pubsub.connect.assert_awaited_once()
    pubsub.close.assert_awaited_once()
    direct.connect.assert_awaited_once()
    direct.close.assert_awaited_once()


def test_messaging_manager_rejects_duplicates_and_missing_entries() -> None:
    """MessagingManager should enforce unique exchanges and fail on misses."""
    manager = MessagingManager()
    pubsub = MagicMock(exchange_name="users")
    direct = MagicMock(exchange_name="emails")

    manager.add_pubsubs([pubsub])
    manager.add_directs([direct])

    with pytest.raises(ValueError):
        manager.add_pubsub(pubsub)
    with pytest.raises(ValueError):
        manager.add_direct(direct)
    with pytest.raises(ValueError):
        manager.get_pubsub("missing")
    with pytest.raises(ValueError):
        manager.get_direct("missing")


def test_facades_fall_back_to_new_event_loop_when_no_running_loop() -> None:
    """Both facade types should create a loop if none is currently running."""
    fallback_loop = MagicMock()

    with (
        patch(
            "src.messaging.pubsub_facade.asyncio.get_running_loop",
            side_effect=RuntimeError,
        ),
        patch(
            "src.messaging.pubsub_facade.asyncio.new_event_loop",
            return_value=fallback_loop,
        ),
    ):
        pubsub = PubSubFacade("amqp://guest:guest@broker/", "users")

    with (
        patch(
            "src.messaging.direct_message_facade.asyncio.get_running_loop",
            side_effect=RuntimeError,
        ),
        patch(
            "src.messaging.direct_message_facade.asyncio.new_event_loop",
            return_value=fallback_loop,
        ),
    ):
        direct = DirectMessageFacade("amqp://guest:guest@broker/", "notifications")

    assert pubsub._loop is fallback_loop
    assert direct._loop is fallback_loop


@pytest.mark.asyncio
async def test_pubsub_facade_connect_publish_subscribe_close_and_status() -> None:
    """PubSubFacade should manage connect, publish, subscribe, and cleanup."""
    connection = AsyncMock()
    connection.is_closed = False
    channel = AsyncMock()
    channel.is_closed = False
    exchange = AsyncMock()
    declared_queue = AsyncMock()
    declared_queue.bind = AsyncMock()
    channel.declare_exchange.return_value = exchange
    channel.declare_queue.return_value = declared_queue
    connection.channel.return_value = channel

    with (
        patch(
            "src.messaging.pubsub_facade.aio_pika.connect_robust",
            new=AsyncMock(return_value=connection),
        ),
        patch("src.messaging.pubsub_facade.aio_pika.Message") as message_cls,
    ):
        facade = PubSubFacade("amqp://guest:guest@broker/", "users")
        await facade.connect()

        sample = SampleMessage(value="created")
        await facade.publish(sample)

        assert facade.is_connected is True
        message_cls.assert_called_once_with(
            body=sample.to_bytes(),
            content_type="application/json",
        )
        exchange.publish.assert_awaited_once()

        callback = AsyncMock()
        with patch.object(facade, "_consume", new=AsyncMock()) as consume_mock:
            facade.subscribe("queue.users", callback, SampleMessage)
            await asyncio.sleep(0)
            consume_mock.assert_awaited_once_with(
                "queue.users", callback, SampleMessage
            )

        facade._consumer_task = FakeTask(done=False)
        facade.subscribe("queue.users", callback, SampleMessage)

        facade._consumer_task = FakeTask()
        await facade.close()

        channel.close.assert_awaited()
        connection.close.assert_awaited()


@pytest.mark.asyncio
async def test_pubsub_facade_guards_when_not_connected() -> None:
    """PubSubFacade should fail fast before connect and expose disconnected state."""
    facade = PubSubFacade("amqp://guest:guest@broker/", "users")

    with pytest.raises(RuntimeError):
        await facade.publish(SampleMessage(value="hello"))
    with pytest.raises(RuntimeError):
        facade.subscribe("queue.users", AsyncMock(), SampleMessage)

    assert facade.exchange_name == "users"
    assert facade.is_connected is False


@pytest.mark.asyncio
async def test_pubsub_consume_messages_processes_and_swallows_handler_errors() -> None:
    """PubSub consumption should decode messages and isolate handler failures."""
    message = make_processed_message(SampleMessage(value="hello").to_bytes())
    queue = MagicMock()
    queue.iterator.return_value = OneMessageIterator(message)
    callback = AsyncMock(side_effect=RuntimeError("boom"))

    await PubSubFacade._consume_messages(SampleMessage, callback, queue)

    callback.assert_awaited_once()


@pytest.mark.asyncio
async def test_pubsub_consume_binds_queue_and_delegates_to_message_loop() -> None:
    """PubSub _consume should declare/bind the queue before consuming."""
    facade = PubSubFacade("amqp://guest:guest@broker/", "users")
    facade._channel = AsyncMock()
    facade._exchange = AsyncMock()
    queue = AsyncMock()
    facade._channel.declare_queue.return_value = queue
    callback = AsyncMock()

    with patch.object(
        PubSubFacade, "_consume_messages", new=AsyncMock()
    ) as consume_messages:
        await facade._consume("queue.users", callback, SampleMessage)

    facade._channel.declare_queue.assert_awaited_once_with("queue.users", durable=True)
    queue.bind.assert_awaited_once_with(facade._exchange)
    consume_messages.assert_awaited_once_with(SampleMessage, callback, queue)


@pytest.mark.asyncio
async def test_direct_message_facade_connect_send_receive_close_and_status() -> None:
    """DirectMessageFacade should manage direct exchange operations."""
    connection = AsyncMock()
    connection.is_closed = False
    channel = AsyncMock()
    channel.is_closed = False
    exchange = AsyncMock()
    channel.declare_exchange.return_value = exchange
    connection.channel.return_value = channel

    with (
        patch(
            "src.messaging.direct_message_facade.aio_pika.connect_robust",
            new=AsyncMock(return_value=connection),
        ),
        patch("src.messaging.direct_message_facade.aio_pika.Message") as message_cls,
    ):
        facade = DirectMessageFacade("amqp://guest:guest@broker/", "notifications")
        await facade.connect()

        sample = SampleMessage(value="ready")
        await facade.send_message(sample, routing_key="doctor.created")

        assert facade.is_connected is True
        message_cls.assert_called_once()
        exchange.publish.assert_awaited_once()

        callback = AsyncMock()
        with patch.object(facade, "_consume", new=AsyncMock()) as consume_mock:
            facade.receive_messages(
                "doctor.created", "queue.notifications", callback, SampleMessage
            )
            await asyncio.sleep(0)
            consume_mock.assert_awaited_once_with(
                "doctor.created", "queue.notifications", callback, SampleMessage
            )

        facade._consumer_task = FakeTask(done=False)
        facade.receive_messages(
            "doctor.created", "queue.notifications", callback, SampleMessage
        )

        facade._consumer_task = FakeTask()
        await facade.close()

        channel.close.assert_awaited()
        connection.close.assert_awaited()


@pytest.mark.asyncio
async def test_direct_message_facade_guards_when_not_connected() -> None:
    """DirectMessageFacade should fail fast and expose disconnected state."""
    facade = DirectMessageFacade("amqp://guest:guest@broker/", "notifications")

    with pytest.raises(RuntimeError):
        await facade.send_message(SampleMessage(value="hello"), "rk")
    with pytest.raises(RuntimeError):
        facade.receive_messages("rk", "queue", AsyncMock(), SampleMessage)

    assert facade.exchange_name == "notifications"
    assert facade.is_connected is False


@pytest.mark.asyncio
async def test_direct_mesg_consume_msg_processes_and_swallows_handler_errors() -> None:
    """Direct consumer should decode and handle message processing errors."""
    message = make_processed_message(SampleMessage(value="hello").to_bytes())
    queue = MagicMock()
    queue.iterator.return_value = OneMessageIterator(message)
    callback = AsyncMock(side_effect=RuntimeError("boom"))

    await DirectMessageFacade._consume_messages(SampleMessage, callback, queue)

    callback.assert_awaited_once()


@pytest.mark.asyncio
async def test_direct_message_consume_binds_queue_and_delegates_to_message_loop() -> (
    None
):
    """Direct _consume should declare/bind the queue before consuming."""
    facade = DirectMessageFacade("amqp://guest:guest@broker/", "notifications")
    facade._channel = AsyncMock()
    facade._exchange = AsyncMock()
    queue = AsyncMock()
    facade._channel.declare_queue.return_value = queue
    callback = AsyncMock()

    with patch.object(
        DirectMessageFacade, "_consume_messages", new=AsyncMock()
    ) as consume_messages:
        await facade._consume(
            "doctor.created", "queue.notifications", callback, SampleMessage
        )

    facade._channel.declare_queue.assert_awaited_once_with(
        "queue.notifications", durable=True
    )
    queue.bind.assert_awaited_once_with(facade._exchange, routing_key="doctor.created")
    consume_messages.assert_awaited_once_with(SampleMessage, callback, queue)
