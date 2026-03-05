"""Core AI processing logic: chunk → embed → retrieve → generate → cleanup."""

import asyncio
import json
import logging
import uuid

from src.ai.ollama_client import embed, generate
from src.ai.prompts import (
    PRESCRIPTION_PROMPT_TEMPLATE,
    SUMMARY_PROMPT_TEMPLATE,
)
from src.rag.vector_store import (
    chunk_text,
    delete_session,
    retrieve_relevant_chunks,
    store_chunks,
)

logger = logging.getLogger(__name__)

# Queries used to retrieve relevant chunks for each AI pass
SUMMARY_QUERY = "chief complaint key clinical findings diagnosis treatment decisions"
PRESCRIPTION_QUERY = "medication prescribed dosage frequency duration instructions"


async def process_transcript(transcript: str) -> dict[str, object]:
    """Run the full RAG pipeline on a (potentially very long) transcript.

    Steps:
    1. Split transcript into overlapping word chunks.
    2. Embed all chunks concurrently with nomic-embed-text.
    3. Store chunks in pgvector under a unique session_id.
    4. Retrieve top-5 relevant chunks per AI pass using targeted queries.
    5. Generate clinical summary from summary-relevant chunks.
    6. Generate prescription JSON from prescription-relevant chunks.
    7. Delete all session chunks from pgvector (clean up).

    Args:
        transcript: The raw transcription text (can be very long).

    Returns:
        A dict with keys ``summary`` (str) and ``prescription`` (dict).

    """
    session_id = str(uuid.uuid4())
    logger.info("Starting RAG session %s", session_id)

    # ── Step 1: Chunk ──────────────────────────────────────────────────────
    chunks = chunk_text(transcript, chunk_size=200, overlap=30)
    if not chunks:
        chunks = [transcript]

    # ── Step 2: Embed all chunks concurrently ──────────────────────────────
    logger.info("Embedding %d chunks...", len(chunks))
    vectors = await asyncio.gather(*[embed(chunk) for chunk in chunks])

    # ── Step 3: Store in pgvector ──────────────────────────────────────────
    await store_chunks(session_id, chunks, list(vectors))

    try:
        # ── Step 4a: Retrieve chunks relevant to summary ───────────────────
        summary_query_vec = await embed(SUMMARY_QUERY)
        summary_chunks = await retrieve_relevant_chunks(
            session_id, summary_query_vec, top_k=5
        )
        summary_context = "\n\n".join(summary_chunks)

        # ── Step 4b: Retrieve chunks relevant to prescription ──────────────
        prescription_query_vec = await embed(PRESCRIPTION_QUERY)
        prescription_chunks = await retrieve_relevant_chunks(
            session_id, prescription_query_vec, top_k=5
        )
        prescription_context = "\n\n".join(prescription_chunks)

        # ── Step 5: Generate clinical summary ─────────────────────────────
        logger.info("Running AI pass 1: clinical summary...")
        summary = await generate(
            SUMMARY_PROMPT_TEMPLATE.format(transcript=summary_context)
        )

        # ── Step 6: Generate prescription JSON ────────────────────────────
        logger.info("Running AI pass 2: prescription extraction...")
        raw_prescription = await generate(
            PRESCRIPTION_PROMPT_TEMPLATE.format(transcript=prescription_context)
        )
        prescription = _parse_json_safe(raw_prescription)

    finally:
        # ── Step 7: Always clean up session chunks ─────────────────────────
        logger.info("Cleaning up session %s from pgvector...", session_id)
        await delete_session(session_id)
        logger.info("Session %s cleaned up.", session_id)

    return {"summary": summary.strip(), "prescription": prescription}


def _parse_json_safe(raw: str) -> dict[str, object]:
    """Attempt to parse JSON from model output; return error dict on failure.

    Args:
        raw: Raw string output from the model.

    Returns:
        Parsed dict or a fallback error dict.

    """
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
