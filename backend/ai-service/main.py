"""Entry point for ai-service."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI

from src.ai.router import router
from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import TRANSCRIPTION_COMPLETED
from src.messaging.pubsub_facade import PubSubFacade
from src.messaging.subscriber import on_transcript_message
from src.rag.vector_store import init_db

logger = logging.getLogger(__name__)

load_dotenv()

AMQP_URL = os.getenv("AMQP_URL")
if not AMQP_URL:
    logger.error("AMQP_URL is not set.")
    raise ValueError("AMQP_URL is not set.")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


async def _ensure_embed_model_pulled() -> None:
    """Pull nomic-embed-text if not already present in Ollama."""
    logger.info("Checking if '%s' is available in Ollama...", OLLAMA_EMBED_MODEL)
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            if any(OLLAMA_EMBED_MODEL in m for m in models):
                logger.info("'%s' already present.", OLLAMA_EMBED_MODEL)
                return
            logger.info("Pulling '%s' from Ollama...", OLLAMA_EMBED_MODEL)
            pull_resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": OLLAMA_EMBED_MODEL, "stream": False},
                timeout=300,
            )
            pull_resp.raise_for_status()
            logger.info("'%s' pulled successfully.", OLLAMA_EMBED_MODEL)
    except httpx.HTTPError as exc:
        logger.warning("Could not pull embed model: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """Manage application startup and shutdown lifecycle."""
    # 1. Init pgvector table
    logger.info("Initialising pgvector database...")
    await init_db()
    logger.info("pgvector database ready.")

    # 2. Ensure nomic-embed-text is available
    await _ensure_embed_model_pulled()

    # 3. Start RabbitMQ messaging
    pubsub = PubSubFacade(AMQP_URL, TRANSCRIPTION_COMPLETED)
    messaging_manager.add_pubsub(pubsub)

    logger.info("Starting up messaging manager...")
    await messaging_manager.start_all()
    logger.info("Messaging manager started.")

    pubsub.subscribe(
        queue_name="ai-service.transcription.completed",
        on_message=on_transcript_message,
        message_class=None,
    )
    logger.info("Subscribed to '%s'.", TRANSCRIPTION_COMPLETED)

    yield

    logger.info("Shutting down messaging manager...")
    await messaging_manager.stop_all()
    logger.info("Messaging manager shut down.")


app = FastAPI(title="ai-service", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "ai-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
