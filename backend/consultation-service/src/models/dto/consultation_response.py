"""DTO for consultation responses."""

import uuid
from datetime import datetime, time

from pydantic import BaseModel

from src.models.db.consultation import Consultation, ConsultationStatus


class ConsultationResponse(BaseModel):
    """Response DTO for a consultation session."""

    id: uuid.UUID
    appointment_id: uuid.UUID
    doctor_id: uuid.UUID
    start_time: time | None
    end_time: time | None
    status: ConsultationStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Consultation) -> "ConsultationResponse":
        """Create a ConsultationResponse from a Consultation entity.

        Args:
            entity (Consultation): The consultation entity.

        Returns:
            ConsultationResponse: The response DTO.

        """
        return cls(
            id=entity.id,
            appointment_id=entity.appointment_id,
            doctor_id=entity.doctor_id,
            start_time=entity.start_time,
            end_time=entity.end_time,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
