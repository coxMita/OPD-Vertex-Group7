"""DTO for creating a consultation."""

import uuid

from pydantic import BaseModel


class ConsultationCreateRequest(BaseModel):
    """Request DTO for creating a consultation session."""

    appointment_id: uuid.UUID
    doctor_id: uuid.UUID
