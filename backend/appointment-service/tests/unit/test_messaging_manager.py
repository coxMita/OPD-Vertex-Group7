"""Unit tests for MessagingManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.messaging.messaging_manager import MessagingManager


def _facade(exchange_name: str) -> MagicMock:
    """Create a mocked messaging facade."""
    facade = MagicMock()
    facade.exchange_name = exchange_name
    facade.connect = AsyncMock()
    facade.close = AsyncMock()
    return facade


@pytest.mark.asyncio
async def test_start_and_stop_all_facades() -> None:
    """Starting and stopping should call each registered facade."""
    manager = MessagingManager()
    pubsub = _facade("pub")
    direct = _facade("direct")
    manager.add_pubsub(pubsub)
    manager.add_direct(direct)

    await manager.start_all()
    await manager.stop_all()

    pubsub.connect.assert_awaited_once()
    direct.connect.assert_awaited_once()
    pubsub.close.assert_awaited_once()
    direct.close.assert_awaited_once()


def test_add_pubsub_rejects_duplicate_exchange() -> None:
    """Adding duplicate pubsub exchanges should raise ValueError."""
    manager = MessagingManager()
    manager.add_pubsub(_facade("pub"))

    with pytest.raises(ValueError, match="already exists"):
        manager.add_pubsub(_facade("pub"))


def test_add_direct_rejects_duplicate_exchange() -> None:
    """Adding duplicate direct exchanges should raise ValueError."""
    manager = MessagingManager()
    manager.add_direct(_facade("direct"))

    with pytest.raises(ValueError, match="already exists"):
        manager.add_direct(_facade("direct"))


def test_add_multiple_and_get_facades() -> None:
    """Adding multiple facades should make them retrievable by exchange."""
    manager = MessagingManager()
    pubsub = _facade("pub")
    direct = _facade("direct")

    manager.add_pubsubs([pubsub])
    manager.add_directs([direct])

    assert manager.get_pubsub("pub") == pubsub
    assert manager.get_direct("direct") == direct


def test_get_pubsub_raises_when_missing() -> None:
    """Getting a missing pubsub should raise ValueError."""
    manager = MessagingManager()

    with pytest.raises(ValueError, match="No PubSubFacade"):
        manager.get_pubsub("missing")


def test_get_direct_raises_when_missing() -> None:
    """Getting a missing direct facade should raise ValueError."""
    manager = MessagingManager()

    with pytest.raises(ValueError, match="No DirectMessageFacade"):
        manager.get_direct("missing")
