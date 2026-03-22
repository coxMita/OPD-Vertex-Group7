"""Entry point for user-service."""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI

import src.logger_config  # noqa: F401, I001
from src.api.routes.doctor_routes import router as doctor_router
from src.api.routes.patient_routes import router as patient_router

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="user-service")
app.include_router(patient_router)
app.include_router(doctor_router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "user-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
