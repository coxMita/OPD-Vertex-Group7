"""Prescription service — business logic."""

import logging
import uuid

from src.models.db.prescription import Prescription, PrescriptionStatus
from src.models.dto.prescription_response import PrescriptionResponse
from src.repositories.prescription_repository import PrescriptionRepository

logger = logging.getLogger(__name__)

# Nil UUID used as placeholder when patient/doctor IDs are not yet known
# (prescription created from RabbitMQ message before BFF enrichment)
NIL_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")


class PrescriptionService:
    """Service for managing prescriptions."""

    def __init__(self, repo: PrescriptionRepository) -> None:
        """Initialise the PrescriptionService.

        Args:
            repo: The prescription repository.

        """
        self._repo = repo

    def create_from_ai(
        self,
        consultation_id: uuid.UUID,
        prescription_json: dict,
        summary: str,
    ) -> PrescriptionResponse:
        """Create a DRAFT prescription from an AI-completed event.

        patient_id and doctor_id are set to NIL_UUID — they can be enriched
        later via a PATCH or by the consultation-service.

        Args:
            consultation_id: UUID of the consultation.
            prescription_json: Structured prescription data from the LLM.
            summary: Clinical summary text from the LLM.

        Returns:
            PrescriptionResponse: The created prescription.

        """
        prescription = Prescription(
            consultation_id=consultation_id,
            patient_id=NIL_UUID,
            doctor_id=NIL_UUID,
            status=PrescriptionStatus.DRAFT,
            prescription_json=prescription_json,
            summary_json={"summary": summary},
        )
        created = self._repo.create(prescription)
        logger.info(
            "Created prescription '%s' for consultation '%s'.",
            created.id,
            consultation_id,
        )
        return PrescriptionResponse.from_entity(created)

    def get_by_id(self, prescription_id: uuid.UUID) -> PrescriptionResponse | None:
        """Get a prescription by ID.

        Args:
            prescription_id: The prescription UUID.

        Returns:
            PrescriptionResponse | None: The prescription if found, else None.

        """
        prescription = self._repo.get_by_id(prescription_id)
        return PrescriptionResponse.from_entity(prescription) if prescription else None

    def get_by_consultation_id(
        self, consultation_id: uuid.UUID
    ) -> PrescriptionResponse | None:
        """Get the most recent prescription for a consultation.

        Args:
            consultation_id: The consultation UUID.

        Returns:
            PrescriptionResponse | None: The prescription if found, else None.

        """
        prescription = self._repo.get_by_consultation_id(consultation_id)
        return PrescriptionResponse.from_entity(prescription) if prescription else None

    def get_by_patient_id(self, patient_id: uuid.UUID) -> list[PrescriptionResponse]:
        """Get all prescriptions for a patient.

        Args:
            patient_id: The patient UUID.

        Returns:
            list[PrescriptionResponse]: The patient's prescriptions.

        """
        prescriptions = self._repo.get_by_patient_id(patient_id)
        return [PrescriptionResponse.from_entity(p) for p in prescriptions]

    def approve(self, prescription_id: uuid.UUID) -> PrescriptionResponse | None:
        """Approve a prescription.

        Args:
            prescription_id: The prescription UUID.

        Returns:
            PrescriptionResponse | None: The updated prescription, or None if not found.

        """
        prescription = self._repo.get_by_id(prescription_id)
        if prescription is None:
            return None
        updated = self._repo.update_status(prescription, PrescriptionStatus.APPROVED)
        return PrescriptionResponse.from_entity(updated)
