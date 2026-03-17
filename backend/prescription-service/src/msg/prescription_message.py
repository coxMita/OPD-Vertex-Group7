"""Prescription event message."""
import uuid, json
from datetime import date, time

from src.models.db.prescription import PrescriptionStatus, Prescription
from msg.abstract_message import AbstractMessage


class PrescriptionMessage(AbstractMessage):
    """Message published when an prescription event occurs.

    Attributes:
        id (UUID): Unique identifier of the prescription.
        patient_id (UUID): Identifier of the patient.
        doctor_id (UUID): Identifier of the doctor.
        consultation_id (UUID): Identifier of a consultation.
        medications_json (json): Json file of the medications assigned.
        approved_at (time): Time of approval of a prescription by the doctor.
        status (PrescriptionStatus): Current status of the prescription.

    """

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID 
    status: PrescriptionStatus
    medications_json: json
    approved_at: time | None 

    @classmethod
    def from_entity(cls, entity: "Prescription") -> "PrescriptionMessage":  # noqa: F821
        """Create an PrescriptionMessage from an Prescription entity.

        Args:
            entity (Prescription): The prescription entity.

        Returns:
            PrescriptionMessage: The created message instance.

        """
        return cls(
            prescription_id=entity.id,
            patient_id=entity.patient_id,
            doctor_id=entity.doctor_id,
            consultation_id=entity.consultation_id,
            approved_at=entity.approved_at,
            medications_json=entity.medications_json,
            status=entity.status,
        )
