"""Prescription database model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
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
    prescription_json: dict = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    summary_json: dict = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    approved_at: datetime | None = Field(default=None)
