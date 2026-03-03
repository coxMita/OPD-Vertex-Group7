"""Unit tests for src/messaging/messaging_manager.py."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_facade import PubSubFacade


def _make_facade(exchange: str) -> MagicMock:
    facade = MagicMock(spec=PubSubFacade)
    facade.exchange_name = exchange
    facade.connect = AsyncMock()
    facade.close = AsyncMock()
    return facade


# ── add_pubsub ────────────────────────────────────────────────────────────────


class TestAddPubSub:
    """Tests for MessagingManager.add_pubsub()."""

    def test_add_single_facade(self) -> None:
        """A facade can be retrieved after being added."""
        manager = MessagingManager()
        facade = _make_facade("exchange_a")
        manager.add_pubsub(facade)
        assert manager.get_pubsub("exchange_a") is facade

    def test_add_duplicate_raises(self) -> None:
        """Adding a second facade with the same exchange name raises ValueError."""
        manager = MessagingManager()
        manager.add_pubsub(_make_facade("exchange_a"))
        with pytest.raises(ValueError, match="exchange_a"):
            manager.add_pubsub(_make_facade("exchange_a"))

    def test_add_multiple_different_exchanges(self) -> None:
        """Multiple facades with different exchange names can coexist."""
        manager = MessagingManager()
        facade_a = _make_facade("exchange_a")
        facade_b = _make_facade("exchange_b")
        manager.add_pubsub(facade_a)
        manager.add_pubsub(facade_b)
        assert manager.get_pubsub("exchange_a") is facade_a
        assert manager.get_pubsub("exchange_b") is facade_b


# ── add_pubsubs ───────────────────────────────────────────────────────────────


class TestAddPubSubs:
    """Tests for MessagingManager.add_pubsubs()."""

    def test_adds_all_facades(self) -> None:
        """All facades in the list are registered."""
        manager = MessagingManager()
        facades = [_make_facade("ex_1"), _make_facade("ex_2"), _make_facade("ex_3")]
        manager.add_pubsubs(facades)
        for f in facades:
            assert manager.get_pubsub(f.exchange_name) is f

    def test_raises_on_duplicate_within_batch(self) -> None:
        """Duplicate exchange in the same batch raises ValueError."""
        manager = MessagingManager()
        with pytest.raises(ValueError):
            manager.add_pubsubs([_make_facade("dup"), _make_facade("dup")])

    def test_raises_on_duplicate_with_existing(self) -> None:
        """Duplicate exchange against an already-registered facade raises ValueError."""
        manager = MessagingManager()
        manager.add_pubsub(_make_facade("existing"))
        with pytest.raises(ValueError):
            manager.add_pubsubs([_make_facade("existing")])


# ── get_pubsub ────────────────────────────────────────────────────────────────


class TestGetPubSub:
    """Tests for MessagingManager.get_pubsub()."""

    def test_get_existing_facade(self) -> None:
        """Returns the correct facade for a known exchange name."""
        manager = MessagingManager()
        facade = _make_facade("exchange_x")
        manager.add_pubsub(facade)
        assert manager.get_pubsub("exchange_x") is facade

    def test_get_nonexistent_raises(self) -> None:
        """Raises ValueError when the exchange name is not registered."""
        manager = MessagingManager()
        with pytest.raises(ValueError, match="ghost_exchange"):
            manager.get_pubsub("ghost_exchange")

    def test_get_correct_facade_among_multiple(self) -> None:
        """Returns the correct facade when several are registered."""
        manager = MessagingManager()
        fa = _make_facade("alpha")
        fb = _make_facade("beta")
        manager.add_pubsubs([fa, fb])
        assert manager.get_pubsub("beta") is fb


# ── start_all / stop_all ──────────────────────────────────────────────────────


class TestStartStopAll:
    """Tests for MessagingManager.start_all() and stop_all()."""

    @pytest.mark.asyncio
    async def test_start_all_connects_every_facade(self) -> None:
        """start_all calls connect() on every registered facade."""
        manager = MessagingManager()
        facades = [_make_facade("e1"), _make_facade("e2")]
        manager.add_pubsubs(facades)
        await manager.start_all()
        for f in facades:
            f.connect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_all_closes_every_facade(self) -> None:
        """stop_all calls close() on every registered facade."""
        manager = MessagingManager()
        facades = [_make_facade("e1"), _make_facade("e2")]
        manager.add_pubsubs(facades)
        await manager.stop_all()
        for f in facades:
            f.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_all_empty_manager(self) -> None:
        """start_all does not raise when no facades are registered."""
        manager = MessagingManager()
        await manager.start_all()

    @pytest.mark.asyncio
    async def test_stop_all_empty_manager(self) -> None:
        """stop_all does not raise when no facades are registered."""
        manager = MessagingManager()
        await manager.stop_all()
