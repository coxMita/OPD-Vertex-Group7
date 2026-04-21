"""Entry point for the API Gateway."""

import src.logger_config  # noqa: F401, I001
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.dependencies.auth import verify_token
from src.routers.appointment_proxy import router as appointment_router
from src.routers.consultation_proxy import router as consultation_router
from src.routers.prescription_proxy import router as prescription_router
from src.routers.transcription_proxy import router as transcription_router
from src.routers.user_proxy import router as user_router

logger = logging.getLogger(__name__)

app = FastAPI(title="OPD-Vertex API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointment_router, dependencies=[Depends(verify_token)])
app.include_router(consultation_router, dependencies=[Depends(verify_token)])
app.include_router(prescription_router, dependencies=[Depends(verify_token)])
app.include_router(transcription_router, dependencies=[Depends(verify_token)])
app.include_router(user_router, dependencies=[Depends(verify_token)])


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "opd-vertex-gateway"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
