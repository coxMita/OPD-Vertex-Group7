"""DTO for updating appointment status."""

from pydantic import BaseModel

from src.models.db.appointment import AppointmentStatus


class AppointmentStatusUpdateRequest(BaseModel):
    """Request DTO for updating an appointment's status."""

    status: AppointmentStatus