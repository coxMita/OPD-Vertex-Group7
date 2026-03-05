"""pgvector store for temporary per-session transcript chunk embeddings."""

import logging
import os
import uuid

import asyncpg

logger = logging.getLogger(__name__)

AI_DB_URL = os.getenv(
    "AI_DB_URL",
    "postgresql://ai_user:ai_pass@ai-db:5432/ai_db",
)

# nomic-embed-text produces 768-dimensional vectors
EMBEDDING_DIM = 768


async def init_db() -> None:
    """Create the pgvector extension and transcript_chunks table."""
    conn = await asyncpg.connect(AI_DB_URL)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS transcript_chunks (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id  UUID NOT NULL,
                chunk       TEXT NOT NULL,
                embedding   vector({EMBEDDING_DIM}) NOT NULL,
                created_at  TIMESTAMPTZ DEFAULT now()
            );
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS transcript_chunks_session_idx
            ON transcript_chunks (session_id);
        """)
        logger.info("pgvector table initialised.")
    finally:
        await conn.close()


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    """Split text into overlapping word-based chunks.

    Args:
        text: The full transcript text to split.
        chunk_size: Number of words per chunk.
        overlap: Number of words to overlap between consecutive chunks.

    Returns:
        List of text chunk strings.

    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break

    logger.info("Split transcript (%d words) into %d chunks.", len(words), len(chunks))
    return chunks


async def store_chunks(
    session_id: str,
    chunks: list[str],
    vectors: list[list[float]],
) -> None:
    """Insert all chunks and their embeddings for a session.

    Args:
        session_id: UUID string identifying this transcript processing session.
        chunks: List of text chunk strings.
        vectors: List of embedding vectors, one per chunk.

    """
    conn = await asyncpg.connect(AI_DB_URL)
    try:
        rows = [
            (
                str(uuid.uuid4()),
                session_id,
                chunk,
                "[" + ",".join(str(v) for v in vector) + "]",
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        await conn.executemany(
            """
            INSERT INTO transcript_chunks (id, session_id, chunk, embedding)
            VALUES ($1, $2, $3, $4::vector)
            """,
            rows,
        )
        logger.info("Stored %d chunks for session %s.", len(rows), session_id)
    finally:
        await conn.close()


async def retrieve_relevant_chunks(
    session_id: str,
    query_vector: list[float],
    top_k: int = 5,
) -> list[str]:
    """Retrieve the most relevant chunks for a query within a session.

    Args:
        session_id: UUID string scoping the search to one transcript.
        query_vector: The query embedding vector.
        top_k: Number of chunks to return.

    Returns:
        List of chunk strings ordered by relevance (closest first).

    """
    conn = await asyncpg.connect(AI_DB_URL)
    try:
        vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"
        rows = await conn.fetch(
            """
            SELECT chunk
            FROM transcript_chunks
            WHERE session_id = $1
            ORDER BY embedding <=> $2::vector
            LIMIT $3
            """,
            session_id,
            vector_str,
            top_k,
        )
        results = [row["chunk"] for row in rows]
        logger.info(
            "Retrieved %d relevant chunks for session %s.", len(results), session_id
        )
        return results
    finally:
        await conn.close()


async def delete_session(session_id: str) -> None:
    """Delete all chunks belonging to a session after processing is complete.

    Args:
        session_id: UUID string of the session to clean up.

    """
    conn = await asyncpg.connect(AI_DB_URL)
    try:
        result = await conn.execute(
            "DELETE FROM transcript_chunks WHERE session_id = $1",
            session_id,
        )
        logger.info("Deleted session %s — %s.", session_id, result)
    finally:
        await conn.close()
