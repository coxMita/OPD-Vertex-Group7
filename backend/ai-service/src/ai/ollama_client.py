"""Ollama HTTP client for local LLM inference and embeddings."""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))


async def generate(prompt: str, temperature: float = 0.0) -> str:
    """Send a prompt to Ollama and return the generated text.

    Args:
        prompt: The full prompt string to send to the model.
        temperature: Sampling temperature (0.0 = deterministic).

    Returns:
        The model's response text.

    Raises:
        RuntimeError: If the Ollama request fails.

    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    logger.info("Sending prompt to Ollama model '%s'...", OLLAMA_MODEL)
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result: str = data["response"]
            logger.info("Ollama response received (%d chars).", len(result))
            return result
    except httpx.HTTPError as exc:
        logger.exception("Ollama HTTP error: %s", exc)
        raise RuntimeError(f"Ollama request failed: {exc}") from exc


async def embed(text: str) -> list[float]:
    """Generate an embedding vector for a single text string.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        RuntimeError: If the Ollama embed request fails.

    """
    vectors = await embed_batch([text])
    return vectors[0]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for a list of texts in a single HTTP request.

    Sending all texts at once is significantly faster than calling embed()
    in a loop or with asyncio.gather — Ollama processes them sequentially
    internally but the round-trip overhead occurs only once.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors in the same order as the input texts.

    Raises:
        RuntimeError: If the Ollama embed request fails.

    """
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {"model": OLLAMA_EMBED_MODEL, "input": texts}
    logger.info(
        "Generating embeddings for %d texts with model '%s'...",
        len(texts),
        OLLAMA_EMBED_MODEL,
    )
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            vectors: list[list[float]] = data["embeddings"]
            logger.info(
                "Embeddings generated: %d vectors (%d dims each).",
                len(vectors),
                len(vectors[0]) if vectors else 0,
            )
            return vectors
    except httpx.HTTPError as exc:
        logger.exception("Ollama embed error: %s", exc)
        raise RuntimeError(f"Ollama embed request failed: {exc}") from exc
