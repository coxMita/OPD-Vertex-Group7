"""HTTP routes for email-service."""

import json
import os
import secrets
import string
from datetime import datetime, timedelta, timezone

import aio_pika
from fastapi import APIRouter, Request
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import settings
from src.models.dto.email_event import EmailEvent
from src.models.dto.otp import OtpSendRequest, OtpVerifyRequest, OtpVerifyResponse

router = APIRouter(prefix="/api", tags=["email"])

# In-memory OTP store: email -> {code, expires_at}
_otp_store: dict[str, dict] = {}
_OTP_TTL_MINUTES = 10
_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates")


def _generate_otp() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))


async def _publish(request: Request, event: EmailEvent) -> None:
    connection = request.app.state.rabbitmq_connection
    channel = await connection.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(event.model_dump()).encode()),
        routing_key=settings.EMAIL_QUEUE_NAME,
    )


@router.post("/send", status_code=202)
async def send_test_email(request: Request, event: EmailEvent) -> dict[str, str]:
    """Test endpoint: publish an email event to the queue (same path as worker)."""
    await _publish(request, event)
    return {"status": "accepted", "message": "Email event published to queue."}


@router.post("/otp/send", status_code=200)
async def send_otp(request: Request, body: OtpSendRequest) -> dict[str, str]:
    """Generate a 6-digit OTP, store it, and send it to the given email."""
    code = _generate_otp()
    _otp_store[body.email] = {
        "code": code,
        "expires_at": datetime.now(tz=timezone.utc)
        + timedelta(minutes=_OTP_TTL_MINUTES),
    }

    env = Environment(
        loader=FileSystemLoader(_TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )
    html = env.get_template("otp.html").render(code=code)

    await _publish(
        request,
        EmailEvent(
            to_email=body.email,
            subject="Your OPD Vertex verification code",
            message=html,
            is_html=True,
        ),
    )
    return {"status": "sent"}


@router.post("/otp/verify", status_code=200, response_model=OtpVerifyResponse)
async def verify_otp(body: OtpVerifyRequest) -> OtpVerifyResponse:
    """Verify a previously issued OTP. The code is consumed on success."""
    entry = _otp_store.get(body.email)
    if not entry:
        return OtpVerifyResponse(valid=False)

    if datetime.now(tz=timezone.utc) > entry["expires_at"]:
        del _otp_store[body.email]
        return OtpVerifyResponse(valid=False)

    if entry["code"] != body.code:
        return OtpVerifyResponse(valid=False)

    del _otp_store[body.email]
    return OtpVerifyResponse(valid=True)
