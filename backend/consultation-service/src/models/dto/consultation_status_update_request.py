"""DTO for updating consultation."""

from datetime import time

from pydantic import BaseModel

from src.models.db.consultation import ConsultationStatus


class ConsultationStatusUpdateRequest(BaseModel):
    """Request DTO for updating a consultation's status."""

    status: ConsultationStatus


class ConsultationUpdateRequest(BaseModel):
    """Request DTO for updating a consultation session."""

    start_time: time | None = None
    end_time: time | None = None
    status: ConsultationStatus | None = None
    audio_path: str | None = None
    transcript_id: int | None = None
    prescription_id: int | None = None
