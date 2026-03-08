"""Ollama HTTP client for local LLM inference and embeddings."""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))


async def generate(prompt: str) -> str:
    """Send a prompt to Ollama and return the generated text.

    Args:
        prompt: The full prompt string to send to the model.

    Returns:
        The model's response text.

    Raises:
        RuntimeError: If the Ollama request fails.

    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
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
    """Generate an embedding vector for the given text using nomic-embed-text.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        RuntimeError: If the Ollama embed request fails.

    """
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {"model": OLLAMA_EMBED_MODEL, "input": text}
    logger.info("Generating embedding with model '%s'...", OLLAMA_EMBED_MODEL)
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            vector: list[float] = data["embeddings"][0]
            logger.info("Embedding generated (%d dims).", len(vector))
            return vector
    except httpx.HTTPError as exc:
        logger.exception("Ollama embed error: %s", exc)
        raise RuntimeError(f"Ollama embed request failed: {exc}") from exc
