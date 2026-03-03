"""Root conftest - sets AMQP_URL so main.py does not raise on import."""

import os

os.environ.setdefault("AMQP_URL", "amqp://guest:guest@localhost/")
