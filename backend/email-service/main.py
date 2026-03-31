"""Entry point for email-service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import aio_pika

from src.consumer import start_consumer, EmailEvent

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
        app.state.rabbitmq_connection = connection
        yield
    finally:
        # On shutdown
        if "connection" in locals():
            await connection.close()
            logger.info("RabbitMQ connection closed.")


app = FastAPI(title="email-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/send", status_code=202)
async def send_test_email(event: EmailEvent) -> dict[str, str]:
    """Test endpoint for the UI to trigger an email via RabbitMQ."""
    connection = app.state.rabbitmq_connection
    channel = await connection.channel()
    
    message_body = json.dumps(event.model_dump()).encode()
    
    await channel.default_exchange.publish(
        aio_pika.Message(body=message_body),
        routing_key="email_queue",
    )
    return {"status": "accepted", "message": "Email event published to queue."}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "email-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
