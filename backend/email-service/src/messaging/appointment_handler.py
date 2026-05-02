"""Handler for appointment pub/sub events."""

import json
import logging
import os

import aio_pika
import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import ValidationError

from src.models.dto.appointment_event import AppointmentMessage, AppointmentStatus
from src.models.dto.email_event import EmailEvent
from src.services.email_service import EmailService

logger = logging.getLogger(__name__)

_email_service = EmailService()
# Default to the Docker internal URL if not provided
USER_SERVICE_URL = os.getenv(
    "USER_SERVICE_URL", "http://user-service:8000/api/v1/user/patients"
)
FALLBACK_EMAIL = "opdvertex00@gmail.com"
HTTP_OK = 200


async def _fetch_patient(patient_id: str) -> dict:
    """Fetch patient details from user-service.

    Falls back to mock data if user-service is unavailable.
    """
    url = f"{USER_SERVICE_URL}/{patient_id}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url, headers={"Accept": "application/json"})
            if response.status_code == HTTP_OK:
                return response.json()
            logger.warning(
                "user-service returned %s for patient %s",
                response.status_code,
                patient_id,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "Failed to fetch patient %s from user-service: %s", patient_id, exc
            )

    # Fallback: user-service is not reachable — send to the team inbox instead
    return {
        "first_name": "Patient",
        "last_name": "",
        "email": FALLBACK_EMAIL,
    }


async def process_appointment_message(
    message: aio_pika.abc.AbstractIncomingMessage,
) -> None:
    """Process an incoming appointment status change message from RabbitMQ."""
    async with message.process(ignore_processed=True):
        try:
            body = message.body.decode()
            data = json.loads(body)
            event = AppointmentMessage(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error("Invalid appointment message format: %s", e)
            await message.reject(requeue=False)
            return

        # Only send an email for scheduling/rescheduling and cancellations.
        if event.status not in (
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CANCELLED,
        ):
            await message.ack()
            return

        try:
            # 1. Fetch patient email and name (fully async)
            patient_data = await _fetch_patient(str(event.patient_id))
            to_email = patient_data.get("email") or FALLBACK_EMAIL
            first_name = patient_data.get("first_name") or "Patient"

            # 2. Setup Jinja2 Environment
            templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
            env = Environment(
                loader=FileSystemLoader(templates_dir),
                autoescape=select_autoescape(["html"]),
            )

            # 3. Build the notification body
            if event.assigned_time:
                assigned_time_str = event.assigned_time.strftime("%H:%M")
            else:
                assigned_time_str = event.time_preference.value

            formatted_date = event.appointment_date.strftime("%A, %d %B %Y")

            exchange_name = message.exchange
            if event.status == AppointmentStatus.CANCELLED:
                subject = "Your Appointment Has Been Cancelled - OPD Vertex"
                template = env.get_template("cancellation.html")
                body_msg = template.render(
                    first_name=first_name, date=formatted_date, time=assigned_time_str
                )
                log_msg = "Cancellation"
            elif exchange_name == "appointment.created":
                subject = "Appointment Confirmation - OPD Vertex"
                template = env.get_template("booking.html")
                body_msg = template.render(
                    first_name=first_name, date=formatted_date, time=assigned_time_str
                )
                log_msg = "Booking confirmation"
            else:
                subject = "Your Appointment Has Been Rescheduled - OPD Vertex"
                template = env.get_template("reschedule.html")
                body_msg = template.render(
                    first_name=first_name, date=formatted_date, time=assigned_time_str
                )
                log_msg = "Reschedule"

            # 4. Send the email through the existing service layer
            email_event = EmailEvent(
                to_email=to_email,
                subject=subject,
                message=body_msg,
                is_html=True,
            )
            await _email_service.handle_event(email_event)
            logger.info("%s email sent to %s", log_msg, to_email)
            await message.ack()

        except Exception as e:
            logger.error("Error processing appointment email: %s", e)
            await message.nack(requeue=True)
