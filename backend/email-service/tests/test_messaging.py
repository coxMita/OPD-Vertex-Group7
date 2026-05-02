"""Tests for messaging facades and the messaging manager."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.messaging.appointment_subscriber_facade import AppointmentSubscriberFacade
from src.messaging.email_queue_facade import EmailQueueFacade
from src.messaging.messaging_manager import MessagingManager

_AMQP_URL = "amqp://guest:guest@localhost/"
_QUEUE_NAME = "test_queue"


# ── EmailQueueFacade ──────────────────────────────────────────────────────────


def test_email_queue_facade_queue_name() -> None:
    """queue_name property returns the name supplied at construction."""
    facade = EmailQueueFacade(_AMQP_URL, _QUEUE_NAME)
    assert facade.queue_name == _QUEUE_NAME


@pytest.mark.asyncio
async def test_email_queue_facade_connect_and_consume() -> None:
    """connect_and_consume declares the queue, attaches a consumer, returns conn."""
    mock_conn = MagicMock()
    mock_conn.is_closed = False
    mock_channel = AsyncMock()
    mock_conn.channel = AsyncMock(return_value=mock_channel)
    mock_queue = AsyncMock()
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)

    with patch(
        "src.messaging.email_queue_facade.aio_pika.connect_robust",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ):
        facade = EmailQueueFacade(_AMQP_URL, _QUEUE_NAME)
        conn = await facade.connect_and_consume()

    assert conn is mock_conn
    mock_channel.set_qos.assert_called_once_with(prefetch_count=10)
    mock_channel.declare_queue.assert_called_once_with(_QUEUE_NAME, durable=True)
    mock_queue.consume.assert_called_once()


@pytest.mark.asyncio
async def test_email_queue_facade_close_open_connection() -> None:
    """close() closes an active connection."""
    mock_conn = MagicMock()
    mock_conn.is_closed = False
    mock_conn.close = AsyncMock()
    mock_channel = AsyncMock()
    mock_conn.channel = AsyncMock(return_value=mock_channel)
    mock_queue = AsyncMock()
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)

    with patch(
        "src.messaging.email_queue_facade.aio_pika.connect_robust",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ):
        facade = EmailQueueFacade(_AMQP_URL, _QUEUE_NAME)
        await facade.connect_and_consume()
        await facade.close()

    mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_email_queue_facade_close_without_connect() -> None:
    """close() on an unconnected facade completes without error."""
    facade = EmailQueueFacade(_AMQP_URL, _QUEUE_NAME)
    await facade.close()  # must not raise


@pytest.mark.asyncio
async def test_email_queue_facade_close_already_closed_skips() -> None:
    """close() skips calling close() when the connection reports is_closed=True."""
    mock_conn = MagicMock()
    mock_conn.is_closed = True
    mock_conn.close = AsyncMock()
    mock_channel = AsyncMock()
    mock_conn.channel = AsyncMock(return_value=mock_channel)
    mock_queue = AsyncMock()
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)

    with patch(
        "src.messaging.email_queue_facade.aio_pika.connect_robust",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ):
        facade = EmailQueueFacade(_AMQP_URL, _QUEUE_NAME)
        await facade.connect_and_consume()
        await facade.close()

    mock_conn.close.assert_not_called()


# ── AppointmentSubscriberFacade ───────────────────────────────────────────────


def test_appointment_subscriber_queue_name() -> None:
    """queue_name returns the hard-coded appointment status queue name."""
    facade = AppointmentSubscriberFacade(_AMQP_URL)
    assert facade.queue_name == "email_service_appointment_status"


@pytest.mark.asyncio
async def test_appointment_subscriber_connect_and_consume() -> None:
    """connect_and_consume binds the queue to both fanout exchanges."""
    mock_conn = MagicMock()
    mock_conn.is_closed = False
    mock_channel = AsyncMock()
    mock_conn.channel = AsyncMock(return_value=mock_channel)
    mock_exchange = AsyncMock()
    mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
    mock_queue = AsyncMock()
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)

    with patch(
        "src.messaging.appointment_subscriber_facade.aio_pika.connect_robust",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ):
        facade = AppointmentSubscriberFacade(_AMQP_URL)
        conn = await facade.connect_and_consume()

    assert conn is mock_conn
    assert mock_channel.declare_exchange.call_count == 2  # noqa: PLR2004
    assert mock_queue.bind.call_count == 2  # noqa: PLR2004
    mock_queue.consume.assert_called_once()


@pytest.mark.asyncio
async def test_appointment_subscriber_close_open_connection() -> None:
    """close() closes an active connection."""
    mock_conn = MagicMock()
    mock_conn.is_closed = False
    mock_conn.close = AsyncMock()
    mock_channel = AsyncMock()
    mock_conn.channel = AsyncMock(return_value=mock_channel)
    mock_exchange = AsyncMock()
    mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
    mock_queue = AsyncMock()
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)

    with patch(
        "src.messaging.appointment_subscriber_facade.aio_pika.connect_robust",
        new_callable=AsyncMock,
        return_value=mock_conn,
    ):
        facade = AppointmentSubscriberFacade(_AMQP_URL)
        await facade.connect_and_consume()
        await facade.close()

    mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_appointment_subscriber_close_without_connect() -> None:
    """close() on an unconnected facade completes without error."""
    facade = AppointmentSubscriberFacade(_AMQP_URL)
    await facade.close()  # must not raise


# ── MessagingManager ──────────────────────────────────────────────────────────


def test_messaging_manager_add_and_get_queue() -> None:
    """add_email_queue registers a facade retrievable by queue name."""
    manager = MessagingManager()
    facade = MagicMock(spec=EmailQueueFacade)
    facade.queue_name = _QUEUE_NAME
    manager.add_email_queue(facade)
    assert manager.get_email_queue(_QUEUE_NAME) is facade


def test_messaging_manager_add_duplicate_raises() -> None:
    """Registering two facades with the same queue name raises ValueError."""
    manager = MessagingManager()
    facade_a = MagicMock(spec=EmailQueueFacade)
    facade_a.queue_name = _QUEUE_NAME
    facade_b = MagicMock(spec=EmailQueueFacade)
    facade_b.queue_name = _QUEUE_NAME
    manager.add_email_queue(facade_a)
    with pytest.raises(ValueError, match=_QUEUE_NAME):
        manager.add_email_queue(facade_b)


def test_messaging_manager_add_email_queues_bulk() -> None:
    """add_email_queues registers all supplied facades in one call."""
    manager = MessagingManager()
    facade_a = MagicMock(spec=EmailQueueFacade)
    facade_a.queue_name = "q1"
    facade_b = MagicMock(spec=EmailQueueFacade)
    facade_b.queue_name = "q2"
    manager.add_email_queues([facade_a, facade_b])
    assert manager.get_email_queue("q1") is facade_a
    assert manager.get_email_queue("q2") is facade_b


def test_messaging_manager_get_queue_not_found_raises() -> None:
    """get_email_queue raises ValueError for an unregistered queue name."""
    manager = MessagingManager()
    with pytest.raises(ValueError, match="missing"):
        manager.get_email_queue("missing")


def test_messaging_manager_connection_before_start_raises() -> None:
    """rabbitmq_connection raises RuntimeError before start_all is called."""
    manager = MessagingManager()
    with pytest.raises(RuntimeError):
        _ = manager.rabbitmq_connection


def test_messaging_manager_connection_when_closed_raises() -> None:
    """rabbitmq_connection raises RuntimeError when the stored connection is closed."""
    manager = MessagingManager()
    mock_conn = MagicMock()
    mock_conn.is_closed = True
    manager._connection = mock_conn  # noqa: SLF001
    with pytest.raises(RuntimeError):
        _ = manager.rabbitmq_connection


@pytest.mark.asyncio
async def test_messaging_manager_start_and_stop_all() -> None:
    """start_all connects facades; stop_all closes them and clears all state."""
    manager = MessagingManager()
    mock_conn = MagicMock()
    mock_conn.is_closed = False

    facade = MagicMock(spec=EmailQueueFacade)
    facade.queue_name = _QUEUE_NAME
    facade.connect_and_consume = AsyncMock(return_value=mock_conn)
    facade.close = AsyncMock()

    manager.add_email_queue(facade)
    await manager.start_all()

    facade.connect_and_consume.assert_called_once()
    assert manager.rabbitmq_connection is mock_conn

    await manager.stop_all()

    facade.close.assert_called_once()
    with pytest.raises(RuntimeError):
        _ = manager.rabbitmq_connection


@pytest.mark.asyncio
async def test_messaging_manager_start_all_empty() -> None:
    """start_all with no registered facades completes without error."""
    manager = MessagingManager()
    await manager.start_all()  # must not raise
