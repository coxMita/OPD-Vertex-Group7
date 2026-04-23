"""Proxy router for email-service."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request, Response

from src.config import EMAIL_SERVICE_URL
from src.models.dto.email_send_request import EmailAcceptedResponse, EmailSendRequest
from src.utils.http_client import client

router = APIRouter(prefix="/api/v1/email")
logger = logging.getLogger(__name__)


@router.post(
    "/send",
    status_code=202,
    response_model=EmailAcceptedResponse,
    summary="Queue an email",
    description=(
        "Publishes an email job to RabbitMQ via email-service (same as POST /api/send "
        "on the email service)."
    ),
)
async def send_email(payload: EmailSendRequest) -> EmailAcceptedResponse:
    """Proxy POST /api/send with a documented JSON body (Swagger UI)."""
    url = f"{EMAIL_SERVICE_URL.rstrip('/')}/api/send"
    body = json.dumps(payload.model_dump()).encode()

    logger.info("Proxying POST to Email Service: %s", url)

    downstream_response = await client.request(
        method="POST",
        url=url,
        headers={"Content-Type": "application/json"},
        content=body,
    )

    logger.info(
        "Received response from Email Service with status %s",
        downstream_response.status_code,
    )

    if not downstream_response.is_success:
        raise HTTPException(
            status_code=downstream_response.status_code,
            detail=downstream_response.text,
        )

    return EmailAcceptedResponse.model_validate_json(downstream_response.content)


@router.api_route(
    "/{path:path}",
    methods=["GET", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def proxy_email(request: Request, path: str) -> Response:
    """Proxy non-POST paths to email-service ``/api/...``.

    ``POST /send`` is a separate operation so it appears in OpenAPI; POST is not
    registered on this catch-all (avoids path/method clashes in ``/docs``).
    """
    path = path.rstrip("/")
    query_string = request.url.query
    base = f"{EMAIL_SERVICE_URL.rstrip('/')}/api"
    url = f"{base}/{path}" if path else base
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying request to Email Service: \n%s %s", request.method, url)

    body = await request.body()
    downstream_response = await client.request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        content=body,
    )

    logger.info(
        "Received response from Email Service with status %s",
        downstream_response.status_code,
    )
    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=dict(downstream_response.headers),
        media_type=downstream_response.headers.get("content-type"),
    )
