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


def _make_generate_side_effect(summary: str, prescription_json: str) -> object:
    """Return a callable side_effect for generate().

    _summarise_chunk() is called once per prescription candidate chunk before
    the two real AI passes (summary + prescription).  The number of chunks
    varies with transcript length, so a fixed list would either run short or
    leave leftovers.  This callable returns NO_MEDICAL_CONTENT for every call
    until only two remain, at which point it returns the summary then the
    prescription JSON — matching the actual call order in process_transcript().
    """

    async def _side_effect(prompt: str) -> str:
        # Detect the summary pass by the SUMMARY_PROMPT_TEMPLATE marker
        if "produce a concise clinical summary" in prompt:
            return summary
        # Detect the prescription pass by its marker
        if "PRIMARY medication prescribed" in prompt:
            return prescription_json
        # Detect the clinical alerts pass by its marker
        if "identify every symptom" in prompt:
            return "ALL_ADDRESSED"
        # All other calls are _summarise_chunk — return empty (no clinical content)
        return "NO_MEDICAL_CONTENT"

    return _side_effect


_FAKE_VECTOR = [0.1] * 768
# embed() is called once for the summary query vector; the prescription path
# only calls embed() a second time when candidates exceed top_k (sub-session).
# With the short _FAKE_TRANSCRIPT that fits in 1–2 chunks this does not happen,
# so the minimum observable call count is 1.
_MIN_EMBED_CALLS = 1
_EXPECTED_GENERATE_CALLS = 2  # summary pass + prescription pass
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
        "embed_batch": patch(
            "src.ai.service.embed_batch",
            new=AsyncMock(return_value=[[0.1] * 768] * 2),
        ),
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
            # Use a callable side_effect so _summarise_chunk calls (one per chunk,
            # unknown count) always return NO_MEDICAL_CONTENT, while the two
            # real AI passes return the expected values regardless of chunk count.
            new=AsyncMock(
                side_effect=_make_generate_side_effect(
                    _FAKE_SUMMARY, _FAKE_PRESCRIPTION_JSON
                )
            ),
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
        assert "clinical_alerts" in body
        assert isinstance(body["clinical_alerts"], list)

    async def test_embed_batch_called_once_for_chunks(
        self, mock_pipeline: dict
    ) -> None:
        """embed_batch() should be called once for the main chunk batch."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            await client.post("/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT})

        mock_pipeline["embed_batch"].assert_awaited()

    async def test_embed_called_for_each_query_vector(
        self, mock_pipeline: dict
    ) -> None:
        """embed() should be called at least once — summary query vector."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            await client.post("/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT})

        assert mock_pipeline["embed"].call_count >= _MIN_EMBED_CALLS

    async def test_store_chunks_called_at_least_once(self, mock_pipeline: dict) -> None:
        """store_chunks() should be called at least once per request."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            await client.post("/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT})

        assert mock_pipeline["store_chunks"].call_count >= 1

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
        mock_pipeline["delete"].assert_awaited()

    async def test_prescription_with_null_fields(self, mock_pipeline: dict) -> None:
        """Should handle a no-prescription response correctly."""
        null_prescription = (
            '{"medication_name": null, "dosage": null, "frequency": null,'
            ' "duration": null, "notes": "No prescription indicated."}'
        )
        mock_pipeline["generate"].side_effect = _make_generate_side_effect(
            _FAKE_SUMMARY, null_prescription
        )

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

    async def test_422_for_empty_transcript(self) -> None:
        """An empty transcript string should be rejected at the schema level."""
        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.post("/ai/prompt", json={"transcript": ""})

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_502_propagates_error_detail(self, mock_pipeline: dict) -> None:
        """The detail field of a 502 should contain the RuntimeError message."""
        mock_pipeline["generate"].side_effect = RuntimeError("Ollama timed out")

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/ai/prompt", json={"transcript": _FAKE_TRANSCRIPT}
            )

        assert response.status_code == HTTPStatus.BAD_GATEWAY
        assert "Ollama timed out" in response.json()["detail"]
