"""Proxy router for transcription-service."""

import logging

import httpx
from fastapi import APIRouter, Request, Response

from src.config import TRANSCRIPTION_SERVICE_URL

router = APIRouter(prefix="/api/v1/transcription")
logger = logging.getLogger(__name__)

# Dedicated client for transcription — needs much longer timeouts for audio files
_transcription_client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,
        write=600.0,  # 5 min to upload the file
        read=600.0,  # 5 min to wait for Whisper to finish
        pool=10.0,
    )
)


@router.post("/")
async def proxy_transcription(request: Request) -> Response:
    """Proxy POST requests to the transcription-service.

    Forwards the full query string (including consultation_id) to the
    downstream service.

    Args:
        request: The incoming FastAPI request.

    Returns:
        Response: The response from the transcription-service.

    """
    query_string = request.url.query
    url = f"{TRANSCRIPTION_SERVICE_URL}/transcription/"
    if query_string:
        url = f"{url}?{query_string}"

    logger.info("Proxying transcription request to: %s", url)

    body = await request.body()
    downstream_response = await _transcription_client.request(
        method="POST",
        url=url,
        headers=request.headers.raw,
        content=body,
    )

    logger.info(
        "Transcription service responded: status=%s", downstream_response.status_code
    )

    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=dict(downstream_response.headers),
        media_type=downstream_response.headers.get("content-type"),
    )
