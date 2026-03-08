"""Unit tests for src.rag.vector_store (pure functions) and src.ai.service helpers."""

from src.ai.service import _filter_prescription_chunks, _parse_json_safe
from src.rag.vector_store import chunk_text

_CHUNK_SIZE = 200


class TestChunkText:
    """Unit tests for chunk_text() — no I/O, pure function."""

    def test_short_text_returns_single_chunk(self) -> None:
        """Text shorter than chunk_size should return one chunk."""
        text = "Patient has fever and sore throat."
        result = chunk_text(text, chunk_size=_CHUNK_SIZE, overlap=30)
        assert len(result) == 1
        assert result[0] == text

    def test_long_text_splits_into_multiple_chunks(self) -> None:
        """Text longer than chunk_size should be split into multiple chunks."""
        words = ["word"] * 500
        text = " ".join(words)
        result = chunk_text(text, chunk_size=_CHUNK_SIZE, overlap=30)
        assert len(result) > 1

    def test_chunks_overlap(self) -> None:
        """Consecutive chunks should share overlapping words."""
        overlap = 20
        chunk_size = 100
        words = [f"w{i}" for i in range(300)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        end_of_first = chunks[0].split()[-overlap:]
        start_of_second = chunks[1].split()[:overlap]
        assert end_of_first == start_of_second

    def test_empty_text_returns_empty_list(self) -> None:
        """Empty string should return an empty list."""
        result = chunk_text("", chunk_size=_CHUNK_SIZE, overlap=30)
        assert result == []

    def test_each_chunk_respects_max_size(self) -> None:
        """No chunk should exceed chunk_size words."""
        words = ["word"] * 1000
        text = " ".join(words)
        result = chunk_text(text, chunk_size=_CHUNK_SIZE, overlap=30)
        for chunk in result:
            assert len(chunk.split()) <= _CHUNK_SIZE


class TestFilterPrescriptionChunks:
    """Unit tests for _filter_prescription_chunks() — pure function."""

    def test_returns_chunks_containing_keywords(self) -> None:
        """Should return only chunks that contain prescription keywords."""
        chunks = [
            "Patient has a sore throat and mild fever since yesterday.",
            "Doctor will prescribe Amoxicillin 500mg three times daily.",
            "Patient advised to rest and drink plenty of water.",
            "Take the tablet after breakfast for seven days.",
        ]
        result = _filter_prescription_chunks(chunks)
        assert len(result) == 2  # noqa: PLR2004
        assert any("prescribe" in c for c in result)
        assert any("tablet" in c for c in result)

    def test_fallback_to_all_chunks_when_no_match(self) -> None:
        """Should return all chunks when no prescription keywords match."""
        chunks = [
            "The weather is lovely today.",
            "Patient discussed general wellbeing.",
            "Follow-up scheduled for next month.",
        ]
        result = _filter_prescription_chunks(chunks)
        assert result == chunks

    def test_case_insensitive_matching(self) -> None:
        """Keyword matching should be case-insensitive."""
        chunks = [
            "Doctor said PRESCRIBE Ibuprofen immediately.",
            "No relevant medical info here.",
        ]
        result = _filter_prescription_chunks(chunks)
        assert len(result) == 1
        assert "PRESCRIBE" in result[0]

    def test_empty_chunks_returns_empty(self) -> None:
        """Empty input should return empty output."""
        result = _filter_prescription_chunks([])
        assert result == []

    def test_all_chunks_match_returns_all(self) -> None:
        """If every chunk matches, all should be returned."""
        chunks = [
            "Take vitamin C once daily.",
            "Prescribed ibuprofen 400mg twice a day.",
        ]
        result = _filter_prescription_chunks(chunks)
        assert result == chunks


class TestParseJsonSafe:
    """Unit tests for _parse_json_safe() helper in service.py."""

    def test_parses_valid_json(self) -> None:
        """Should correctly parse a well-formed JSON string."""
        raw = '{"medication_name": "Amoxicillin", "dosage": "500mg"}'
        result = _parse_json_safe(raw)
        assert result["medication_name"] == "Amoxicillin"
        assert result["dosage"] == "500mg"

    def test_strips_markdown_fences(self) -> None:
        """Should strip ```json ... ``` fences before parsing."""
        raw = '```json\n{"medication_name": "Paracetamol"}\n```'
        result = _parse_json_safe(raw)
        assert result["medication_name"] == "Paracetamol"

    def test_returns_error_dict_on_invalid_json(self) -> None:
        """Should return error dict when model output is not valid JSON."""
        raw = "I cannot extract a prescription from this transcript."
        result = _parse_json_safe(raw)
        assert "error" in result
        assert result["raw"] == raw

    def test_handles_null_fields(self) -> None:
        """Should correctly parse JSON with null values."""
        raw = (
            '{"medication_name": null, "dosage": null, "frequency": null,'
            ' "duration": null, "notes": "No prescription indicated."}'
        )
        result = _parse_json_safe(raw)
        assert result["medication_name"] is None
        assert result["notes"] == "No prescription indicated."
