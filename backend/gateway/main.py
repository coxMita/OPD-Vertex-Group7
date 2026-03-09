"""Entry point for the API Gateway."""

import src.logger_config  # noqa: F401, I001
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.appointment_proxy import router as appointment_router

logger = logging.getLogger(__name__)

app = FastAPI(title="OPD-Vertex API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointment_router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "opd-vertex-gateway"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
