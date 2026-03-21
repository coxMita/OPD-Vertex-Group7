"""Consultation event message."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.models.db.consultation import ConsultationStatus
from src.models.msg.abstract_message import AbstractMessage

if TYPE_CHECKING:
    from src.models.db.consultation import Consultation


class ConsultationMessage(AbstractMessage):
    """Message published when a consultation event occurs.

    Attributes:
        consultation_id (uuid.UUID): Unique identifier of the consultation.
        appointment_id (int): Identifier of the associated appointment.
        doctor_id (int): Identifier of the doctor.
        status (ConsultationStatus): Current status of the consultation.

    """

    consultation_id: uuid.UUID
    appointment_id: uuid.UUID
    doctor_id: uuid.UUID
    status: ConsultationStatus

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
        )
