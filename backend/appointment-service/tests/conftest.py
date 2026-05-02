"""Pytest configuration and shared fixtures."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AMQP_URL", "amqp://guest:guest@localhost/")
