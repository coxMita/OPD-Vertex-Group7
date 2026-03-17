"""DTO for creating an appointment."""

import uuid, json
from datetime import time

from pydantic import BaseModel

from src.models.db.prescription import PrescriptionStatus


class PrescriptionCreateRequest(BaseModel):
    """Request DTO for handling a prescription."""

    prescription_id= uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    consultation_id: uuid.UUID
    status= PrescriptionStatus.DRAFT
    medications_json= json
    approved_at: time | None= None
