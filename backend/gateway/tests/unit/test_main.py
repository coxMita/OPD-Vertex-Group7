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


def test_root_response_is_json(client: TestClient) -> None:
    """Root should return JSON content-type."""
    response = client.get("/")
    assert "application/json" in response.headers["content-type"]


def test_health_response_is_json(client: TestClient) -> None:
    """Health should return JSON content-type."""
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
