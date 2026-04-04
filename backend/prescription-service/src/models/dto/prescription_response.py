"""DTO for prescription responses."""

import uuid
from datetime import time

from pydantic import BaseModel

from src.models.db.prescription import Prescription, PrescriptionStatus


class PrescriptionResponse(BaseModel):
    """Response DTO for a prescription."""

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    status: PrescriptionStatus
    prescription_json: dict
    summary_json: dict
    approved_at: time | None

    model_config = {"from_attributes": True}  # allows .model_validate(entity)

    @classmethod
    def from_entity(cls, entity: Prescription) -> "PrescriptionResponse":
        """Create an PrescriptionResponse from an Prescription entity.

        Args:
            entity (Prescription): The prescription entity.

        Returns:
            PrescriptionResponse: The response DTO.

        """
        return cls(
            id=entity.id,
            consultation_id=entity.consultation_id,
            patient_id=entity.patient_id,
            doctor_id=entity.doctor_id,
            status=entity.status,
            prescription_json=entity.prescription_json,
            summary_json=entity.summary_json,
            approved_at=entity.approved_at,
        )
