"""DTO for consultation responses."""

from datetime import datetime, time

from pydantic import BaseModel

from src.models.db.consultation import Consultation, ConsultationStatus


class ConsultationResponse(BaseModel):
    """Response DTO for a consultation session."""

    id: int
    appointment_id: int
    doctor_id: int
    start_time: time | None
    end_time: time | None
    status: ConsultationStatus
    audio_path: str | None
    transcript_id: int | None
    prescription_id: int | None
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
            audio_path=entity.audio_path,
            transcript_id=entity.transcript_id,
            prescription_id=entity.prescription_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
