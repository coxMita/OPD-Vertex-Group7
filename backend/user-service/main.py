"""Main application entry point for the User Service.

This sets up the FastAPI application, configures messaging, and includes API routes.
It also defines startup and shutdown procedures for the messaging manager.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI

import src.logger_config  # noqa: F401, I001
from src.api.routes.doctor_routes import router as doctor_router
from src.api.routes.patient_routes import router as patient_router
from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import USER_CREATED
from src.messaging.pubsub_facade import PubSubFacade

logger = logging.getLogger(__name__)

load_dotenv()
AMQP_URL = os.getenv("AMQP_URL")
if not AMQP_URL:
    logger.error("AMQP_URL is not set. Please set it in the environment variables.")
    raise ValueError("AMQP_URL is not set.")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """Manage application startup and shutdown lifecycle."""
    messaging_manager.add_pubsub(PubSubFacade(AMQP_URL, USER_CREATED))

    logger.info("Starting up messaging manager...")
    await messaging_manager.start_all()
    logger.info("Messaging manager started.")
    yield
    logger.info("Shutting down messaging manager...")
    await messaging_manager.stop_all()
    logger.info("Messaging manager shut down.")


app = FastAPI(title="user-service", lifespan=lifespan)
app.include_router(patient_router)
app.include_router(doctor_router)


@app.get("/")
def get_root() -> dict[str, str]:
    """Root endpoint providing basic service information.

    Returns:
        dict: A dictionary with service information.

    """
    return {"service": "User Service"}


@app.get("/health")
def get_health() -> dict[str, str]:
    """Health check endpoint to verify service status.

    Returns:
        dict: A dictionary indicating service health status.

    """
    return {"status": "ok"}
