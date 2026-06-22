"""Entry point for prescription-service."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI

import src.logger_config  # noqa: F401, I001
from src.api.routes.prescription_routes import router as prescription_router
from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import AI_COMPLETED
from src.messaging.pubsub_facade import PubSubFacade
from src.messaging.subscriber import on_ai_completed_message
from src.models.msg.ai_completed_message import AICompletedMessage

logger = logging.getLogger(__name__)

load_dotenv()

AMQP_URL = os.getenv("AMQP_URL")
if not AMQP_URL:
    logger.error("AMQP_URL not set in environment variables")
    raise ValueError("AMQP_URL not set in environment variables")

messaging_manager.add_pubsubs(
    [
        PubSubFacade(AMQP_URL, AI_COMPLETED),
    ]
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """Manage application startup and shutdown lifecycle.

    Args:
        _: The FastAPI app instance.

    Returns:
        AsyncGenerator[None, Any]: An async generator for lifespan management.

    """
    logger.info("Starting up messaging manager...")
    await messaging_manager.start_all()
    logger.info("Messaging manager started.")

    messaging_manager.get_pubsub(AI_COMPLETED).subscribe(
        queue_name="prescription-service.ai.completed",
        on_message=on_ai_completed_message,
        message_class=AICompletedMessage,
    )
    logger.info("Subscribed to '%s'.", AI_COMPLETED)

    yield

    logger.info("Shutting down messaging manager...")
    await messaging_manager.stop_all()
    logger.info("Messaging manager stopped.")


app = FastAPI(title="prescription-service", lifespan=lifespan)
app.include_router(prescription_router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "prescription-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
