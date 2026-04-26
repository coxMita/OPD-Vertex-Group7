"""Proxy router for ai-service."""

import logging

import httpx
from fastapi import APIRouter, Request, Response

from src.config import AI_SERVICE_URL

router = APIRouter(prefix="/api/v1/ai")
logger = logging.getLogger(__name__)

# Dedicated client for ai-service — generation can take several minutes.
_ai_client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,
        write=300.0,
        read=300.0,
        pool=10.0,
    ),
    follow_redirects=True,
)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_ai(request: Request, path: str) -> Response:
    """Proxy requests to the ai-service with path."""
    path = path.rstrip("/")
    query_string = request.url.query
    url = f"{AI_SERVICE_URL}/ai/{path}"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying to AI Service: %s %s", request.method, url)

    body = await request.body()
    downstream = await _ai_client.request(
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
