"""Unit tests for src.rag.vector_store (pure functions and async DB ops).

And src.ai.service helpers.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.service import _filter_prescription_chunks, _parse_json_safe
from src.rag.vector_store import (
    chunk_text,
    delete_session,
    init_db,
    retrieve_relevant_chunks,
    store_chunks,
)

_CHUNK_SIZE = 200
_EMBEDDING_DIM = 768


# ---------------------------------------------------------------------------
# chunk_text — pure, no I/O
# ---------------------------------------------------------------------------


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

    def test_exact_chunk_size_text_returns_single_chunk(self) -> None:
        """Text with exactly chunk_size words should return exactly one chunk."""
        text = " ".join(["word"] * _CHUNK_SIZE)
        result = chunk_text(text, chunk_size=_CHUNK_SIZE, overlap=0)
        assert len(result) == 1
        assert len(result[0].split()) == _CHUNK_SIZE

    def test_whitespace_only_returns_empty_list(self) -> None:
        """Text consisting only of whitespace has no words and returns []."""
        result = chunk_text("   \t\n  ", chunk_size=_CHUNK_SIZE, overlap=30)
        assert result == []


# ---------------------------------------------------------------------------
# init_db — mocked asyncpg pool
# ---------------------------------------------------------------------------


class TestInitDb:
    """Unit tests for init_db() — verifies SQL execution against mock pool."""

    @pytest.mark.asyncio
    async def test_creates_extension_and_table(self) -> None:
        """init_db should execute CREATE EXTENSION and CREATE TABLE statements."""
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await init_db()

        calls = [str(c) for c in mock_conn.execute.call_args_list]
        assert any("CREATE EXTENSION" in c for c in calls)
        assert any("transcript_chunks" in c for c in calls)

    @pytest.mark.asyncio
    async def test_creates_index(self) -> None:
        """init_db should create the session index."""
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await init_db()

        calls = [str(c) for c in mock_conn.execute.call_args_list]
        assert any("CREATE INDEX" in c for c in calls)


# ---------------------------------------------------------------------------
# store_chunks — mocked asyncpg pool
# ---------------------------------------------------------------------------


class TestStoreChunks:
    """Unit tests for store_chunks() — verifies correct SQL and args."""

    @pytest.mark.asyncio
    async def test_inserts_correct_number_of_rows(self) -> None:
        """Should call executemany with a row for each chunk."""
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        chunks = ["chunk one", "chunk two", "chunk three"]
        vectors = [[0.1] * _EMBEDDING_DIM] * 3

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await store_chunks("session-abc", chunks, vectors)

        mock_conn.executemany.assert_called_once()
        _, rows = mock_conn.executemany.call_args.args
        assert len(rows) == 3  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_rows_contain_session_id_and_chunk(self) -> None:
        """Each row tuple should carry the session_id and the chunk text."""
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        session_id = "test-session-id"
        chunks = ["hello world"]
        vectors = [[0.5] * _EMBEDDING_DIM]

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await store_chunks(session_id, chunks, vectors)

        _, rows = mock_conn.executemany.call_args.args
        row = rows[0]
        assert row[1] == session_id  # position 1 = session_id
        assert row[2] == "hello world"  # position 2 = chunk

    @pytest.mark.asyncio
    async def test_vector_formatted_as_postgres_array_string(self) -> None:
        """Embedding should be formatted as '[v1,v2,...]' for pgvector."""
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        chunks = ["chunk"]
        vectors = [[0.1, 0.2, 0.3]]

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await store_chunks("sid", chunks, vectors)

        _, rows = mock_conn.executemany.call_args.args
        embedding_str: str = rows[0][3]
        assert embedding_str.startswith("[")
        assert embedding_str.endswith("]")
        assert "0.1" in embedding_str


# ---------------------------------------------------------------------------
# retrieve_relevant_chunks — mocked asyncpg pool
# ---------------------------------------------------------------------------


class TestRetrieveRelevantChunks:
    """Unit tests for retrieve_relevant_chunks()."""

    @pytest.mark.asyncio
    async def test_returns_chunk_strings_in_order(self) -> None:
        """Should return the 'chunk' field from each fetched row."""
        mock_rows = [{"chunk": "first chunk"}, {"chunk": "second chunk"}]
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            result = await retrieve_relevant_chunks(
                "sid", [0.1] * _EMBEDDING_DIM, top_k=2
            )

        assert result == ["first chunk", "second chunk"]

    @pytest.mark.asyncio
    async def test_passes_top_k_to_query(self) -> None:
        """top_k value should be forwarded as the LIMIT parameter."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await retrieve_relevant_chunks("sid", [0.0] * _EMBEDDING_DIM, top_k=7)

        call_args = mock_conn.fetch.call_args.args
        # $3 is the LIMIT — passed as the 3rd positional arg after sql and session_id
        assert call_args[3] == 7  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_rows(self) -> None:
        """Should return an empty list when the query yields no results."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            result = await retrieve_relevant_chunks("sid", [0.0] * _EMBEDDING_DIM)

        assert result == []


# ---------------------------------------------------------------------------
# delete_session — mocked asyncpg pool
# ---------------------------------------------------------------------------


class TestDeleteSession:
    """Unit tests for delete_session()."""

    @pytest.mark.asyncio
    async def test_executes_delete_with_correct_session_id(self) -> None:
        """Should run DELETE WHERE session_id = $1 with the correct value."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="DELETE 5")
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await delete_session("my-session-id")

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args.args
        assert "my-session-id" in call_args

    @pytest.mark.asyncio
    async def test_delete_does_not_raise_on_empty_result(self) -> None:
        """Should not raise even when no rows were deleted."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="DELETE 0")
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.rag.vector_store.get_pool", new=AsyncMock(return_value=mock_pool)
        ):
            await delete_session("non-existent-session")  # should not raise


# ---------------------------------------------------------------------------
# _filter_prescription_chunks — pure function
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# _parse_json_safe — pure function
# ---------------------------------------------------------------------------


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

    def test_normalises_quoted_null_string(self) -> None:
        r"""Should convert "null" string values to proper JSON null."""
        raw = '{"medication_name": "Amoxicillin", "dosage": "null"}'
        result = _parse_json_safe(raw)
        assert result["dosage"] is None

    def test_normalises_none_specified_string(self) -> None:
        r"""Should convert "None Specified" to proper JSON null."""
        raw = '{"medication_name": "Ibuprofen", "duration": "None Specified"}'
        result = _parse_json_safe(raw)
        assert result["duration"] is None

    def test_normalises_not_stated_string(self) -> None:
        r"""Should convert "Not Stated" to proper JSON null."""
        raw = '{"medication_name": "Paracetamol", "frequency": "Not Stated"}'
        result = _parse_json_safe(raw)
        assert result["frequency"] is None

    def test_normalises_na_string(self) -> None:
        r"""Should convert "N/A" to proper JSON null."""
        raw = '{"medication_name": "Aspirin", "dosage": "N/A"}'
        result = _parse_json_safe(raw)
        assert result["dosage"] is None

    def test_strips_plain_backtick_fence(self) -> None:
        """Should handle plain ``` fences without 'json' language tag."""
        raw = '```\n{"medication_name": "Ibuprofen"}\n```'
        result = _parse_json_safe(raw)
        assert result["medication_name"] == "Ibuprofen"

    def test_normalises_none_string_to_null(self) -> None:
        """Should convert bare "None" string values to proper JSON null."""
        raw = '{"medication_name": "Metoprolol", "notes": "None"}'
        result = _parse_json_safe(raw)
        assert result["notes"] is None

    def test_normalises_not_mentioned_string(self) -> None:
        """Should convert "Not Mentioned" to proper JSON null."""
        raw = '{"medication_name": "Aspirin", "duration": "Not Mentioned"}'
        result = _parse_json_safe(raw)
        assert result["duration"] is None

    def test_repairs_truncated_json_missing_closing_brace(self) -> None:
        """Should recover from a truncated JSON object missing the closing brace."""
        raw = (
            '{"medication_name": "Metoprolol", "dosage": "25mg",'
            ' "frequency": "once daily", "duration": "four weeks",'
            ' "notes": null'
        )
        result = _parse_json_safe(raw)
        assert result["medication_name"] == "Metoprolol"
        assert result["dosage"] == "25mg"
        assert result["notes"] is None

    def test_repairs_truncated_json_with_multiple_missing_braces(self) -> None:
        """Should close multiple missing braces for deeply truncated output."""
        raw = '{"medication_name": "Aspirin", "nested": {"key": "value"'
        result = _parse_json_safe(raw)
        assert result["medication_name"] == "Aspirin"

    def test_returns_error_dict_when_repair_still_fails(self) -> None:
        """Should return error dict when JSON cannot be repaired."""
        raw = "This is not JSON at all, no braces."
        result = _parse_json_safe(raw)
        assert "error" in result
        assert result["raw"] == raw

    def test_returns_error_dict_when_brace_repair_produces_invalid_json(self) -> None:
        """Should return error dict when brace repair also yields invalid JSON."""
        # Has an open brace so brace_depth > 0, but the content is unparseable
        raw = '{"key": broken content {'
        result = _parse_json_safe(raw)
        assert "error" in result
        assert result["raw"] == raw
