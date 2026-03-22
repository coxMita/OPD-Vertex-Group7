"""DTOs for patient endpoints."""

import uuid
from datetime import date

from pydantic import BaseModel

from src.models.db.user import Gender, Patient


class PatientFindOrCreateRequest(BaseModel):
    """Request DTO for find-or-create patient."""

    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: date
    gender: Gender


class PatientResponse(BaseModel):
    """Response DTO for a patient."""

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: date
    gender: Gender

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Patient) -> "PatientResponse":
        """Create a PatientResponse from a Patient entity.

        Args:
            entity (Patient): The patient entity.

        Returns:
            PatientResponse: The response DTO.

        """
        return cls(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            email=entity.email,
            phone=entity.phone,
            date_of_birth=entity.date_of_birth,
            gender=entity.gender,
        )
