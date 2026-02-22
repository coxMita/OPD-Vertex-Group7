"""Entry point for ai-service."""

from fastapi import FastAPI

app = FastAPI(title="ai-service")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "ai-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
