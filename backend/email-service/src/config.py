"""Load process environment into typed ``settings`` (single place for os.getenv).

Docker or your shell still *set* the variables; this module only *reads* them at
import time, applies defaults, and parses types so other modules import ``settings``
instead of calling ``os.getenv`` everywhere.

The gateway only forwards HTTP; it does not inject RabbitMQ or SMTP values here.
"""

import os

from dotenv import load_dotenv

from src.constants import DEFAULT_EMAIL_QUEUE_NAME

load_dotenv()


class Settings:
    """Application configuration loaded from the environment."""

    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    EMAIL_QUEUE_NAME: str = os.getenv("EMAIL_QUEUE_NAME", DEFAULT_EMAIL_QUEUE_NAME)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "test@example.com")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "t")


settings = Settings()
