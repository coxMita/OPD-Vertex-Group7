"""Core AI processing logic: runs summary and prescription generation."""

import json
import logging

from src.ai.ollama_client import generate
from src.ai.prompts import PRESCRIPTION_PROMPT_TEMPLATE, SUMMARY_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


async def process_transcript(transcript: str) -> dict[str, object]:
    """Run both AI passes on a transcript and return structured results.

    Performs two sequential Ollama inference calls:
    1. Clinical summary (free-text).
    2. Prescription extraction (structured JSON).

    Args:
        transcript: The raw transcription text.

    Returns:
        A dict with keys ``summary`` (str) and ``prescription`` (dict).

    """
    logger.info("Running AI pass 1: clinical summary...")
    summary = await generate(SUMMARY_PROMPT_TEMPLATE.format(transcript=transcript))

    logger.info("Running AI pass 2: prescription extraction...")
    raw_prescription = await generate(
        PRESCRIPTION_PROMPT_TEMPLATE.format(transcript=transcript)
    )

    prescription: dict[str, object] = _parse_json_safe(raw_prescription)

    return {"summary": summary.strip(), "prescription": prescription}


def _parse_json_safe(raw: str) -> dict[str, object]:
    """Attempt to parse JSON from model output; return error dict on failure.

    Args:
        raw: Raw string output from the model.

    Returns:
        Parsed dict or a fallback error dict.

    """
    # Strip markdown code fences if the model wraps output in ```json ... ```
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()

    try:
        result: dict[str, object] = json.loads(cleaned)
        return result
    except json.JSONDecodeError:
        logger.warning("Could not parse prescription JSON from model output.")
        return {"error": "Could not parse JSON", "raw": raw}
