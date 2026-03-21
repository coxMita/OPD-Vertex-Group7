"""Entry point for consultation-service."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlmodel import Session

import src.logger_config  # noqa: F401, I001
from src.api.dependencies import engine
from src.api.routes.consultation_routes import router as consultation_router
from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import (
    APPOINTMENT_SESSION_STARTED,
    CONSULTATION_COMPLETED,
    CONSULTATION_CREATED,
    CONSULTATION_STARTED,
)
from src.messaging.pubsub_facade import PubSubFacade
from src.messaging.session_started_handler import handle_session_started
from src.models.msg.session_started_message import SessionStartedMessage

logger = logging.getLogger(__name__)

load_dotenv()


def _is_truthy(value: str | None) -> bool:
    """Interpret common truthy environment variable values."""
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


AMQP_URL = os.getenv("AMQP_URL")
MESSAGING_REQUIRED = _is_truthy(os.getenv("MESSAGING_REQUIRED"))
MESSAGING_ENABLED = bool(AMQP_URL)
SESSION_STARTED_QUEUE_NAME = os.getenv(
    "SESSION_STARTED_QUEUE_NAME",
    "consultation.session_started.queue",
)


def _get_session() -> Session:
    """Create a database session for background messaging handlers."""
    return Session(engine)


if MESSAGING_ENABLED:
    messaging_manager.add_pubsubs(
        [
            PubSubFacade(AMQP_URL, CONSULTATION_CREATED),
            PubSubFacade(AMQP_URL, CONSULTATION_STARTED),
            PubSubFacade(AMQP_URL, CONSULTATION_COMPLETED),
            PubSubFacade(AMQP_URL, APPOINTMENT_SESSION_STARTED),
        ]
    )
else:
    logger.warning("AMQP_URL not set; consultation messaging is disabled.")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """Lifespan context manager to handle stratup and shutdown events.

    Args:
        _: The FastAPI app instance.

    Returns:
        AsyncGenerator[None, Any]: An async generator for lifespan management.

    """
    messaging_started = False
    if MESSAGING_ENABLED:
        logger.info("Starting up messaging manager...")
        try:
            await messaging_manager.start_all()

            messaging_manager.get_pubsub(APPOINTMENT_SESSION_STARTED).subscribe(
                queue_name=SESSION_STARTED_QUEUE_NAME,
                on_message=lambda event: handle_session_started(
                    event,
                    get_session=_get_session,
                    messaging_manager=messaging_manager,
                ),
                message_class=SessionStartedMessage,
            )

            messaging_started = True
            logger.info("Messaging manager started.")
        except Exception:
            if MESSAGING_REQUIRED:
                logger.exception("Messaging startup failed and is required.")
                raise
            logger.exception("Messaging startup failed; continuing without messaging.")
    else:
        logger.info("Skipping messaging startup because messaging is disabled.")
    yield
    if messaging_started:
        logger.info("Shutting down messaging manager...")
        await messaging_manager.stop_all()
        logger.info("Messaging manager stopped.")


app = FastAPI(title="consultation-service", lifespan=lifespan)
app.include_router(consultation_router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "consultation-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
