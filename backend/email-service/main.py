"""Entry point for email-service."""

from fastapi import FastAPI

app = FastAPI(title="email-service")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "email-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
