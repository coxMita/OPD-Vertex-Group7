"""Proxy router for appointment-service."""

import logging

from fastapi import APIRouter, Request, Response

from src.config import APPOINTMENT_SERVICE_URL
from src.dependencies.auth import require_doctor
from src.utils.http_client import client

router = APIRouter(prefix="/api/v1/appointments")
logger = logging.getLogger(__name__)

# Public routes (no token required):
# POST ""              → create appointment
# GET  "patient/{id}"  → patient's appointments
_PUBLIC_RULES: list[tuple[str, str]] = [
    ("POST", ""),
    ("GET", "patient"),
]


def _is_public(method: str, path: str) -> bool:
    """Return True if the request does not require authentication."""
    first_segment = path.strip("/").split("/")[0] if path.strip("/") else ""
    for pub_method, pub_segment in _PUBLIC_RULES:
        if method.upper() == pub_method and first_segment == pub_segment:
            return True
    return False


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_appointment(request: Request, path: str) -> Response:
    """Proxy requests to the appointment-service.

    Public routes (no token required):
        POST   /api/v1/appointments          — book appointment
        GET    /api/v1/appointments/patient/{id} — patient's appointments

    Protected routes (doctor token required):
        GET    /api/v1/appointments/queue/day
        PATCH  /api/v1/appointments/queue/reorder
        GET    /api/v1/appointments/{id}
        PATCH  /api/v1/appointments/{id}/status

    Args:
        request (Request): The incoming FastAPI request.
        path (str): The path to be appended to the Appointment Service URL.

    Returns:
        Response: The response from the appointment-service.

    """
    path = path.rstrip("/")

    if not _is_public(request.method, path):
        require_doctor(request)

    query_string = request.url.query
    url = f"{APPOINTMENT_SERVICE_URL}/api/v1/appointments"
    if path:
        url = f"{url}/{path}"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying request to Appointment Service: \n%s %s", request.method, url)

    body = await request.body()
    downstream_response = await client.request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        content=body,
    )

    logger.info(
        "Received response from Appointment Service with content: \n%s",
        downstream_response.content.decode(),
    )
    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=dict(downstream_response.headers),
        media_type=downstream_response.headers.get("content-type"),
    )
