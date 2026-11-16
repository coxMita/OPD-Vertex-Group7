"""OpenAI-compatible HTTP client for LLM inference and embeddings.

Works against any server that speaks the OpenAI API:
  * vLLM on UCloud behind nginx   (LLM_BASE_URL=https://<public-link>/v1)
  * a local Ollama container       (LLM_BASE_URL=http://ollama:11434/v1)
"""

import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://ollama:11434/v1").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "300"))
# Qwen3 "thinks" by default; we want plain answers. Ignored by other models.
LLM_DISABLE_THINKING = os.getenv("LLM_DISABLE_THINKING", "true").lower() == "true"

EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", LLM_BASE_URL).rstrip("/")
EMBED_API_KEY = os.getenv("EMBED_API_KEY", LLM_API_KEY)
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _headers(api_key: str) -> dict[str, str]:
    """Build request headers, adding the Bearer token when one is configured."""
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


async def generate(prompt: str, temperature: float = 0.0) -> str:
    """Send a prompt to the chat model and return the generated text.

    Args:
        prompt: The full prompt string to send to the model.
        temperature: Sampling temperature (0.0 = deterministic).

    Returns:
        The model's response text.

    Raises:
        RuntimeError: If the LLM request fails.

    """
    url = f"{LLM_BASE_URL}/chat/completions"
    payload: dict = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "stream": False,
    }
    if LLM_DISABLE_THINKING:
        payload["chat_template_kwargs"] = {"enable_thinking": False}

    logger.info("Sending prompt to LLM model '%s'...", LLM_MODEL)
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            response = await client.post(
                url, json=payload, headers=_headers(LLM_API_KEY)
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"] or ""
            result: str = _THINK_RE.sub("", content).strip()
            logger.info("LLM response received (%d chars).", len(result))
            return result
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        logger.exception("LLM request error: %s", exc)
        raise RuntimeError(f"LLM request failed: {exc}") from exc


async def embed(text: str) -> list[float]:
    """Generate an embedding vector for a single text string.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        RuntimeError: If the embed request fails.

    """
    vectors = await embed_batch([text])
    return vectors[0]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for a list of texts in a single HTTP request.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors in the same order as the input texts.

    Raises:
        RuntimeError: If the embed request fails.

    """
    url = f"{EMBED_BASE_URL}/embeddings"
    payload = {"model": EMBED_MODEL, "input": texts}
    logger.info(
        "Generating embeddings for %d texts with model '%s'...",
        len(texts),
        EMBED_MODEL,
    )
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            response = await client.post(
                url, json=payload, headers=_headers(EMBED_API_KEY)
            )
            response.raise_for_status()
            items = sorted(response.json()["data"], key=lambda d: d["index"])
            vectors: list[list[float]] = [item["embedding"] for item in items]
            logger.info(
                "Embeddings generated: %d vectors (%d dims each).",
                len(vectors),
                len(vectors[0]) if vectors else 0,
            )
            return vectors
    except (httpx.HTTPError, KeyError) as exc:
        logger.exception("Embed request error: %s", exc)
        raise RuntimeError(f"Embed request failed: {exc}") from exc


async def check_connection() -> None:
    """Log whether the LLM endpoint is reachable (never raises)."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{LLM_BASE_URL}/models", headers=_headers(LLM_API_KEY)
            )
            resp.raise_for_status()
            ids = [m.get("id") for m in resp.json().get("data", [])]
            logger.info("LLM endpoint %s reachable, models: %s", LLM_BASE_URL, ids)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("LLM endpoint %s NOT reachable: %s", LLM_BASE_URL, exc)
