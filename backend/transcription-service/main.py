"""Entry point for transcription-service."""

from fastapi import FastAPI

app = FastAPI(title="transcription-service")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "transcription-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
