"""Unit tests for src.ai.router and src.ai.service (mocked dependencies)."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ai.router import router
from src.ai.service import process_transcript

# Minimal app just for router testing — no lifespan/messaging
_app = FastAPI()
_app.include_router(router)

_FAKE_VECTOR = [0.1] * 768


class TestRouter:
    """Unit tests for POST /ai/prompt endpoint."""

    def test_returns_200_with_valid_transcript(self) -> None:
        """Should return 200 with summary and prescription on success."""
        fake_result = {
            "summary": "Patient had fever. Amoxicillin prescribed.",
            "prescription": {
                "medication_name": "Amoxicillin",
                "dosage": "500mg",
                "frequency": "three times a day",
                "duration": "7 days",
                "notes": None,
            },
        }
        with (
            patch(
                "src.ai.router.process_transcript",
                new=AsyncMock(return_value=fake_result),
            ),
            TestClient(_app) as client,
        ):
            response = client.post(
                "/ai/prompt",
                json={"transcript": "Patient has fever and sore throat."},
            )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "summary" in data
        assert "prescription" in data
        assert data["summary"] == fake_result["summary"]

    def test_returns_422_for_empty_transcript(self) -> None:
        """Should return 422 when transcript is an empty string."""
        with TestClient(_app) as client:
            response = client.post("/ai/prompt", json={"transcript": ""})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_returns_422_for_missing_transcript(self) -> None:
        """Should return 422 when transcript field is missing."""
        with TestClient(_app) as client:
            response = client.post("/ai/prompt", json={})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_returns_502_when_process_transcript_raises(self) -> None:
        """Should return 502 when the AI pipeline raises a RuntimeError."""
        with (
            patch(
                "src.ai.router.process_transcript",
                new=AsyncMock(side_effect=RuntimeError("Ollama request failed")),
            ),
            TestClient(_app) as client,
        ):
            response = client.post(
                "/ai/prompt",
                json={"transcript": "Patient has fever."},
            )
        assert response.status_code == HTTPStatus.BAD_GATEWAY
        assert "Ollama request failed" in response.json()["detail"]

    def test_response_schema_matches_model(self) -> None:
        """Response body should match the AIResponse schema exactly."""
        fake_result = {
            "summary": "Summary text.",
            "prescription": {"medication_name": "Ibuprofen"},
        }
        with (
            patch(
                "src.ai.router.process_transcript",
                new=AsyncMock(return_value=fake_result),
            ),
            TestClient(_app) as client,
        ):
            response = client.post(
                "/ai/prompt",
                json={"transcript": "Some transcript text."},
            )
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert set(body.keys()) == {"summary", "prescription"}


class TestProcessTranscript:
    """Unit tests for process_transcript() with all external deps mocked."""

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_summary_and_prescription(self) -> None:
        """Should return dict with summary and prescription keys."""
        fake_chunks = ["chunk one", "chunk two"]
        fake_prescription = {
            "medication_name": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "three times a day",
            "duration": "7 days",
            "notes": None,
        }

        with (
            patch("src.ai.service.chunk_text", return_value=fake_chunks),
            patch(
                "src.ai.service.embed",
                new=AsyncMock(return_value=_FAKE_VECTOR),
            ),
            patch("src.ai.service.store_chunks", new=AsyncMock()),
            patch(
                "src.ai.service.retrieve_relevant_chunks",
                new=AsyncMock(return_value=fake_chunks),
            ),
            patch("src.ai.service.delete_session", new=AsyncMock()),
            patch(
                "src.ai.service.generate",
                new=AsyncMock(
                    side_effect=[
                        "Clinical summary of the consultation.",
                        str(fake_prescription).replace("'", '"'),
                    ]
                ),
            ),
        ):
            result = await process_transcript("Patient has fever.")

        assert "summary" in result
        assert "prescription" in result
        assert result["summary"] == "Clinical summary of the consultation."

    @pytest.mark.asyncio
    async def test_delete_session_called_even_on_error(self) -> None:
        """delete_session should always run even if generate() raises."""
        mock_delete = AsyncMock()

        with (
            patch("src.ai.service.chunk_text", return_value=["chunk"]),
            patch(
                "src.ai.service.embed",
                new=AsyncMock(return_value=_FAKE_VECTOR),
            ),
            patch("src.ai.service.store_chunks", new=AsyncMock()),
            patch(
                "src.ai.service.retrieve_relevant_chunks",
                new=AsyncMock(return_value=["chunk"]),
            ),
            patch("src.ai.service.delete_session", new=mock_delete),
            patch(
                "src.ai.service.generate",
                new=AsyncMock(side_effect=RuntimeError("Ollama down")),
            ),
            pytest.raises(RuntimeError),
        ):
            await process_transcript("Some transcript.")

        mock_delete.assert_called_once()
