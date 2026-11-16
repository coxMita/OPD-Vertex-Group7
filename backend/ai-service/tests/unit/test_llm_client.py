"""Unit tests for src.ai.llm_client (OpenAI-compatible API)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.ai import llm_client
from src.ai.llm_client import check_connection, embed, embed_batch, generate

_EMBEDDING_DIM = 768
_CLIENT = "src.ai.llm_client.httpx.AsyncClient"


def _chat_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    resp.raise_for_status = MagicMock()
    return resp


def _embed_response(vectors: list[list[float]]) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "data": [{"index": i, "embedding": v} for i, v in enumerate(vectors)]
    }
    resp.raise_for_status = MagicMock()
    return resp


def _patched(mock_client: AsyncMock):  # noqa: ANN202
    ctx = patch(_CLIENT)
    mock_cls = ctx.start()
    mock_cls.return_value.__aenter__.return_value = mock_client
    return ctx


class TestGenerate:
    """Unit tests for generate()."""

    @pytest.mark.asyncio
    async def test_returns_message_content(self) -> None:
        """Should return choices[0].message.content."""
        client = AsyncMock()
        client.post.return_value = _chat_response("Clinical summary here.")
        ctx = _patched(client)
        try:
            result = await generate("Some transcript")
        finally:
            ctx.stop()
        assert result == "Clinical summary here."

    @pytest.mark.asyncio
    async def test_strips_think_block(self) -> None:
        """<think>...</think> reasoning blocks are removed from the answer."""
        client = AsyncMock()
        client.post.return_value = _chat_response("<think>\nhmm\n</think>\n\nAnswer")
        ctx = _patched(client)
        try:
            result = await generate("x")
        finally:
            ctx.stop()
        assert result == "Answer"

    @pytest.mark.asyncio
    async def test_sends_chat_completions_payload(self) -> None:
        """Should POST model + user message to /chat/completions."""
        client = AsyncMock()
        client.post.return_value = _chat_response("ok")
        ctx = _patched(client)
        try:
            await generate("test prompt")
        finally:
            ctx.stop()
        call = client.post.call_args
        assert call.args[0].endswith("/chat/completions")
        payload = call.kwargs["json"]
        assert payload["messages"] == [{"role": "user", "content": "test prompt"}]
        assert payload["stream"] is False
        assert payload["model"] == llm_client.LLM_MODEL

    @pytest.mark.asyncio
    async def test_temperature_default_and_custom(self) -> None:
        """Temperature defaults to 0.0 and custom values are forwarded."""
        client = AsyncMock()
        client.post.return_value = _chat_response("ok")
        ctx = _patched(client)
        try:
            await generate("a")
            assert client.post.call_args.kwargs["json"]["temperature"] == 0.0
            await generate("a", temperature=0.7)
            assert client.post.call_args.kwargs["json"]["temperature"] == 0.7  # noqa: PLR2004
        finally:
            ctx.stop()

    @pytest.mark.asyncio
    async def test_sends_bearer_token_when_configured(self) -> None:
        """Authorization header carries the API key."""
        client = AsyncMock()
        client.post.return_value = _chat_response("ok")
        ctx = _patched(client)
        try:
            with patch.object(llm_client, "LLM_API_KEY", "secret"):
                await generate("a")
        finally:
            ctx.stop()
        headers = client.post.call_args.kwargs["headers"]
        assert headers == {"Authorization": "Bearer secret"}

    @pytest.mark.asyncio
    async def test_no_auth_header_without_key(self) -> None:
        """No Authorization header when no key is set (local Ollama)."""
        client = AsyncMock()
        client.post.return_value = _chat_response("ok")
        ctx = _patched(client)
        try:
            with patch.object(llm_client, "LLM_API_KEY", ""):
                await generate("a")
        finally:
            ctx.stop()
        assert client.post.call_args.kwargs["headers"] == {}

    @pytest.mark.asyncio
    async def test_disable_thinking_flag(self) -> None:
        """chat_template_kwargs is sent only when thinking is disabled."""
        client = AsyncMock()
        client.post.return_value = _chat_response("ok")
        ctx = _patched(client)
        try:
            with patch.object(llm_client, "LLM_DISABLE_THINKING", True):
                await generate("a")
            assert client.post.call_args.kwargs["json"]["chat_template_kwargs"] == {
                "enable_thinking": False
            }
            with patch.object(llm_client, "LLM_DISABLE_THINKING", False):
                await generate("a")
            assert "chat_template_kwargs" not in client.post.call_args.kwargs["json"]
        finally:
            ctx.stop()

    @pytest.mark.asyncio
    async def test_raises_runtime_error_on_http_error(self) -> None:
        """Connection errors become RuntimeError."""
        client = AsyncMock()
        client.post.side_effect = httpx.HTTPError("connection refused")
        ctx = _patched(client)
        try:
            with pytest.raises(RuntimeError, match="LLM request failed"):
                await generate("test prompt")
        finally:
            ctx.stop()

    @pytest.mark.asyncio
    async def test_raises_on_401(self) -> None:
        """A wrong token (401 from nginx) becomes RuntimeError."""
        resp = MagicMock()
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock()
        )
        client = AsyncMock()
        client.post.return_value = resp
        ctx = _patched(client)
        try:
            with pytest.raises(RuntimeError, match="LLM request failed"):
                await generate("test prompt")
        finally:
            ctx.stop()

    @pytest.mark.asyncio
    async def test_raises_on_malformed_response(self) -> None:
        """A response without choices becomes RuntimeError."""
        resp = MagicMock()
        resp.json.return_value = {"error": "boom"}
        resp.raise_for_status = MagicMock()
        client = AsyncMock()
        client.post.return_value = resp
        ctx = _patched(client)
        try:
            with pytest.raises(RuntimeError, match="LLM request failed"):
                await generate("x")
        finally:
            ctx.stop()


class TestEmbedBatch:
    """Unit tests for embed() / embed_batch()."""

    @pytest.mark.asyncio
    async def test_embed_returns_vector(self) -> None:
        """embed() returns the single vector."""
        vec = [0.1] * _EMBEDDING_DIM
        client = AsyncMock()
        client.post.return_value = _embed_response([vec])
        ctx = _patched(client)
        try:
            result = await embed("some text")
        finally:
            ctx.stop()
        assert result == vec
        assert client.post.call_args.kwargs["json"]["input"] == ["some text"]

    @pytest.mark.asyncio
    async def test_batch_single_request_to_embeddings(self) -> None:
        """All texts go in one POST to /embeddings."""
        texts = ["one", "two", "three"]
        vecs = [[float(i)] * _EMBEDDING_DIM for i in range(3)]
        client = AsyncMock()
        client.post.return_value = _embed_response(vecs)
        ctx = _patched(client)
        try:
            result = await embed_batch(texts)
        finally:
            ctx.stop()
        assert client.post.call_count == 1
        assert client.post.call_args.args[0].endswith("/embeddings")
        assert client.post.call_args.kwargs["json"]["input"] == texts
        assert result == vecs

    @pytest.mark.asyncio
    async def test_batch_orders_by_index(self) -> None:
        """Vectors are returned in input order even if the server reorders."""
        resp = MagicMock()
        resp.json.return_value = {
            "data": [
                {"index": 1, "embedding": [2.0]},
                {"index": 0, "embedding": [1.0]},
            ]
        }
        resp.raise_for_status = MagicMock()
        client = AsyncMock()
        client.post.return_value = resp
        ctx = _patched(client)
        try:
            result = await embed_batch(["a", "b"])
        finally:
            ctx.stop()
        assert result == [[1.0], [2.0]]

    @pytest.mark.asyncio
    async def test_raises_runtime_error_on_http_error(self) -> None:
        """HTTP errors become RuntimeError."""
        client = AsyncMock()
        client.post.side_effect = httpx.HTTPError("connection reset")
        ctx = _patched(client)
        try:
            with pytest.raises(RuntimeError, match="Embed request failed"):
                await embed_batch(["a", "b"])
        finally:
            ctx.stop()


class TestCheckConnection:
    """Unit tests for check_connection()."""

    @pytest.mark.asyncio
    async def test_never_raises_on_error(self) -> None:
        """Unreachable endpoint only logs a warning."""
        client = AsyncMock()
        client.get.side_effect = httpx.HTTPError("down")
        ctx = _patched(client)
        try:
            await check_connection()
        finally:
            ctx.stop()

    @pytest.mark.asyncio
    async def test_queries_models_endpoint(self) -> None:
        """Calls GET /models."""
        resp = MagicMock()
        resp.json.return_value = {"data": [{"id": "opd-llm"}]}
        resp.raise_for_status = MagicMock()
        client = AsyncMock()
        client.get.return_value = resp
        ctx = _patched(client)
        try:
            await check_connection()
        finally:
            ctx.stop()
        assert client.get.call_args.args[0].endswith("/models")
