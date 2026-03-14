"""Message published when an AM or PM session window opens for a doctor."""

import uuid
from datetime import date, time

from pydantic import BaseModel

from src.models.db.appointment import TimePreference
from src.models.msg.abstract_message import AbstractMessage


class AppointmentSlot(BaseModel):
    """Details of a single appointment within a session.

    Attributes:
        appointment_id (uuid.UUID): Unique identifier of the appointment.
        patient_id (uuid.UUID): Identifier of the patient.
        assigned_time (time): The assigned time slot.
        notes (str | None): Optional notes for the appointment.

    """

    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    assigned_time: time
    notes: str | None = None


class SessionStartedMessage(AbstractMessage):
    """Published when the AM or PM window starts for a doctor on a given date.

    Attributes:
        doctor_id (uuid.UUID): The doctor whose session is starting.
        appointment_date (date): The date of the session.
        time_preference (TimePreference): AM or PM.
        appointments (list[AppointmentSlot]): Ordered list of appointments
            with full details, sorted by assigned_time.

    """

    doctor_id: uuid.UUID
    appointment_date: date
    time_preference: TimePreference
    appointments: list[AppointmentSlot]
