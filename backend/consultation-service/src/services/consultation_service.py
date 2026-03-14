"""Consultation service — business logic for consultations."""

import asyncio
import logging
from datetime import datetime

from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_exchanges import (
    CONSULTATION_COMPLETED,
    CONSULTATION_CREATED,
    CONSULTATION_STARTED,
)
from src.models.db.consultation import Consultation, ConsultationStatus
from src.models.dto.consultation_create_request import ConsultationCreateRequest
from src.models.dto.consultation_response import ConsultationResponse
from src.models.dto.consultation_status_update_request import (
    ConsultationUpdateRequest,
)
from src.models.msg.consultation_message import ConsultationMessage
from src.repositories.consultation_repository import ConsultationRepository

logger = logging.getLogger(__name__)


class ConsultationService:
    """Service for managing consultation sessions."""

    def __init__(
        self,
        repo: ConsultationRepository,
        messaging: MessagingManager,
    ) -> None:
        """Initialize the ConsultationService.

        Args:
            repo (ConsultationRepository): The consultation repository.
            messaging (MessagingManager): The messaging manager.

        """
        self._repo = repo
        self._messaging = messaging

    def create_consultation(
        self, request: ConsultationCreateRequest
    ) -> ConsultationResponse:
        """Create a new consultation session.

        Args:
            request (ConsultationCreateRequest): The consultation request.

        Returns:
            ConsultationResponse: The created consultation.

        Raises:
            ValueError: If a consultation already exists for the appointment.

        """
        existing = self._repo.get_by_appointment_id(request.appointment_id)
        if existing:
            raise ValueError(
                f"Consultation already exists for appointment {request.appointment_id}"
            )

        consultation = Consultation(
            appointment_id=request.appointment_id,
            doctor_id=request.doctor_id,
            status=ConsultationStatus.ACTIVE,
        )
        created = self._repo.create(consultation)
        self._publish(created, CONSULTATION_CREATED)
        self._publish(created, CONSULTATION_STARTED)
        return ConsultationResponse.from_entity(created)

    def get_consultation(self, consultation_id: int) -> ConsultationResponse | None:
        """Get a consultation by ID.

        Args:
            consultation_id (int): The consultation ID.

        Returns:
            ConsultationResponse | None: The consultation if found, else None.

        """
        consultation = self._repo.get_by_id(consultation_id)
        return ConsultationResponse.from_entity(consultation) if consultation else None

    def get_by_appointment_id(self, appointment_id: int) -> ConsultationResponse | None:
        """Get a consultation by appointment ID.

        Args:
            appointment_id (int): The appointment ID.

        Returns:
            ConsultationResponse | None: The consultation if found, else None.

        """
        consultation = self._repo.get_by_appointment_id(appointment_id)
        return ConsultationResponse.from_entity(consultation) if consultation else None

    def get_doctor_consultations(self, doctor_id: int) -> list[ConsultationResponse]:
        """Get all consultations for a doctor.

        Args:
            doctor_id (int): The doctor's ID.

        Returns:
            list[ConsultationResponse]: The doctor's consultations.

        """
        consultations = self._repo.get_by_doctor_id(doctor_id)
        return [ConsultationResponse.from_entity(c) for c in consultations]

    def update_consultation(
        self,
        consultation_id: int,
        request: ConsultationUpdateRequest,
    ) -> ConsultationResponse | None:
        """Update a consultation.

        Args:
            consultation_id (int): The consultation ID.
            request (ConsultationUpdateRequest): The update request.

        Returns:
            ConsultationResponse | None: The updated consultation, or None if not found.

        """
        consultation = self._repo.get_by_id(consultation_id)
        if consultation is None:
            return None

        update_fields = {}
        if request.start_time is not None:
            update_fields["start_time"] = request.start_time
        if request.end_time is not None:
            update_fields["end_time"] = request.end_time
        if request.audio_path is not None:
            update_fields["audio_path"] = request.audio_path
        if request.transcript_id is not None:
            update_fields["transcript_id"] = request.transcript_id
        if request.prescription_id is not None:
            update_fields["prescription_id"] = request.prescription_id

        update_fields["updated_at"] = datetime.utcnow()

        updated = self._repo.update(consultation, **update_fields)

        if request.status is not None and request.status != consultation.status:
            updated = self._repo.update_status(updated, request.status)
            self._publish(updated, CONSULTATION_CREATED)
            if request.status == ConsultationStatus.COMPLETED:
                self._publish(updated, CONSULTATION_COMPLETED)

        return ConsultationResponse.from_entity(updated)

    def update_status(
        self, consultation_id: int, status: ConsultationStatus
    ) -> ConsultationResponse | None:
        """Update the status of a consultation.

        Args:
            consultation_id (int): The consultation ID.
            status (ConsultationStatus): The new status.

        Returns:
            ConsultationResponse | None: The updated consultation, or None if not found.

        """
        consultation = self._repo.get_by_id(consultation_id)
        if consultation is None:
            return None

        updated = self._repo.update_status(consultation, status)
        self._publish(updated, CONSULTATION_CREATED)
        if status == ConsultationStatus.COMPLETED:
            self._publish(updated, CONSULTATION_COMPLETED)

        return ConsultationResponse.from_entity(updated)

    def _publish(self, consultation: Consultation, exchange: str) -> None:
        try:
            task = asyncio.create_task(
                self._messaging.get_pubsub(exchange).publish(
                    ConsultationMessage.from_entity(consultation)
                )
            )
            task.add_done_callback(ConsultationService._log_task_exception)
        except RuntimeError:
            logger.exception("Failed to publish event to exchange '%s'", exchange)

    @staticmethod
    def _log_task_exception(task: asyncio.Task) -> None:
        """Log exceptions from background publish tasks.

        Args:
            task (asyncio.Task): The completed task.

        """
        try:
            task.result()
        except Exception as e:
            logger.exception("Background publish failed: %s", e)
