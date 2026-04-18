"""Entry point for gateway with robust proxy logic and connection pooling."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registry of downstream services
# These map incoming path prefixes to internal service URLs
SERVICE_MAP = {
    "/api/v1/users": os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
    "/api/v1/appointments": os.getenv("APPOINTMENT_SERVICE_URL", "http://appointment-service:8000"),
    "/api/v1/consultations": os.getenv("CONSULTATION_SERVICE_URL", "http://consultation-service:8000"),
    "/api/v1/prescriptions": os.getenv("PRESCRIPTION_SERVICE_URL", "http://prescription-service:8000"),
    "/api/v1/ai": os.getenv("AI_SERVICE_URL", "http://ai-service:8000"),
    "/api/v1/email": os.getenv("EMAIL_SERVICE_URL", "http://email-service:8000"),
    "/transcription": os.getenv("TRANSCRIPTION_SERVICE_URL", "http://transcription-service:8000"),
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Manage Gateway lifecycle, specifically the shared HTTP client."""
    # Using a 60s default timeout. Connection pooling is handled automatically by httpx.
    app.state.client = httpx.AsyncClient(timeout=60.0)
    logger.info("Gateway shared AsyncClient initialized.")
    yield
    await app.state.client.aclose()
    logger.info("Gateway shared AsyncClient closed.")


app = FastAPI(title="OPD-Vertex Gateway", lifespan=lifespan)

# Enable CORS for the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(request: Request, path: str) -> Response:
    """Universal proxy for all microservices in the OPD-Vertex ecosystem."""
    full_path = f"/{path}"

    # 1. Identify Target Service
    target_base_url = None
    # Sort by length descending to match the most specific prefix first
    sorted_prefixes = sorted(SERVICE_MAP.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if full_path.startswith(prefix):
            target_base_url = SERVICE_MAP[prefix]
            break

    # Handle Gateway's own routes
    if not target_base_url:
        if path == "" or path == "health":
            return Response(content='{"service": "gateway", "status": "ok"}', media_type="application/json")
        return Response(content=f"Gateway: No route match for {full_path}", status_code=404)

    # 2. Prepare Forwarded Request
    url = f"{target_base_url}{full_path}"
    # Filter headers to avoid conflicts (e.g., httpx sets the correct Host header)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    
    # Apply specific timeouts for heavy-duty services
    timeout = 300.0 if any(x in full_path for x in ["transcription", "ai"]) else 60.0

    # 3. Proxy Request
    try:
        proxy_resp = await request.app.state.client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body(),
            params=dict(request.query_params),
            timeout=timeout,
        )

        # 4. Return Forwarded Response
        return Response(
            content=proxy_resp.content,
            status_code=proxy_resp.status_code,
            headers=dict(proxy_resp.headers),
        )
    except httpx.ConnectError:
        logger.error(f"Service unreachable: {target_base_url}")
        return Response(content=f"Gateway error: Service {target_base_url} is unreachable.", status_code=503)
    except httpx.TimeoutException:
        logger.error(f"Service timed out: {url}")
        return Response(content="Gateway error: Service timed out.", status_code=504)
    except Exception as e:
        logger.exception(f"Unexpected proxy error: {str(e)}")
        return Response(content=f"Gateway internal error: {str(e)}", status_code=502)
