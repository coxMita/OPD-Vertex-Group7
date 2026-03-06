"""Unit tests for src.ai.ollama_client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.ai.ollama_client import embed, generate

_EMBEDDING_DIM = 768


class TestGenerate:
    """Unit tests for the generate() function."""

    @pytest.mark.asyncio
    async def test_generate_returns_response_text(self) -> None:
        """Should return the 'response' field from Ollama's JSON payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Clinical summary here."}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("src.ai.ollama_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            result = await generate("Some transcript")

        assert result == "Clinical summary here."

    @pytest.mark.asyncio
    async def test_generate_sends_correct_payload(self) -> None:
        """Should send model name, prompt, and stream=False to Ollama."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "ok"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("src.ai.ollama_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            await generate("test prompt")

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["prompt"] == "test prompt"
        assert payload["stream"] is False
        assert "model" in payload

    @pytest.mark.asyncio
    async def test_generate_raises_runtime_error_on_http_error(self) -> None:
        """Should raise RuntimeError when Ollama returns an HTTP error."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPError("connection refused")

        with patch("src.ai.ollama_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            with pytest.raises(RuntimeError, match="Ollama request failed"):
                await generate("test prompt")

    @pytest.mark.asyncio
    async def test_generate_raises_on_500(self) -> None:
        """Should raise RuntimeError when Ollama returns a 500 status."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("src.ai.ollama_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            with pytest.raises(RuntimeError, match="Ollama request failed"):
                await generate("test prompt")


class TestEmbed:
    """Unit tests for the embed() function."""

    @pytest.mark.asyncio
    async def test_embed_returns_vector(self) -> None:
        """Should return the first embedding vector from Ollama's response."""
        fake_vector = [0.1, 0.2, 0.3] * 256  # 768 floats
        mock_response = MagicMock()
        mock_response.json.return_value = {"embeddings": [fake_vector]}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("src.ai.ollama_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            result = await embed("some text")

        assert result == fake_vector
        assert len(result) == _EMBEDDING_DIM

    @pytest.mark.asyncio
    async def test_embed_sends_correct_payload(self) -> None:
        """Should send model name and input text to /api/embed endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"embeddings": [[0.1] * _EMBEDDING_DIM]}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("src.ai.ollama_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            await embed("patient has fever")

        call_kwargs = mock_client.post.call_args
        assert "/api/embed" in call_kwargs.args[0]
        payload = call_kwargs.kwargs["json"]
        assert payload["input"] == "patient has fever"
        assert "model" in payload

    @pytest.mark.asyncio
    async def test_embed_raises_runtime_error_on_http_error(self) -> None:
        """Should raise RuntimeError when the embed request fails."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPError("timeout")

        with patch("src.ai.ollama_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            with pytest.raises(RuntimeError, match="Ollama embed request failed"):
                await embed("some text")
