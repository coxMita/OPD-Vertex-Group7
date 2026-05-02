"""Pytest configuration and shared fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def amqp_message() -> MagicMock:
    """Return a mock aio_pika incoming message with async process() context manager."""
    msg = MagicMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = msg
    msg.process.return_value = cm
    msg.ack = AsyncMock()
    msg.nack = AsyncMock()
    msg.reject = AsyncMock()
    return msg
