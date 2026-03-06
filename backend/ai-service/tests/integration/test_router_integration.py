"""Integration tests for the AI service HTTP API.

These tests spin up the full FastAPI app but mock all external dependencies
(Ollama, pgvector, RabbitMQ) so no running infrastructure is required.
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.ai.router import router

# Minimal app without lifespan for integration testing
_app = FastAPI()
_app.include_router(router)

_FAKE_VECTOR = [0.1] * 768
_MIN_EMBED_CALLS = 3
_EXPECTED_GENERATE_CALLS = 2
_FAKE_TRANSCRIPT = (
    "Doctor: Good morning. Patient: I have had a sore throat and fever "
    "for three days. Doctor: I can see tonsillar inflammation. I will "
    "prescribe Amoxicillin 500mg three times daily for 7 days."
)
_FAKE_SUMMARY = (
    "Patient presented with a 3-day sore throat and fever. "
    "Tonsillar inflammation was noted. Amoxicillin 500mg was prescribed "
    "three times daily for 7 days."
)
_FAKE_PRESCRIPTION_JSON = """{
    "medication_name": "Amoxicillin",
    "dosage": "500mg",
    "frequency": "three times a day",
    "duration": "7 days",
    "notes": null
}"""


@pytest.fixture()
def mock_pipeline() -> dict:
    """Patch all external dependencies for the RAG pipeline."""
    patches = {
        "embed": patch(
            "src.ai.service.embed",
            new=AsyncMock(return_value=_FAKE_VECTOR),
        ),
        "store_chunks": patch("src.ai.service.store_chunks", new=AsyncMock()),
        "retrieve": patch(
            "src.ai.service.retrieve_relevant_chunks",
            new=AsyncMock(return_value=["chunk one", "chunk two"]),
        ),
        "delete": patch("src.ai.service.delete_session", new=AsyncMock()),
        "generate": patch(
            "src.ai.service.generate",
            new=AsyncMock(side_effect=[_FAKE_SUMMARY, _FAKE_PRESCRIPTION_JSON]),
        ),
    }
    started = {k: p.start() for k, p in patches.items()}
    yield started
    for p in patches.values():
        p.stop()


@pytest.mark.asyncio
class TestPromptEndpointIntegration:
    """Integration tests for POST /ai/prompt."""

    async def test_full_pipeline_returns_200(self, mock_pipeline: dict) -> None:
        """Should return 200 with both summary and prescription."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT}
            )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["summary"] == _FAKE_SUMMARY
        assert body["prescription"]["medication_name"] == "Amoxicillin"
        assert body["prescription"]["dosage"] == "500mg"

    async def test_embed_called_for_each_query(self, mock_pipeline: dict) -> None:
        """embed() should be called for chunks + 2 query vectors."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            await client.post("/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT})

        embed_mock = mock_pipeline["embed"]
        assert embed_mock.call_count >= _MIN_EMBED_CALLS

    async def test_store_chunks_called_once(self, mock_pipeline: dict) -> None:
        """store_chunks() should be called exactly once per request."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            await client.post("/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT})

        mock_pipeline["store_chunks"].assert_called_once()

    async def test_delete_session_always_called(self, mock_pipeline: dict) -> None:
        """delete_session() must be called even when generate raises."""
        mock_pipeline["generate"].side_effect = RuntimeError("Ollama down")

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT}
            )

        assert response.status_code == HTTPStatus.BAD_GATEWAY
        mock_pipeline["delete"].assert_called_once()

    async def test_generate_called_twice(self, mock_pipeline: dict) -> None:
        """generate() should be called twice: summary + prescription."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            await client.post("/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT})

        assert mock_pipeline["generate"].call_count == _EXPECTED_GENERATE_CALLS

    async def test_prescription_with_null_fields(self, mock_pipeline: dict) -> None:
        """Should handle a no-prescription response correctly."""
        null_prescription = (
            '{"medication_name": null, "dosage": null, "frequency": null,'
            ' "duration": null, "notes": "No prescription indicated."}'
        )
        mock_pipeline["generate"].side_effect = [_FAKE_SUMMARY, null_prescription]

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/ai/prompt", json={"transcript": "Patient advised to rest."}
            )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["prescription"]["medication_name"] is None
        assert body["prescription"]["notes"] == "No prescription indicated."

    async def test_route_exists(self) -> None:
        """POST /ai/prompt route should exist (not 404)."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get("/ai/prompt")

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
