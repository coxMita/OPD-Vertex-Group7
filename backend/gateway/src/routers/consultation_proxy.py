"""Proxy router for consultation-service."""

import logging

from fastapi import APIRouter, Request, Response

from src.config import CONSULTATION_SERVICE_URL
from src.dependencies.auth import require_doctor
from src.utils.http_client import client

router = APIRouter(prefix="/api/v1/consultations")
logger = logging.getLogger(__name__)

# Consultation routes are protected — doctor role required for all endpoints


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_consultation_root(request: Request) -> Response:
    """Proxy requests to the consultation-service root.

    Protected: doctor role required.
    """
    require_doctor(request)

    query_string = request.url.query
    url = f"{CONSULTATION_SERVICE_URL}/api/v1/consultations"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info(
        "Proxying request to Consultation Service: \n%s %s", request.method, url
    )

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
async def proxy_consultation(request: Request, path: str) -> Response:
    """Proxy requests to the consultation-service with path.

    Protected: doctor role required.
    """
    require_doctor(request)

    path = path.rstrip("/")
    query_string = request.url.query
    url = f"{CONSULTATION_SERVICE_URL}/api/v1/consultations/{path}"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info(
        "Proxying request to Consultation Service: \n%s %s", request.method, url
    )

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
