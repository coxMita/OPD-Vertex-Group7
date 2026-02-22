"""Entry point for gateway."""

from fastapi import FastAPI

app = FastAPI(title="gateway")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "gateway"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
