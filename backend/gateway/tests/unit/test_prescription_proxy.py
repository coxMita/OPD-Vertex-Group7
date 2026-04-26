"""Unit tests for the prescription proxy router."""

import uuid
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.dependencies.auth import verify_token

CONSULTATION_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))
PRESCRIPTION_ID = str(uuid.UUID("22222222-2222-2222-2222-222222222222"))
PATIENT_ID = str(uuid.UUID("33333333-3333-3333-3333-333333333333"))

_PRESCRIPTION_JSON = (
    b'{"id": "%s", "consultation_id": "%s", "status": "draft", '
    b'"prescription_json": {}, "summary_json": {}, '
    b'"patient_id": "00000000-0000-0000-0000-000000000000", '
    b'"doctor_id": "00000000-0000-0000-0000-000000000000", '
    b'"approved_at": null}'
    % (
        PRESCRIPTION_ID.encode(),
        CONSULTATION_ID.encode(),
    )
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user"}
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(verify_token, None)


def _mock_response(
    status_code: int = status.HTTP_200_OK,
    content: bytes = _PRESCRIPTION_JSON,
    headers: dict | None = None,
) -> AsyncMock:
    mock = AsyncMock()
    mock.status_code = status_code
    mock.content = content
    mock.headers = headers or {"content-type": "application/json"}
    return mock


# ── GET /api/v1/prescriptions/consultation/{id} ───────────────────────────────


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_prescription_by_consultation_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /consultation/{id} should proxy to prescription-service and return 200."""
    mock_request.return_value = _mock_response()

    response = client.get(f"/api/v1/prescriptions/consultation/{CONSULTATION_ID}")

    assert response.status_code == status.HTTP_200_OK
    mock_request.assert_called_once_with(
        method="GET",
        url=f"http://prescription-service:8000/api/v1/prescriptions/consultation/{CONSULTATION_ID}",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_prescription_by_consultation_returns_404(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 404 from prescription-service unchanged."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_404_NOT_FOUND,
        content=b'{"message": "Prescription not found"}',
    )

    response = client.get(f"/api/v1/prescriptions/consultation/{uuid.uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ── GET /api/v1/prescriptions/{id} ───────────────────────────────────────────


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_prescription_by_id_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /{id} should proxy to prescription-service and return 200."""
    mock_request.return_value = _mock_response()

    response = client.get(f"/api/v1/prescriptions/{PRESCRIPTION_ID}")

    assert response.status_code == status.HTTP_200_OK
    mock_request.assert_called_once_with(
        method="GET",
        url=f"http://prescription-service:8000/api/v1/prescriptions/{PRESCRIPTION_ID}",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_prescription_by_id_returns_404(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 404 from prescription-service unchanged."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_404_NOT_FOUND,
        content=b'{"message": "Prescription not found"}',
    )

    response = client.get(f"/api/v1/prescriptions/{uuid.uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ── GET /api/v1/prescriptions/patient/{id} ───────────────────────────────────


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_get_prescriptions_by_patient_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """GET /patient/{id} should proxy to prescription-service and return 200."""
    mock_request.return_value = _mock_response(content=b"[]")

    response = client.get(f"/api/v1/prescriptions/patient/{PATIENT_ID}")

    assert response.status_code == status.HTTP_200_OK
    mock_request.assert_called_once_with(
        method="GET",
        url=f"http://prescription-service:8000/api/v1/prescriptions/patient/{PATIENT_ID}",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )


# ── PATCH /api/v1/prescriptions/{id}/approve ─────────────────────────────────


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_approve_prescription_returns_200(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """PATCH /{id}/approve should proxy to prescription-service and return 200."""
    approved = _PRESCRIPTION_JSON.replace(b'"draft"', b'"approved"')
    mock_request.return_value = _mock_response(content=approved)

    response = client.patch(f"/api/v1/prescriptions/{PRESCRIPTION_ID}/approve")

    assert response.status_code == status.HTTP_200_OK
    mock_request.assert_called_once_with(
        method="PATCH",
        url=f"http://prescription-service:8000/api/v1/prescriptions/{PRESCRIPTION_ID}/approve",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_approve_prescription_returns_404(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 404 from prescription-service when not found."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_404_NOT_FOUND,
        content=b'{"message": "Prescription not found"}',
    )

    response = client.patch(f"/api/v1/prescriptions/{uuid.uuid4()}/approve")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ── Query string forwarding ───────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_prescription_proxy_forwards_query_params(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Proxy should forward any query parameters to prescription-service."""
    mock_request.return_value = _mock_response(content=b"[]")

    response = client.get(f"/api/v1/prescriptions/patient/{PATIENT_ID}?status=draft")

    assert response.status_code == status.HTTP_200_OK
    called_url: str = mock_request.call_args[1]["url"]
    assert "status=draft" in called_url


# ── HTTP method forwarding ────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_prescription_proxy_forwards_correct_method(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Proxy should forward the exact HTTP method."""
    mock_request.return_value = _mock_response()

    client.get(f"/api/v1/prescriptions/{PRESCRIPTION_ID}")

    assert mock_request.call_args[1]["method"] == "GET"


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_prescription_proxy_patch_forwards_correct_method(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Proxy should forward PATCH method correctly."""
    mock_request.return_value = _mock_response()

    client.patch(f"/api/v1/prescriptions/{PRESCRIPTION_ID}/approve")

    assert mock_request.call_args[1]["method"] == "PATCH"


# ── Downstream error passthrough ──────────────────────────────────────────────


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_prescription_proxy_passes_through_500(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Should pass through 500 from prescription-service unchanged."""
    mock_request.return_value = _mock_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=b'{"detail": "Internal Server Error"}',
    )

    response = client.get(f"/api/v1/prescriptions/{PRESCRIPTION_ID}")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
