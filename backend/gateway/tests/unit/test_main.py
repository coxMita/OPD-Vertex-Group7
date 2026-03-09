"""Unit tests for the main gateway endpoints."""

from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture to initialize the FastAPI TestClient."""
    with TestClient(app) as client:
        yield client


def test_root(client: TestClient) -> None:
    """Test the root endpoint (GET /)."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"service": "opd-vertex-gateway"}


def test_health(client: TestClient) -> None:
    """Test the health check endpoint (GET /health)."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
