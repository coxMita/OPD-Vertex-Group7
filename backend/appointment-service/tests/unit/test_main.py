"""Unit tests for appointment-service entrypoint helpers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import main
from src.models.db.appointment import TimePreference


def test_root_returns_service_name() -> None:
    """Root endpoint should identify the service."""
    assert main.root() == {"service": "appointment-service"}


def test_health_returns_ok() -> None:
    """Health endpoint should return ok."""
    assert main.health() == {"status": "ok"}


def test_get_repo_returns_appointment_repository() -> None:
    """The repo factory should create repositories with fresh sessions."""
    with patch("main.Session") as session_cls:
        repo = main._get_repo()

    session_cls.assert_called_once_with(main._engine)
    assert repo._session == session_cls.return_value


@pytest.mark.asyncio
async def test_trigger_session_uses_am_preference() -> None:
    """The debug trigger should call the scheduler with AM preference."""
    with (
        patch("main._get_repo", return_value=MagicMock()) as get_repo,
        patch("main._notify_session", new=AsyncMock()) as notify,
    ):
        result = await main.trigger_session("am")

    assert result == {"triggered": "am"}
    notify.assert_awaited_once_with(
        get_repo.return_value, main.messaging_manager, TimePreference.AM
    )


@pytest.mark.asyncio
async def test_trigger_session_uses_pm_preference() -> None:
    """The debug trigger should call the scheduler with PM preference."""
    with (
        patch("main._get_repo", return_value=MagicMock()) as get_repo,
        patch("main._notify_session", new=AsyncMock()) as notify,
    ):
        result = await main.trigger_session("anything-else")

    assert result == {"triggered": "anything-else"}
    notify.assert_awaited_once_with(
        get_repo.return_value, main.messaging_manager, TimePreference.PM
    )
