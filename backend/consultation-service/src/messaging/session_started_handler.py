"""Handlers for incoming appointment session events."""

import logging
from typing import Callable

from sqlmodel import Session

from src.messaging.messaging_manager import MessagingManager
from src.models.dto.consultation_create_request import ConsultationCreateRequest
from src.models.msg.session_started_message import SessionStartedMessage
from src.repositories.consultation_repository import ConsultationRepository
from src.services.consultation_service import ConsultationService

logger = logging.getLogger(__name__)


async def handle_session_started(
    message: SessionStartedMessage,
    get_session: Callable[[], Session],
    messaging_manager: MessagingManager,
) -> None:
    """Create consultations for all appointments in a session-started event."""
    with get_session() as session:
        repo = ConsultationRepository(session)
        service = ConsultationService(repo, messaging_manager)

        logger.info(
            "Received session_started | doctor=%s | %s | %s | %d appointments",
            message.doctor_id,
            message.time_preference.value,
            message.appointment_date,
            len(message.appointments),
        )

        for appointment in message.appointments:
            try:
                service.create_consultation(
                    ConsultationCreateRequest(
                        appointment_id=appointment.appointment_id,
                        doctor_id=message.doctor_id,
                    )
                )
                logger.info(
                    "Created consultation for appointment %s (doctor=%s)",
                    appointment.appointment_id,
                    message.doctor_id,
                )
            except ValueError:
                logger.info(
                    "Consultation already exists for appointment %s; skipping",
                    appointment.appointment_id,
                )
            except Exception:
                logger.exception(
                    "Failed to create consultation for appointment %s",
                    appointment.appointment_id,
                )
