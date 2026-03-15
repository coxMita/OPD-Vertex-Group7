"""Entry point for email-service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.consumer import start_consumer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the application lifecycle events.

    Handles startup and shutdown operations for the email service.
    On startup, establishes a RabbitMQ connection and starts the consumer.
    On shutdown, properly closes the RabbitMQ connection.

    Args:
        app: The FastAPI application instance

    Yields:
        None: The context manager yields control to the application during its lifetime

    """
    # On startup
    try:
        connection = await start_consumer()
        yield
    finally:
        # On shutdown
        if "connection" in locals():
            await connection.close()
            logger.info("RabbitMQ connection closed.")


app = FastAPI(title="email-service", lifespan=lifespan)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "email-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
