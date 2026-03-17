"""Appointment database model."""
import uuid, json
from datetime import date, time
from enum import Enum

from sqlmodel import Field, SQLModel

class PrescriptionStatus(str, Enum):
    """Status of an prescription."""

    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"

class Prescription(SQLModel, table=True):
    """Represents a patient prescription."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    status: PrescriptionStatus = Field(default=PrescriptionStatus.DRAFT)
    medications_json: json
    approved_at: time | None = Field(default=None)
