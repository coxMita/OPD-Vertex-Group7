"""Unit tests for src.ai.router and src.ai.service (mocked dependencies)."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ai.router import router
from src.ai.service import (
    _dynamic_top_k,
    _hierarchical_summarise,
    _summarise_chunk,
    process_transcript,
)

# Minimal app just for router testing — no lifespan/messaging
_app = FastAPI()
_app.include_router(router)

_FAKE_VECTOR = [0.1] * 768
_FAKE_VECTORS = [[0.1] * 768, [0.2] * 768]


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


class TestDynamicTopK:
    """Unit tests for _dynamic_top_k() — pure function, all branches."""

    def test_five_or_fewer_candidates_returns_all(self) -> None:
        """Fewer than 6 candidates should return count equal to len(candidates)."""
        for n in range(1, 6):
            assert _dynamic_top_k(["x"] * n) == n

    def test_six_to_eight_candidates_returns_all(self) -> None:
        """6–8 candidates should still return the full count."""
        for n in (6, 7, 8):
            assert _dynamic_top_k(["x"] * n) == n

    def test_nine_to_twenty_candidates_capped_at_eight(self) -> None:
        """9–20 candidates should be capped at 8 for llama3.2:3b quality."""
        for n in (9, 15, 20):
            assert _dynamic_top_k(["x"] * n) == 8  # noqa: PLR2004

    def test_over_twenty_candidates_capped_at_eight(self) -> None:
        """Very long transcripts (>20 chunks) should also be capped at 8."""
        assert _dynamic_top_k(["x"] * 50) == 8  # noqa: PLR2004
        assert _dynamic_top_k(["x"] * 100) == 8  # noqa: PLR2004


class TestSummariseChunk:
    """Unit tests for _summarise_chunk() internal helper."""

    @pytest.mark.asyncio
    async def test_returns_stripped_summary_for_medical_content(self) -> None:
        """Should return the model's cleaned response when medical content exists."""
        with patch(
            "src.ai.service.generate",
            new=AsyncMock(return_value="  Patient has fever.  "),
        ):
            result = await _summarise_chunk("Patient has fever since yesterday.")
        assert result == "Patient has fever."

    @pytest.mark.asyncio
    async def test_returns_empty_string_for_no_medical_content(self) -> None:
        """Should return empty string when model responds with NO_MEDICAL_CONTENT."""
        with patch(
            "src.ai.service.generate",
            new=AsyncMock(return_value="NO_MEDICAL_CONTENT"),
        ):
            result = await _summarise_chunk("The weather is nice today.")
        assert result == ""

    @pytest.mark.asyncio
    async def test_no_medical_content_embedded_in_longer_response(self) -> None:
        """Should return empty string when NO_MEDICAL_CONTENT appears mid-response."""
        with patch(
            "src.ai.service.generate",
            new=AsyncMock(return_value="This chunk: NO_MEDICAL_CONTENT present."),
        ):
            result = await _summarise_chunk("Some non-medical text.")
        assert result == ""


class TestHierarchicalSummarise:
    """Unit tests for _hierarchical_summarise() internal helper."""

    @pytest.mark.asyncio
    async def test_filters_out_empty_summaries(self) -> None:
        """Chunks returning NO_MEDICAL_CONTENT should be excluded from output."""
        with patch(
            "src.ai.service.generate",
            new=AsyncMock(
                side_effect=[
                    "Patient has fever.",
                    "NO_MEDICAL_CONTENT",
                    "Amoxicillin prescribed.",
                ]
            ),
        ):
            result = await _hierarchical_summarise(["c1", "c2", "c3"])
        assert len(result) == 2  # noqa: PLR2004
        assert "Patient has fever." in result
        assert "Amoxicillin prescribed." in result

    @pytest.mark.asyncio
    async def test_all_chunks_have_medical_content(self) -> None:
        """Should return all summaries when all chunks have clinical content."""
        summaries = ["Summary A.", "Summary B."]
        with patch(
            "src.ai.service.generate",
            new=AsyncMock(side_effect=summaries),
        ):
            result = await _hierarchical_summarise(["chunk1", "chunk2"])
        assert result == summaries

    @pytest.mark.asyncio
    async def test_all_chunks_empty_returns_empty_list(self) -> None:
        """Should return an empty list when every chunk is non-medical."""
        with patch(
            "src.ai.service.generate",
            new=AsyncMock(side_effect=["NO_MEDICAL_CONTENT", "NO_MEDICAL_CONTENT"]),
        ):
            result = await _hierarchical_summarise(["a", "b"])
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_input_returns_empty_list(self) -> None:
        """Should return an empty list when no chunks are provided."""
        with patch("src.ai.service.generate", new=AsyncMock()):
            result = await _hierarchical_summarise([])
        assert result == []


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
                "src.ai.service.embed_batch",
                new=AsyncMock(return_value=_FAKE_VECTORS),
            ),
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
                        "NO_MEDICAL_CONTENT",  # _summarise_chunk chunk one
                        # _summarise_chunk chunk two
                        "Amoxicillin 500mg prescribed.",
                        "Clinical summary of the consultation.",  # summary pass
                        str(fake_prescription).replace("'", '"'),  # prescription pass
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
                "src.ai.service.embed_batch",
                new=AsyncMock(return_value=[_FAKE_VECTOR]),
            ),
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

    @pytest.mark.asyncio
    async def test_sub_session_created_when_many_candidates(self) -> None:
        """When prescription candidates exceed top_k, a sub-session is used.

        This requires >8 keyword-matched chunks so _dynamic_top_k caps at 8
        and the vector-ranking sub-session path executes.
        """
        # 10 chunks all containing "prescribe" — exceeds the cap of 8
        many_chunks = [f"doctor will prescribe drug {i}" for i in range(10)]

        mock_delete = AsyncMock()
        mock_store = AsyncMock()

        with (
            patch("src.ai.service.chunk_text", return_value=many_chunks),
            patch(
                "src.ai.service.embed_batch",
                new=AsyncMock(return_value=[[0.1] * 768] * 10),
            ),
            patch(
                "src.ai.service.embed",
                new=AsyncMock(return_value=_FAKE_VECTOR),
            ),
            patch("src.ai.service.store_chunks", new=mock_store),
            patch(
                "src.ai.service.retrieve_relevant_chunks",
                new=AsyncMock(return_value=many_chunks[:8]),
            ),
            patch("src.ai.service.delete_session", new=mock_delete),
            patch(
                "src.ai.service.generate",
                new=AsyncMock(
                    side_effect=(
                        # _summarise_chunk for each of the 8 top prescription chunks
                        ["Drug summary."] * 8
                        # summary pass
                        + ["Clinical summary."]
                        # prescription pass
                        + [
                            '{"medication_name": "DrugX",'
                            ' "dosage": null, "frequency": null,'
                            ' "duration": null, "notes": null}'
                        ]
                    )
                ),
            ),
        ):
            result = await process_transcript("long transcript")

        # store_chunks should be called twice: main session + sub-session
        assert mock_store.call_count == 2  # noqa: PLR2004
        # delete_session should also be called twice: sub-session + main session
        assert mock_delete.call_count == 2  # noqa: PLR2004
        assert result["prescription"]["medication_name"] == "DrugX"

    @pytest.mark.asyncio
    async def test_empty_transcript_falls_back_to_single_chunk(self) -> None:
        """When chunk_text returns [], transcript itself is used as one chunk."""
        mock_delete = AsyncMock()

        with (
            patch("src.ai.service.chunk_text", return_value=[]),
            patch(
                "src.ai.service.embed_batch",
                new=AsyncMock(return_value=[_FAKE_VECTOR]),
            ),
            patch(
                "src.ai.service.embed",
                new=AsyncMock(return_value=_FAKE_VECTOR),
            ),
            patch("src.ai.service.store_chunks", new=AsyncMock()),
            patch(
                "src.ai.service.retrieve_relevant_chunks",
                new=AsyncMock(return_value=["fallback chunk"]),
            ),
            patch("src.ai.service.delete_session", new=mock_delete),
            patch(
                "src.ai.service.generate",
                new=AsyncMock(
                    side_effect=[
                        "NO_MEDICAL_CONTENT",
                        "Fallback summary.",
                        '{"medication_name": null, "dosage": null,'
                        ' "frequency": null, "duration": null,'
                        ' "notes": "No prescription indicated."}',
                    ]
                ),
            ),
        ):
            result = await process_transcript("short text")

        assert "summary" in result
        mock_delete.assert_called_once()
