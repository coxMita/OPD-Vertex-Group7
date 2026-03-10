"""Consultation database model."""

from datetime import datetime, time
from enum import Enum

from sqlmodel import Field, SQLModel


class ConsultationStatus(str, Enum):
    """Status of a consultation."""

    ACTIVE = "active"
    COMPLETED = "completed"


class Consultation(SQLModel, table=True):
    """Represents a patient consultation session tied to an appointment."""

    id: int | None = Field(default=None, primary_key=True)
    appointment_id: int = Field(foreign_key="appointment.id", unique=True)
    doctor_id: int
    start_time: time | None = Field(default=None)
    end_time: time | None = Field(default=None)
    status: ConsultationStatus = Field(default=ConsultationStatus.ACTIVE)
    audio_path: str | None = Field(default=None)
    transcript_id: int | None = Field(default=None)
    prescription_id: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
