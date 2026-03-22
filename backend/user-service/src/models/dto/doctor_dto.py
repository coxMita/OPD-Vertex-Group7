"""DTOs for doctor endpoints."""

import uuid

from pydantic import BaseModel

from src.models.db.user import Doctor


class DoctorResponse(BaseModel):
    """Response DTO for a doctor."""

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    specialization: str
    keycloak_id: uuid.UUID | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Doctor) -> "DoctorResponse":
        """Create a DoctorResponse from a Doctor entity.

        Args:
            entity (Doctor): The doctor entity.

        Returns:
            DoctorResponse: The response DTO.

        """
        return cls(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            email=entity.email,
            specialization=entity.specialization,
            keycloak_id=entity.keycloak_id,
        )
