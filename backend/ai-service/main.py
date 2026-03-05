"""Entry point for ai-service."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI

from src.ai.router import router
from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import TRANSCRIPTION_COMPLETED
from src.messaging.pubsub_facade import PubSubFacade
from src.messaging.subscriber import on_transcript_message

logger = logging.getLogger(__name__)

load_dotenv()

AMQP_URL = os.getenv("AMQP_URL")
if not AMQP_URL:
    logger.error("AMQP_URL is not set.")
    raise ValueError("AMQP_URL is not set.")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """Manage application startup and shutdown lifecycle."""
    pubsub = PubSubFacade(AMQP_URL, TRANSCRIPTION_COMPLETED)
    messaging_manager.add_pubsub(pubsub)

    logger.info("Starting up messaging manager...")
    await messaging_manager.start_all()
    logger.info("Messaging manager started.")

    # Subscribe to transcription.completed events
    pubsub.subscribe(
        queue_name="ai-service.transcription.completed",
        on_message=on_transcript_message,
        message_class=None,  # handled inside subscriber with raw bytes
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
