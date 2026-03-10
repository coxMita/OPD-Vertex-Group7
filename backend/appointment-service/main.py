"""Entry point for appointment-service."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlmodel import Session, create_engine

import src.logger_config  # noqa: F401, I001
from src.api.routes.appointment_routes import router as appointment_router
from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import (
    APPOINTMENT_CREATED,
    APPOINTMENT_SESSION_STARTED,
    APPOINTMENT_STATUS_CHANGED,
)
from src.messaging.pubsub_facade import PubSubFacade
from src.repositories.appointment_repository import AppointmentRepository
from src.scheduling.appointment_scheduler import build_scheduler

logger = logging.getLogger(__name__)

load_dotenv()

AMQP_URL = os.getenv("AMQP_URL")
if not AMQP_URL:
    logger.error("AMQP_URL not set in environment variables")
    raise ValueError("AMQP_URL not set in environment variables")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not set in environment variables")
    raise ValueError("DATABASE_URL not set in environment variables")

messaging_manager.add_pubsubs(
    [
        PubSubFacade(AMQP_URL, APPOINTMENT_CREATED),
        PubSubFacade(AMQP_URL, APPOINTMENT_STATUS_CHANGED),
        PubSubFacade(AMQP_URL, APPOINTMENT_SESSION_STARTED),
    ]
)

_engine = create_engine(DATABASE_URL)


def _get_repo() -> AppointmentRepository:
    """Create a fresh AppointmentRepository with its own Session.

    Returns:
        AppointmentRepository: A new repository instance.

    """
    return AppointmentRepository(Session(_engine))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """Lifespan context manager to handle startup and shutdown events.

    Args:
        _: The FastAPI app instance.

    Returns:
        AsyncGenerator[None, Any]: An async generator for lifespan management.

    """
    logger.info("Starting up messaging manager...")
    await messaging_manager.start_all()
    logger.info("Messaging manager started.")

    scheduler = build_scheduler(_get_repo, messaging_manager)
    scheduler.start()
    logger.info("Scheduler started. Jobs: %s", scheduler.get_jobs())

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped.")
    await messaging_manager.stop_all()
    logger.info("Messaging manager stopped.")


app = FastAPI(title="appointment-service", lifespan=lifespan)
app.include_router(appointment_router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "appointment-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
