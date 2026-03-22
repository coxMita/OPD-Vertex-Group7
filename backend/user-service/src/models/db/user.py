"""User database models — Patient and Doctor."""

import uuid
from datetime import date
from enum import Enum

from sqlmodel import Field, SQLModel


class Gender(str, Enum):
    """Patient gender."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Patient(SQLModel, table=True):
    """Represents a patient in the system."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True, index=True)
    phone: str = Field(unique=True)
    date_of_birth: date
    gender: Gender


class Doctor(SQLModel, table=True):
    """Represents a doctor in the system."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True, index=True)
    specialization: str
    keycloak_id: uuid.UUID | None = Field(default=None, nullable=True)
