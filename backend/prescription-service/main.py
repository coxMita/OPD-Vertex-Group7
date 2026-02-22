"""Entry point for prescription-service."""

from fastapi import FastAPI

app = FastAPI(title="prescription-service")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "prescription-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
