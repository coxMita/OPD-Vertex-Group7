"""Unit tests for the email proxy router."""

from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
@patch("src.utils.http_client.client.request")
async def test_proxy_post_send_email(
    mock_request: AsyncMock, client: TestClient
) -> None:
    """Test POST /api/v1/email/send is proxied to email-service /api/send."""
    mock_response = AsyncMock()
    mock_response.status_code = status.HTTP_202_ACCEPTED
    mock_response.content = (
        b'{"status":"accepted","message":"Email event published to queue."}'
    )
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response

    payload = {
        "to_email": "patient@example.com",
        "subject": "Test",
        "message": "Hello",
        "is_html": False,
    }
    response = client.post("/api/v1/email/send", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["status"] == "accepted"
    mock_request.assert_called_once_with(
        method="POST",
        url="http://email-service:8000/api/send",
        headers=mock_request.call_args[1]["headers"],
        content=mock_request.call_args[1]["content"],
    )
