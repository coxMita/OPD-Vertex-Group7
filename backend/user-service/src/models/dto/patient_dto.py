from datetime import date
from uuid import UUID

from pydantic import BaseModel


class PatientDTO(BaseModel):
    """Data Transfer Object for Patient."""

    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone_number: int
    email: str
