"""Appointment database model."""

from datetime import date, time
from enum import Enum

from sqlmodel import Field, SQLModel


class TimePreference(str, Enum):
    """Time preference for appointment."""

    AM = "AM"
    PM = "PM"


class AppointmentStatus(str, Enum):
    """Status of an appointment."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Appointment(SQLModel, table=True):
    """Represents a patient appointment."""

    id: int | None = Field(default=None, primary_key=True)
    patient_id: int
    doctor_id: int
    appointment_date: date
    time_preference: TimePreference
    assigned_time: time | None = Field(default=None)
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    notes: str | None = Field(default=None)
