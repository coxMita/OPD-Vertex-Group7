"""Consultation database model."""

import uuid
from datetime import datetime, time
from enum import Enum

from sqlmodel import Field, SQLModel


class ConsultationStatus(str, Enum):
    """Status of a consultation."""

    ACTIVE = "active"
    COMPLETED = "completed"


class Consultation(SQLModel, table=True):
    """Represents a patient consultation session tied to an appointment."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    appointment_id: uuid.UUID = Field(unique=True)
    doctor_id: uuid.UUID
    start_time: time | None = Field(default=None)
    end_time: time | None = Field(default=None)
    status: ConsultationStatus = Field(default=ConsultationStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
