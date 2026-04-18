"""Entry point for email-service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.email_routes import router as email_router
from src.config import settings
from src.messaging.email_queue_facade import EmailQueueFacade
from src.messaging.messaging_manager import messaging_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start RabbitMQ consumer on startup; close on shutdown."""
    messaging_manager.add_email_queue(
        EmailQueueFacade(settings.RABBITMQ_URL, settings.EMAIL_QUEUE_NAME)
    )
    try:
        logger.info("Starting up messaging manager...")
        await messaging_manager.start_all()
        logger.info("Messaging manager started.")
        app.state.rabbitmq_connection = messaging_manager.rabbitmq_connection
        yield
    finally:
        logger.info("Shutting down messaging manager...")
        await messaging_manager.stop_all()
        logger.info("Messaging manager shut down.")


app = FastAPI(title="email-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(email_router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "email-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
