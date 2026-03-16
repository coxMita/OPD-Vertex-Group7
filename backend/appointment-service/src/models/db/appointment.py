"""Appointment database model."""

import uuid
from datetime import date, time
from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class TimePreference(str, Enum):
    """Time preference for appointment."""

    AM = "AM"
    PM = "PM"


class AppointmentStatus(str, Enum):
    """Status of the appointment."""

    SCHEDULED = "scheduled"
    HANDED_OFF = "handed_off"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Appointment(SQLModel, table=True):
    """Represents a patient appointment."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    time_preference: TimePreference
    assigned_time: time | None = Field(default=None)
    status: AppointmentStatus = Field(
        default=AppointmentStatus.SCHEDULED,
        sa_column=Column(
            SAEnum(AppointmentStatus, values_callable=lambda x: [e.value for e in x]),
            nullable=False,
        ),
    )
    notes: str | None = Field(default=None)
