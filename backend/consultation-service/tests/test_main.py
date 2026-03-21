"""Tests for consultation-service application startup."""

from unittest.mock import AsyncMock

import pytest

import main


@pytest.mark.asyncio
async def test_lifespan_continues_when_messaging_startup_fails(monkeypatch):
    """The API should still start when messaging is optional and unavailable."""
    monkeypatch.setattr(main, "MESSAGING_ENABLED", True)
    monkeypatch.setattr(main, "MESSAGING_REQUIRED", False)
    monkeypatch.setattr(
        main.messaging_manager, "start_all", AsyncMock(side_effect=RuntimeError("boom"))
    )
    stop_all = AsyncMock()
    monkeypatch.setattr(main.messaging_manager, "stop_all", stop_all)

    async with main.lifespan(main.app):
        pass

    stop_all.assert_not_awaited()


@pytest.mark.asyncio
async def test_lifespan_raises_when_messaging_is_required(monkeypatch):
    """Required messaging failures should still abort startup."""
    monkeypatch.setattr(main, "MESSAGING_ENABLED", True)
    monkeypatch.setattr(main, "MESSAGING_REQUIRED", True)
    monkeypatch.setattr(
        main.messaging_manager, "start_all", AsyncMock(side_effect=RuntimeError("boom"))
    )

    with pytest.raises(RuntimeError, match="boom"):
        async with main.lifespan(main.app):
            pass
