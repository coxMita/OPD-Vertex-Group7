"""Entry point for consultation-service."""

from fastapi import FastAPI

app = FastAPI(title="consultation-service")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "consultation-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
