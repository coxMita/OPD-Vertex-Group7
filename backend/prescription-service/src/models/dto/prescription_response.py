"""DTO for prescription responses."""
import uuid

from datetime import date, time

from pydantic import BaseModel

from src.models.db.prescription import Prescription, PrescriptionStatus, TimePreference


class PrescriptionResponse(BaseModel):
    """Response DTO for a prescription."""
    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID 
    status: PrescriptionStatus
    medications_json: json
    approved_at: time | None 

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
            medications_json=entity.medications_json,
            approved_at=entity.approved_at,
        )
