"""Core AI processing logic: chunk → embed → retrieve → summarise → generate."""

import asyncio
import json
import logging
import re
import uuid

from src.ai.ollama_client import embed, embed_batch, generate
from src.ai.prompts import (
    CHUNK_SUMMARY_PROMPT_TEMPLATE,
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
PRESCRIPTION_QUERY = (
    "prescribe tablet medicine vitamin dosage mg take after breakfast lunch"
)

# Sentinel returned by the chunk summariser when a chunk has no clinical content
_NO_MEDICAL_CONTENT = "NO_MEDICAL_CONTENT"

# Keywords that strongly indicate a prescription moment in the transcript
_PRESCRIPTION_KEYWORDS: frozenset[str] = frozenset(
    {
        "prescribe",
        "prescribed",
        "prescription",
        "medication",
        "medicine",
        "tablet",
        "capsule",
        "pill",
        "mg",
        "dose",
        "dosage",
        "vitamin",
        "antibiotic",
        "anti-inflammatory",
        "paracetamol",
        "amoxicillin",
        "ibuprofen",
        "syrup",
        "drops",
        "injection",
        "take",
        "twice",
        "once",
        "daily",
        "every",
        "morning",
        "night",
        "after breakfast",
        "after lunch",
        "after dinner",
        "before bed",
        "course",
        "days",
        "weeks",
    }
)


def _dynamic_top_k(candidates: list[str]) -> int:
    """Calculate top_k for prescription retrieval based on candidate count.

    Scales based on how many keyword-matched chunks exist, ensuring enough
    context without exceeding the 3b model's quality sweet spot (~2000 tokens).
    Each chunk is ~200 words / ~270 tokens; quality degrades past ~8 chunks
    for 3b. Bump the caps when switching to llama3.1:8b (safe up to ~12-15).

    Args:
        candidates: Keyword-filtered prescription candidate chunks.

    Returns:
        top_k value scaled to candidate count, capped for model quality.

    """
    n = len(candidates)
    if n <= 5:  # noqa: PLR2004
        return n  # use all — fits well within quality zone
    if n <= 8:  # noqa: PLR2004
        return n  # still within 3b sweet spot
    if n <= 20:  # noqa: PLR2004
        return 8  # hard quality cap for llama3.2:3b  # noqa: PLR2004
    return 8  # noqa: PLR2004  # cap for very long transcripts


def _filter_prescription_chunks(chunks: list[str]) -> list[str]:
    """Return chunks that contain at least one prescription-related keyword.

    Falls back to all chunks if no keyword matches are found, so the
    pipeline never ends up with an empty context.

    Args:
        chunks: All text chunks from the transcript.

    Returns:
        Filtered list of chunks likely to contain prescription information.

    """
    matched = [
        chunk
        for chunk in chunks
        if any(kw in chunk.lower() for kw in _PRESCRIPTION_KEYWORDS)
    ]
    if not matched:
        logger.info(
            "No prescription keyword matches found; falling back to all %d chunks.",
            len(chunks),
        )
        return chunks

    logger.info(
        "Prescription keyword filter: %d/%d chunks matched.",
        len(matched),
        len(chunks),
    )
    return matched


async def _summarise_chunk(chunk: str) -> str:
    """Summarise a single transcript chunk into 1-2 clinical sentences.

    Used only for the prescription path to isolate drug-specific content.

    Args:
        chunk: A raw transcript chunk (up to 200 words).

    Returns:
        A 1-2 sentence clinical summary, or an empty string if the chunk
        contains no medically relevant content.

    """
    raw = await generate(CHUNK_SUMMARY_PROMPT_TEMPLATE.format(chunk=chunk))
    result = raw.strip()
    if _NO_MEDICAL_CONTENT in result:
        return ""
    return result


async def _hierarchical_summarise(chunks: list[str]) -> list[str]:
    """Summarise all chunks concurrently and filter out empty results.

    Used only for the prescription path.

    Args:
        chunks: List of raw transcript chunks.

    Returns:
        List of non-empty mini-summaries, one per clinically relevant chunk.

    """
    logger.info("Hierarchical summarisation: processing %d chunks...", len(chunks))
    summaries = await asyncio.gather(*[_summarise_chunk(c) for c in chunks])
    filtered = [s for s in summaries if s]
    logger.info(
        "Hierarchical summarisation complete: %d/%d chunks had clinical content.",
        len(filtered),
        len(chunks),
    )
    return filtered


async def process_transcript(transcript: str) -> dict[str, object]:
    """Run the full RAG pipeline on a (potentially very long) transcript.

    Steps:
    1.  Split transcript into overlapping word chunks.
    2.  Embed all chunks concurrently with nomic-embed-text.
    3.  Store chunks in pgvector under a unique session_id.
    4.  Retrieve top-8 relevant chunks for the summary via vector search.
    5.  Feed raw summary chunks directly to the summary LLM pass (no compression).
    6.  Pre-filter ALL chunks by prescription keywords, then vector-rank top-k.
    7.  Hierarchically summarise prescription candidates into mini-summaries.
    8.  Generate clinical summary from raw summary chunks.
    9.  Generate prescription JSON from condensed prescription mini-summaries.
    10. Delete all session chunks from pgvector (clean up).

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

    # ── Step 2: Embed all chunks in a single batch request ────────────────
    # embed_batch sends one HTTP request to Ollama regardless of chunk count,
    # avoiding the overhead of 35+ individual round trips.
    logger.info("Embedding %d chunks in a single batch request...", len(chunks))
    vectors = await embed_batch(chunks)

    # ── Step 3: Store in pgvector ──────────────────────────────────────────
    await store_chunks(session_id, chunks, list(vectors))

    try:
        # ── Step 4: Retrieve chunks relevant to summary ────────────────────
        summary_query_vec = await embed(SUMMARY_QUERY)
        summary_chunks = await retrieve_relevant_chunks(
            session_id,
            summary_query_vec,
            top_k=8,
        )

        # ── Step 5: Use raw chunks directly — no double compression ────────
        # Hierarchical summarisation is skipped here intentionally.
        # The summary prompt works better with full context than pre-digested
        # mini-summaries which lose specificity (vitals, exact diagnoses, etc).
        summary_context = "\n\n".join(summary_chunks)

        # ── Step 6: Prescription — keyword filter → dynamic vector rank ────
        prescription_candidates = _filter_prescription_chunks(chunks)
        top_k_prescription = _dynamic_top_k(prescription_candidates)
        logger.info(
            "Dynamic top_k for prescription: %d (from %d candidates).",
            top_k_prescription,
            len(prescription_candidates),
        )

        if len(prescription_candidates) <= top_k_prescription:
            top_prescription_chunks = prescription_candidates
            logger.info(
                "Using all %d prescription candidate chunks directly.",
                len(prescription_candidates),
            )
        else:
            sub_session_id = str(uuid.uuid4())
            candidate_vectors = await embed_batch(prescription_candidates)
            await store_chunks(
                sub_session_id, prescription_candidates, list(candidate_vectors)
            )
            try:
                prescription_query_vec = await embed(PRESCRIPTION_QUERY)
                top_prescription_chunks = await retrieve_relevant_chunks(
                    sub_session_id,
                    prescription_query_vec,
                    top_k=top_k_prescription,
                )
            finally:
                await delete_session(sub_session_id)

        # ── Step 7: Hierarchically summarise prescription chunks ───────────
        # Only the prescription path uses hierarchical summarisation — it
        # isolates drug sentences from podcast narration noise effectively.
        prescription_mini = await _hierarchical_summarise(top_prescription_chunks)
        prescription_context = "\n\n".join(prescription_mini or top_prescription_chunks)

        # ── Step 8: Generate clinical summary ─────────────────────────────
        logger.info("Running AI pass 1: clinical summary...")
        summary = await generate(
            SUMMARY_PROMPT_TEMPLATE.format(transcript=summary_context)
        )

        # ── Step 9: Generate prescription JSON ────────────────────────────
        logger.info("Running AI pass 2: prescription extraction...")
        raw_prescription = await generate(
            PRESCRIPTION_PROMPT_TEMPLATE.format(transcript=prescription_context)
        )
        prescription = _parse_json_safe(raw_prescription)

    finally:
        # ── Step 10: Always clean up session chunks ────────────────────────
        logger.info("Cleaning up session %s from pgvector...", session_id)
        await delete_session(session_id)
        logger.info("Session %s cleaned up.", session_id)

    return {"summary": summary.strip(), "prescription": prescription}


def _parse_json_safe(raw: str) -> dict[str, object]:
    """Attempt to parse JSON from model output; return error dict on failure.

    Handles markdown fences and fixes common model mistakes of writing
    null-equivalent strings instead of proper JSON null.

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

    # Normalise all null-equivalent string variants to proper JSON null
    cleaned = re.sub(r':\s*"[Nn]ull"', ": null", cleaned)
    cleaned = re.sub(r':\s*"[Nn]one\s*[Ss]pecified"', ": null", cleaned)
    cleaned = re.sub(r':\s*"[Nn]/[Aa]"', ": null", cleaned)
    cleaned = re.sub(r':\s*"[Nn]ot\s*[Ss]tated"', ": null", cleaned)
    cleaned = re.sub(r':\s*"[Nn]ot\s*[Mm]entioned"', ": null", cleaned)

    try:
        result: dict[str, object] = json.loads(cleaned)
        return result
    except json.JSONDecodeError:
        logger.warning("Could not parse prescription JSON from model output.")
        return {"error": "Could not parse JSON", "raw": raw}
