FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock .python-version .env main.py alembic.ini seed.py entrypoint.sh ./
COPY src ./src
COPY migrations ./migrations
RUN uv venv && uv sync
RUN chmod +x entrypoint.sh
ENV PYTHONPATH=/app
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]
