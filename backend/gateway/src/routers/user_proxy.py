"""Proxy router for user-service."""

import logging

from fastapi import APIRouter, Request, Response

from src.config import USER_SERVICE_URL
from src.utils.http_client import client

router = APIRouter(prefix="/api/v1/users")
logger = logging.getLogger(__name__)


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_user_root(request: Request) -> Response:
    """Proxy requests to the user-service root.

    Args:
        request (Request): The incoming FastAPI request.

    Returns:
        Response: The response from the user-service.

    """
    query_string = request.url.query
    url = f"{USER_SERVICE_URL}/api/v1/users"
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

    Args:
        request (Request): The incoming FastAPI request.
        path (str): The path to be appended to the User Service URL.

    Returns:
        Response: The response from the user-service.

    """
    path = path.rstrip("/")
    query_string = request.url.query
    url = f"{USER_SERVICE_URL}/api/v1/users/{path}"
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
