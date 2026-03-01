"""DTO for creating an appointment."""

from datetime import date

from pydantic import BaseModel

from src.models.db.appointment import TimePreference


class AppointmentCreateRequest(BaseModel):
    """Request DTO for booking an appointment.

    The patient provides date, doctor and AM/PM preference.
    The assigned time slot is determined automatically by the service.
    """

    patient_id: int
    doctor_id: int
    appointment_date: date
    time_preference: TimePreference
    notes: str | None = None