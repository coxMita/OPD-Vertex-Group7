"""Proxy router for prescription-service."""

import logging

from fastapi import APIRouter, Request, Response

from src.config import PRESCRIPTION_SERVICE_URL
from src.utils.http_client import client

router = APIRouter(prefix="/api/v1/prescriptions")
logger = logging.getLogger(__name__)


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_prescription_root(request: Request) -> Response:
    """Proxy requests to the prescription-service root."""
    query_string = request.url.query
    url = f"{PRESCRIPTION_SERVICE_URL}/api/v1/prescriptions"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying to Prescription Service: %s %s", request.method, url)

    body = await request.body()
    downstream = await client.request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        content=body,
    )
    return Response(
        content=downstream.content,
        status_code=downstream.status_code,
        headers=dict(downstream.headers),
        media_type=downstream.headers.get("content-type"),
    )


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_prescription(request: Request, path: str) -> Response:
    """Proxy requests to the prescription-service with path."""
    path = path.rstrip("/")
    query_string = request.url.query
    url = f"{PRESCRIPTION_SERVICE_URL}/api/v1/prescriptions/{path}"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying to Prescription Service: %s %s", request.method, url)

    body = await request.body()
    downstream = await client.request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        content=body,
    )
    return Response(
        content=downstream.content,
        status_code=downstream.status_code,
        headers=dict(downstream.headers),
        media_type=downstream.headers.get("content-type"),
    )
