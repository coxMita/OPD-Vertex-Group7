"""Root conftest — sets required env vars so imports succeed without Docker."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("AMQP_URL", "amqp://guest:guest@localhost:5672/")
