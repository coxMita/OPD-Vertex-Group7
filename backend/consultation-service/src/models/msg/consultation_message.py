"""Consultation event message."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.models.db.consultation import ConsultationStatus
from src.models.msg.abstract_message import AbstractMessage

if TYPE_CHECKING:
    from src.models.db.consultation import Consultation


class ConsultationMessage(AbstractMessage):
    """Message published when a consultation event occurs.

    Attributes:
        consultation_id (int): Unique identifier of the consultation.
        appointment_id (int): Identifier of the associated appointment.
        doctor_id (int): Identifier of the doctor.
        status (ConsultationStatus): Current status of the consultation.
        audio_path (str | None): Path to audio file for transcription.
        transcript_id (int | None): Identifier of the transcript.
        prescription_id (int | None): Identifier of the prescription.

    """

    consultation_id: int
    appointment_id: int
    doctor_id: int
    status: ConsultationStatus
    audio_path: str | None = None
    transcript_id: int | None = None
    prescription_id: int | None = None

    @classmethod
    def from_entity(cls, entity: "Consultation") -> "ConsultationMessage":
        """Create a ConsultationMessage from a Consultation entity.

        Args:
            entity (Consultation): The consultation entity.

        Returns:
            ConsultationMessage: The created message instance.

        """
        return cls(
            consultation_id=entity.id,
            appointment_id=entity.appointment_id,
            doctor_id=entity.doctor_id,
            status=entity.status,
            audio_path=entity.audio_path,
            transcript_id=entity.transcript_id,
            prescription_id=entity.prescription_id,
        )
