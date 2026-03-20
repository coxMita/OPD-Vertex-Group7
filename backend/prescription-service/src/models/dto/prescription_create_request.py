"""DTO for creating an appointment."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from src.models.db.prescription import PrescriptionStatus


class PrescriptionCreateRequest(BaseModel):
    """Request DTO for handling a prescription."""

    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    consultation_id: uuid.UUID
    status: PrescriptionStatus = PrescriptionStatus.DRAFT
    prescription_json: dict = {}
    summary_json: dict = {}
    approved_at: datetime | None = None
