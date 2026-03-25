from datetime import date

from pydantic import BaseModel


class PatientCreateRequest(BaseModel):
    """Request model for creating or finding a patient."""

    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone_number: int
    email: str
