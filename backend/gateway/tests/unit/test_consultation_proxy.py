"""Unit tests for the consultation proxy router."""

import uuid
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app

CONSULTATION_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))
DOCTOR_ID = str(uuid.UUID("00000000-0000-0000-0001-000000000001"))

_CONSULTATION_JSON = b'{"id": "%b", "doctor_id": "%b", "status": "ACTIVE"}' % (
    CONSULTATION_ID.encode(),
    DOCTOR_ID.encode(),
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    with TestClient(app) as client:
        yield client


def _mock_response(
    status_code: int = status.HTTP_200_OK,
    content: bytes = _CONSULTATION_JSON,
    headers: dict | None = None,
) -> AsyncMock:
    mock = AsyncMock()
    mock.status_code = status_code
    mock.content = content
    mock.headers = headers or {"content-type": "application/json"}
    return mock


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_consultation_by_id_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /{id} should proxy to consultation-service."""
    mock_request.return_value = _mock_response()

    response = client.get(f"/api/v1/consultations/{CONSULTATION_ID}")

    assert response.status_code == status.HTTP_200_OK
    called_url: str = mock_request.call_args[1]["url"]
    assert "consultation-service:8000" in called_url
    assert CONSULTATION_ID in called_url


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_consultations_root_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET / root should proxy to consultation-service."""
    mock_request.return_value = _mock_response(content=b"[]")

    response = client.get("/api/v1/consultations")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_consultations_forwards_query_params(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Query params (e.g. doctor_id) should be forwarded."""
    mock_request.return_value = _mock_response(content=b"[]")

    client.get(f"/api/v1/consultations?doctor_id={DOCTOR_ID}")

    called_url: str = mock_request.call_args[1]["url"]
    assert f"doctor_id={DOCTOR_ID}" in called_url


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_consultation_returns_404(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 404 from consultation-service unchanged."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_404_NOT_FOUND,
        content=b'{"message": "Not found"}',
    )

    response = client.get(f"/api/v1/consultations/{uuid.uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_doctor_consultations(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /doctor/{id} should proxy correctly."""
    mock_request.return_value = _mock_response(content=b"[]")

    response = client.get(f"/api/v1/consultations/doctor/{DOCTOR_ID}")

    assert response.status_code == status.HTTP_200_OK
    called_url: str = mock_request.call_args[1]["url"]
    assert f"doctor/{DOCTOR_ID}" in called_url


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_post_consultation_returns_201(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """POST / should proxy to consultation-service and return downstream status."""
    mock_request.return_value = _mock_response(status_code=status.HTTP_201_CREATED)

    response = client.post(
        "/api/v1/consultations", json={"appointment_id": CONSULTATION_ID}
    )

    assert response.status_code == status.HTTP_201_CREATED
