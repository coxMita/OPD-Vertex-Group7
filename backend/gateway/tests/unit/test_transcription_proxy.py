"""Unit tests for the transcription proxy router."""

import uuid
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.config import TRANSCRIPTION_SERVICE_URL
from src.dependencies.auth import verify_token

CONSULTATION_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))

_TRANSCRIPT_RESPONSE = b'{"transcript": "Good morning doctor."}'


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user"}
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(verify_token, None)


def _mock_response(
    status_code: int = status.HTTP_200_OK,
    content: bytes = _TRANSCRIPT_RESPONSE,
    headers: dict | None = None,
) -> AsyncMock:
    mock = AsyncMock()
    mock.status_code = status_code
    mock.content = content
    mock.headers = headers or {"content-type": "application/json"}
    return mock


# ── POST /api/v1/transcription/ ───────────────────────────────────────────────


@pytest.mark.asyncio
@patch("src.routers.transcription_proxy._transcription_client.request")
async def test_transcription_proxy_forwards_post(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """POST /api/v1/transcription/ should proxy to transcription-service."""
    mock_request.return_value = _mock_response()

    response = client.post(
        f"/api/v1/transcription/?consultation_id={CONSULTATION_ID}",
        content=b"fake-wav-bytes",
        headers={"content-type": "audio/wav"},
    )

    assert response.status_code == status.HTTP_200_OK
    mock_request.assert_called_once()


@pytest.mark.asyncio
@patch("src.routers.transcription_proxy._transcription_client.request")
async def test_transcription_proxy_forwards_consultation_id_query_param(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """consultation_id query param must be forwarded to transcription-service."""
    mock_request.return_value = _mock_response()

    client.post(
        f"/api/v1/transcription/?consultation_id={CONSULTATION_ID}",
        content=b"fake-wav-bytes",
    )

    called_url: str = mock_request.call_args[1]["url"]
    assert "consultation_id=" in called_url
    assert CONSULTATION_ID in called_url


@pytest.mark.asyncio
@patch("src.routers.transcription_proxy._transcription_client.request")
async def test_transcription_proxy_targets_correct_service_url(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Proxy should target the transcription-service URL."""
    mock_request.return_value = _mock_response()

    client.post(
        f"/api/v1/transcription/?consultation_id={CONSULTATION_ID}",
        content=b"bytes",
    )

    called_url: str = mock_request.call_args[1]["url"]
    assert called_url.startswith(f"{TRANSCRIPTION_SERVICE_URL}/transcription/")
    assert "/transcription/" in called_url


@pytest.mark.asyncio
@patch("src.routers.transcription_proxy._transcription_client.request")
async def test_transcription_proxy_passes_through_422(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 422 from transcription-service unchanged."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=b'{"detail": [{"msg": "Field required"}]}',
    )

    response = client.post(
        f"/api/v1/transcription/?consultation_id={CONSULTATION_ID}",
        content=b"bytes",
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
@patch("src.routers.transcription_proxy._transcription_client.request")
async def test_transcription_proxy_passes_through_500(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 500 from transcription-service unchanged."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=b'{"detail": "model error"}',
    )

    response = client.post(
        f"/api/v1/transcription/?consultation_id={CONSULTATION_ID}",
        content=b"bytes",
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@patch("src.routers.transcription_proxy._transcription_client.request")
async def test_transcription_proxy_forwards_body(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Request body (WAV bytes) should be forwarded to the downstream service."""
    mock_request.return_value = _mock_response()
    wav_bytes = b"RIFF" + b"\x00" * 40  # minimal fake WAV header

    client.post(
        f"/api/v1/transcription/?consultation_id={CONSULTATION_ID}",
        content=wav_bytes,
    )

    forwarded_body: bytes = mock_request.call_args[1]["content"]
    assert forwarded_body == wav_bytes


@pytest.mark.asyncio
@patch("src.routers.transcription_proxy._transcription_client.request")
async def test_transcription_proxy_uses_post_method(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Proxy should always forward as POST."""
    mock_request.return_value = _mock_response()

    client.post(
        f"/api/v1/transcription/?consultation_id={CONSULTATION_ID}",
        content=b"bytes",
    )

    assert mock_request.call_args[1]["method"] == "POST"
