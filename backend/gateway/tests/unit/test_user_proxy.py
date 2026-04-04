"""Unit tests for the user proxy router."""

import uuid
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app

PATIENT_ID = str(uuid.UUID("33333333-3333-3333-3333-333333333333"))
DOCTOR_ID = str(uuid.UUID("00000000-0000-0000-0001-000000000001"))

_PATIENT_JSON = (
    b'{"patient_id": "%b", "email": "test@example.com"}' % PATIENT_ID.encode()
)
_DOCTOR_JSON = b'{"doctor_id": "%b", "full_name": "House"}' % DOCTOR_ID.encode()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    with TestClient(app) as client:
        yield client


def _mock_response(
    status_code: int = status.HTTP_200_OK,
    content: bytes = _PATIENT_JSON,
    headers: dict | None = None,
) -> AsyncMock:
    mock = AsyncMock()
    mock.status_code = status_code
    mock.content = content
    mock.headers = headers or {"content-type": "application/json"}
    return mock


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_patient_by_id_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /patients/{id} should proxy to user-service."""
    mock_request.return_value = _mock_response()

    response = client.get(f"/api/v1/user/patients/{PATIENT_ID}")

    assert response.status_code == status.HTTP_200_OK
    called_url: str = mock_request.call_args[1]["url"]
    assert "user-service:8000" in called_url
    assert f"patients/{PATIENT_ID}" in called_url


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_patient_by_email_forwards_query_param(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /patients/by-email?email=... should forward the query param."""
    mock_request.return_value = _mock_response()

    client.get("/api/v1/user/patients/by-email?email=test@example.com")

    called_url: str = mock_request.call_args[1]["url"]
    assert (
        "email=test%40example.com" in called_url
        or "email=test@example.com" in called_url
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_doctors_by_department(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /doctor/{dept}/doctors should proxy correctly."""
    mock_request.return_value = _mock_response(content=b"[]")

    response = client.get("/api/v1/user/doctor/General%20Practice/doctors")

    assert response.status_code == status.HTTP_200_OK
    called_url: str = mock_request.call_args[1]["url"]
    assert "doctor" in called_url
    assert "doctors" in called_url


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_post_find_or_create_patient(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """POST /patients should proxy find-or-create patient request."""
    mock_request.return_value = _mock_response(status_code=status.HTTP_200_OK)

    payload = {
        "first_name": "Maria",
        "last_name": "Andersen",
        "email": "maria@example.com",
        "phone_number": 12345678,
        "date_of_birth": "1990-01-01",
        "gender": "female",
    }
    response = client.post("/api/v1/user/patients", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert mock_request.call_args[1]["method"] == "POST"


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_user_proxy_root_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /api/v1/user root should proxy to user-service."""
    mock_request.return_value = _mock_response(content=b"[]")

    response = client.get("/api/v1/user")

    assert response.status_code == status.HTTP_200_OK
    called_url: str = mock_request.call_args[1]["url"]
    assert "user-service:8000/api/v1/user" in called_url


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_user_proxy_passes_through_404(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 404 from user-service unchanged."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_404_NOT_FOUND,
        content=b'{"detail": "Not found"}',
    )

    response = client.get(f"/api/v1/user/patients/{uuid.uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
