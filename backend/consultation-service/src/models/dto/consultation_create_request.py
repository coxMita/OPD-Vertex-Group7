"""DTO for creating a consultation."""

from pydantic import BaseModel


class ConsultationCreateRequest(BaseModel):
    """Request DTO for creating a consultation session."""

    appointment_id: int
    doctor_id: int
