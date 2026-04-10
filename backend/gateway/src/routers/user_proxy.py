# backend/gateway/src/routers/user_proxy.py
"""Proxy router for user-service."""

import logging

from fastapi import APIRouter, Request, Response

from src.config import USER_SERVICE_URL
from src.dependencies.auth import require_doctor
from src.utils.http_client import client

router = APIRouter(prefix="/api/v1/user")
logger = logging.getLogger(__name__)

# Public routes (no token required):
# POST ""                           → find-or-create patient
# GET  "patients/by-email"          → lookup patient after email (for booking form)
# GET  "doctor/{dept}/doctors"      → list of doctors for the booking form
_PUBLIC_RULES: list[tuple[str, str]] = [
    ("POST", "patients"),
    ("GET", "patients"),  # patients/by-email
    ("GET", "doctor"),  # doctor/{dept}/doctors
]


def _is_public(method: str, path: str) -> bool:
    """Return True if the request does not require authentication."""
    first_segment = path.strip("/").split("/")[0] if path.strip("/") else ""
    for pub_method, pub_segment in _PUBLIC_RULES:
        if method.upper() == pub_method and first_segment == pub_segment:
            return True
    return False


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_user_root(request: Request) -> Response:
    """Proxy requests to the user-service root.

    Public routes (no token required):
        POST /api/v1/user/patients — find-or-create patient

    Args:
        request (Request): The incoming FastAPI request.

    Returns:
        Response: The response from the user-service.

    """
    # Root-ul without path
    if request.method.upper() not in ("POST",):
        require_doctor(request)

    query_string = request.url.query
    url = f"{USER_SERVICE_URL}/api/v1/user"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying request to User Service: \n%s %s", request.method, url)

    body = await request.body()
    downstream_response = await client.request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        content=body,
    )

    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=dict(downstream_response.headers),
        media_type=downstream_response.headers.get("content-type"),
    )


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_user(request: Request, path: str) -> Response:
    """Proxy requests to the user-service with path.

    Public routes (no token required):
        POST /api/v1/user/patients          — find-or-create patient
        GET  /api/v1/user/patients/by-email — lookup by email
        GET  /api/v1/user/doctor/{dept}/doctors — doctor list for booking form

    Protected routes (doctor token required):
        GET  /api/v1/user/patients/{id}     — get patient by ID
        GET  /api/v1/user/doctors/{id}      — get doctor by ID

    Args:
        request (Request): The incoming FastAPI request.
        path (str): The path to be appended to the User Service URL.

    Returns:
        Response: The response from the user-service.

    """
    path = path.rstrip("/")

    if not _is_public(request.method, path):
        require_doctor(request)

    query_string = request.url.query
    url = f"{USER_SERVICE_URL}/api/v1/user/{path}"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying request to User Service: \n%s %s", request.method, url)

    body = await request.body()
    downstream_response = await client.request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        content=body,
    )

    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=dict(downstream_response.headers),
        media_type=downstream_response.headers.get("content-type"),
    )
