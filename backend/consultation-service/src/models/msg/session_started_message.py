"""Message published when an appointment session window opens."""

import uuid
from datetime import date, time
from enum import Enum

from pydantic import BaseModel

from src.models.msg.abstract_message import AbstractMessage


class TimePreference(str, Enum):
    """Session half-day preference."""

    AM = "AM"
    PM = "PM"


class AppointmentSlot(BaseModel):
    """Details of a single appointment within a session."""

    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    assigned_time: time
    notes: str | None = None


class SessionStartedMessage(AbstractMessage):
    """Published when AM/PM session starts for a doctor on a date."""

    doctor_id: uuid.UUID
    appointment_date: date
    time_preference: TimePreference
    appointments: list[AppointmentSlot]
