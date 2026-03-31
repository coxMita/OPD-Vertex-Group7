from datetime import date
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Patient(SQLModel, table=True):
    """Patient database model."""

    patient_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
    )
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    date_of_birth: date = Field(nullable=False)
    gender: str = Field(nullable=False)
    phone_number: int = Field(nullable=False)
    email: str = Field(nullable=False)
