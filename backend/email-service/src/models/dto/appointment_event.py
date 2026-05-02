"""Appointment event DTO for email-service."""

import uuid
from datetime import date, time
from enum import Enum

from pydantic import BaseModel


class AppointmentStatus(str, Enum):
    """Status enum matching appointment-service."""

    SCHEDULED = "scheduled"
    HANDED_OFF = "handed_off"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TimePreference(str, Enum):
    """Preference enum."""

    AM = "AM"
    PM = "PM"


class AppointmentMessage(BaseModel):
    """Message received from appointment-service via fanout exchange."""

    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    time_preference: TimePreference
    assigned_time: time | None
    status: AppointmentStatus
