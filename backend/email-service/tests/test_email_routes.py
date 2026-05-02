"""Tests for email HTTP routes."""

from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.routes.email_routes import _generate_otp, _otp_store, router

_OTP_LENGTH = 6


def _make_app() -> FastAPI:
    """Build a minimal FastAPI app containing only the email router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture(autouse=True)
def _reset_otp_store() -> Generator[None, None, None]:
    """Clear the in-memory OTP store before and after every test."""
    _otp_store.clear()
    yield
    _otp_store.clear()


@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client bound to the email router."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        yield client


# ── _generate_otp ─────────────────────────────────────────────────────────────


def test_generate_otp_is_six_digits() -> None:
    """Generated OTP is exactly 6 digit characters."""
    code = _generate_otp()
    assert len(code) == _OTP_LENGTH
    assert code.isdigit()


def test_generate_otp_produces_varied_output() -> None:
    """Multiple calls do not all return the same value."""
    codes = {_generate_otp() for _ in range(20)}
    assert len(codes) > 1


# ── POST /api/send ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_test_email_returns_202(http_client: AsyncClient) -> None:
    """POST /api/send returns 202 Accepted and queues the event."""
    with patch(
        "src.api.routes.email_routes._publish", new_callable=AsyncMock
    ) as mock_publish:
        response = await http_client.post(
            "/api/send",
            json={"to_email": "a@b.com", "subject": "Hi", "message": "Hello"},
        )

    assert response.status_code == HTTPStatus.ACCEPTED
    assert response.json()["status"] == "accepted"
    mock_publish.assert_called_once()


# ── POST /api/otp/send ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_otp_stores_code(http_client: AsyncClient) -> None:
    """POST /api/otp/send stores a 6-digit numeric code for the email."""
    with patch("src.api.routes.email_routes._publish", new_callable=AsyncMock):
        response = await http_client.post(
            "/api/otp/send", json={"email": "user@example.com"}
        )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "sent"}
    entry = _otp_store.get("user@example.com")
    assert entry is not None
    assert len(entry["code"]) == _OTP_LENGTH
    assert entry["code"].isdigit()


@pytest.mark.asyncio
async def test_send_otp_publishes_html_email(http_client: AsyncClient) -> None:
    """POST /api/otp/send publishes an HTML email with the OTP subject line."""
    with patch(
        "src.api.routes.email_routes._publish", new_callable=AsyncMock
    ) as mock_publish:
        await http_client.post("/api/otp/send", json={"email": "u@x.com"})

    mock_publish.assert_called_once()
    _req, email_event = mock_publish.call_args.args
    assert email_event.to_email == "u@x.com"
    assert email_event.is_html is True
    assert email_event.subject == "Your OPD Vertex verification code"
    assert email_event.message != ""


@pytest.mark.asyncio
async def test_send_otp_otp_in_rendered_html(http_client: AsyncClient) -> None:
    """The published HTML message contains the generated OTP code."""
    with patch(
        "src.api.routes.email_routes._publish", new_callable=AsyncMock
    ) as mock_publish:
        await http_client.post("/api/otp/send", json={"email": "u@x.com"})

    stored_code = _otp_store["u@x.com"]["code"]
    _req, email_event = mock_publish.call_args.args
    assert stored_code in email_event.message


# ── POST /api/otp/verify ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_otp_valid_code(http_client: AsyncClient) -> None:
    """Correct, non-expired code returns valid=True and removes the entry."""
    _otp_store["u@x.com"] = {
        "code": "123456",
        "expires_at": datetime.now(tz=timezone.utc) + timedelta(minutes=5),
    }
    response = await http_client.post(
        "/api/otp/verify", json={"email": "u@x.com", "code": "123456"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"valid": True}
    assert "u@x.com" not in _otp_store


@pytest.mark.asyncio
async def test_verify_otp_unknown_email(http_client: AsyncClient) -> None:
    """Verifying an OTP for an unknown email returns valid=False."""
    response = await http_client.post(
        "/api/otp/verify",
        json={"email": "nobody@x.com", "code": "000000"},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"valid": False}


@pytest.mark.asyncio
async def test_verify_otp_expired_entry(http_client: AsyncClient) -> None:
    """Expired OTP returns valid=False and removes the store entry."""
    _otp_store["u@x.com"] = {
        "code": "123456",
        "expires_at": datetime.now(tz=timezone.utc) - timedelta(minutes=1),
    }
    response = await http_client.post(
        "/api/otp/verify", json={"email": "u@x.com", "code": "123456"}
    )
    assert response.json() == {"valid": False}
    assert "u@x.com" not in _otp_store


@pytest.mark.asyncio
async def test_verify_otp_wrong_code_leaves_entry(http_client: AsyncClient) -> None:
    """Wrong code returns valid=False and keeps the entry for a future retry."""
    _otp_store["u@x.com"] = {
        "code": "123456",
        "expires_at": datetime.now(tz=timezone.utc) + timedelta(minutes=5),
    }
    response = await http_client.post(
        "/api/otp/verify", json={"email": "u@x.com", "code": "999999"}
    )
    assert response.json() == {"valid": False}
    assert "u@x.com" in _otp_store


@pytest.mark.asyncio
async def test_verify_otp_entry_consumed_on_success(
    http_client: AsyncClient,
) -> None:
    """The store entry is deleted after a successful verification."""
    _otp_store["u@x.com"] = {
        "code": "111111",
        "expires_at": datetime.now(tz=timezone.utc) + timedelta(minutes=5),
    }
    await http_client.post(
        "/api/otp/verify", json={"email": "u@x.com", "code": "111111"}
    )
    assert "u@x.com" not in _otp_store
