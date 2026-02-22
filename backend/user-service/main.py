"""Entry point for user-service."""

from fastapi import FastAPI

app = FastAPI(title="user-service")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "user-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
