from uuid import UUID

from pydantic import BaseModel


class DoctorDTO(BaseModel):
    """Data Transfer Object for Doctor."""

    doctor_id: UUID
    full_name: str
    department_name: str
    email: str
    keycloak_id: UUID
