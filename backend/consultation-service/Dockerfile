FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock .python-version main.py .env alembic.ini ./
COPY src ./src
COPY migrations ./migrations
RUN uv venv && uv sync
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]
