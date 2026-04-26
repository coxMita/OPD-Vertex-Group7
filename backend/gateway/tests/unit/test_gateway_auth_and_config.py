"""Tests for gateway auth routing and Keycloak config."""

import importlib
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app

EXPECTED_PUBLIC_CALLS = 2


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client


def _mock_response(
    status_code: int = status.HTTP_200_OK,
    content: bytes = b"[]",
    headers: dict | None = None,
) -> AsyncMock:
    mock = AsyncMock()
    mock.status_code = status_code
    mock.content = content
    mock.headers = headers or {"content-type": "application/json"}
    return mock


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_public_routes_do_not_require_authentication(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """User and appointment routes should be reachable without a bearer token."""
    mock_request.return_value = _mock_response()

    user_response = client.get("/api/v1/user")
    appointment_response = client.get(
        "/api/v1/appointments/queue/day?doctor_id=1&appointment_date=2026-04-26"
    )

    assert user_response.status_code == status.HTTP_200_OK
    assert appointment_response.status_code == status.HTTP_200_OK
    assert mock_request.await_count == EXPECTED_PUBLIC_CALLS


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_consultation_routes_still_require_authentication(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Consultation routes should reject requests that do not include auth."""
    response = client.get("/api/v1/consultations")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    mock_request.assert_not_called()


def test_keycloak_certs_url_uses_internal_url_when_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JWKS lookup should prefer the internal Keycloak URL when available."""
    monkeypatch.setenv("APPOINTMENT_SERVICE_URL", "http://appointment-service:8000")
    monkeypatch.setenv("CONSULTATION_SERVICE_URL", "http://consultation-service:8000")
    monkeypatch.setenv("USER_SERVICE_URL", "http://user-service:8000")
    monkeypatch.setenv("PRESCRIPTION_SERVICE_URL", "http://prescription-service:8000")
    monkeypatch.setenv("TRANSCRIPTION_SERVICE_URL", "http://transcription-service:8000")
    monkeypatch.setenv("KEYCLOAK_REALM", "opd-vertex")
    monkeypatch.setenv("KEYCLOAK_EXTERNAL_URL", "http://localhost:8089")
    monkeypatch.setenv("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080")

    config = importlib.import_module("src.config")
    config = importlib.reload(config)

    assert config.KEYCLOAK_CERTS_URL == (
        "http://keycloak:8080/realms/opd-vertex/protocol/openid-connect/certs"
    )
