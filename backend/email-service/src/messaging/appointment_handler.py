"""Handler for appointment pub/sub events."""

import json
import logging

import aio_pika
import httpx
import os
from pydantic import ValidationError

from src.models.dto.appointment_event import AppointmentMessage, AppointmentStatus
from src.models.dto.email_event import EmailEvent
from src.services.email_service import EmailService

logger = logging.getLogger(__name__)

_email_service = EmailService()
# Default to the Docker internal URL if not provided
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000/api/v1/user/patients")
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

        # Only send an email when an appointment is (re)scheduled or created.
        if event.status != AppointmentStatus.SCHEDULED:
            await message.ack()
            return

        try:
            # 1. Fetch patient email and name (fully async)
            patient_data = await _fetch_patient(str(event.patient_id))
            to_email = patient_data.get("email") or FALLBACK_EMAIL
            first_name = patient_data.get("first_name") or "Patient"

            # 2. Build the notification body
            if event.assigned_time:
                assigned_time_str = event.assigned_time.strftime("%H:%M")
            else:
                assigned_time_str = event.time_preference.value

            formatted_date = event.appointment_date.strftime("%A, %d %B %Y")
            
            exchange_name = message.exchange
            if exchange_name == "appointment.created":
                subject = "Appointment Confirmation - OPD Vertex"
                body_msg = (
                    f"Hello {first_name},\n\n"
                    "Your appointment has been successfully booked.\n\n"
                    f"Date: {formatted_date}\n"
                    f"Assigned Time: {assigned_time_str}\n\n"
                    "Please arrive 10 minutes early.\n\n"
                    "Best regards,\n"
                    "OPD Vertex Staff"
                )
                log_msg = "Booking confirmation"
            else:
                subject = "Your Appointment Has Been Rescheduled - OPD Vertex"
                body_msg = (
                    f"Hello {first_name},\n\n"
                    "We wanted to let you know that your appointment at OPD Vertex "
                    "has been rescheduled by your doctor.\n\n"
                    f"  New date:  {formatted_date}\n"
                    f"  New time:  {assigned_time_str}\n\n"
                    "Please make a note of this change. If you have any questions or "
                    "need to make further changes, don't hesitate to contact us.\n\n"
                    "Best regards,\n"
                    "OPD Vertex Team"
                )
                log_msg = "Reschedule"

            # 3. Send the email through the existing service layer
            email_event = EmailEvent(
                to_email=to_email,
                subject=subject,
                message=body_msg,
                is_html=False,
            )
            await _email_service.handle_event(email_event)
            logger.info("%s email sent to %s", log_msg, to_email)
            await message.ack()

        except Exception as e:
            logger.error("Error processing appointment email: %s", e)
            await message.nack(requeue=True)
