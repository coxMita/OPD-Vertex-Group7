#!/bin/sh
# Bring the database up to date before the service starts accepting traffic.
# Without this a fresh volume has no tables and every doctor query 500s.
set -e

echo "Applying database migrations..."
uv run alembic upgrade head

# Development-only sample doctors. seed.py skips rows that already exist.
if [ "$SEED_ON_STARTUP" = "true" ]; then
    echo "Seeding doctors..."
    uv run python seed.py
fi

exec "$@"
