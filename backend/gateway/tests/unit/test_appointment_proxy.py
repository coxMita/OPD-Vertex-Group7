"""Unit tests for the appointment proxy router."""

from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    with TestClient(app) as client:
        yield client


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_get_appointment(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test GET request is proxied correctly to appointment-service."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.content = b'{"id": 1, "patient_id": 1, "doctor_id": 1}'
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response

    response = client.get("/api/v1/appointments/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "patient_id": 1, "doctor_id": 1}
    mock_request.assert_called_once_with(
        method="GET",
        url="http://appointment-service:8000/api/v1/appointments/1",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_post_appointment(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test POST request is proxied correctly to appointment-service."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_201_CREATED
    mock_response.content = b'{"id": 1, "status": "scheduled"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response

    payload = {
        "patient_id": 1,
        "doctor_id": 1,
        "appointment_date": "2026-03-15",
        "time_preference": "AM",
    }
    response = client.post("/api/v1/appointments", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"id": 1, "status": "scheduled"}
    mock_request.assert_called_once_with(
        method="POST",
        url="http://appointment-service:8000/api/v1/appointments",
        headers=mock_request.call_args[1]["headers"],
        content=mock_request.call_args[1]["content"],
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_patch_appointment_status(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test PATCH request for status update is proxied correctly."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.content = b'{"id": 1, "status": "in_progress"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response

    response = client.patch(
        "/api/v1/appointments/1/status", json={"status": "in_progress"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "status": "in_progress"}
    mock_request.assert_called_once_with(
        method="PATCH",
        url="http://appointment-service:8000/api/v1/appointments/1/status",
        headers=mock_request.call_args[1]["headers"],
        content=mock_request.call_args[1]["content"],
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_delete_appointment(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test DELETE request is proxied correctly to appointment-service."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_204_NO_CONTENT
    mock_response.content = b""
    mock_response.headers = {}
    mock_request.return_value = mock_response

    response = client.delete("/api/v1/appointments/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_request.assert_called_once_with(
        method="DELETE",
        url="http://appointment-service:8000/api/v1/appointments/1",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_get_queue_with_query_params(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test GET queue request with query params is proxied correctly."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.content = b'[{"id": 1}, {"id": 2}]'
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response

    response = client.get(
        "/api/v1/appointments/queue/day?doctor_id=1&appointment_date=2026-03-15"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id": 1}, {"id": 2}]
    mock_request.assert_called_once_with(
        method="GET",
        url="http://appointment-service:8000/api/v1/appointments/queue/day?doctor_id=1&appointment_date=2026-03-15",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_returns_404_from_downstream(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test that a 404 from appointment-service is passed through unchanged."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_404_NOT_FOUND
    mock_response.content = b'{"message": "Appointment not found"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response

    response = client.get("/api/v1/appointments/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"message": "Appointment not found"}


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_get_patient_appointments(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test GET patient appointments is proxied correctly."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.content = b'[{"id": 1, "patient_id": 5}]'
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response

    response = client.get("/api/v1/appointments/patient/5")

    assert response.status_code == status.HTTP_200_OK
    mock_request.assert_called_once_with(
        method="GET",
        url="http://appointment-service:8000/api/v1/appointments/patient/5",
        headers=mock_request.call_args[1]["headers"],
        content=b"",
    )
