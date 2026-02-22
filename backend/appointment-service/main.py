"""Entry point for appointment-service."""

from fastapi import FastAPI

app = FastAPI(title="appointment-service")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "appointment-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
