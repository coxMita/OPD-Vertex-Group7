from datetime import date

from pydantic import BaseModel

from src.models.db.appointment import TimePreference


class AppointmentRescheduleRequest(BaseModel):
    """Request DTO for moving an appointment to a different date/time slot."""

    new_date: date
    new_time_preference: TimePreference
    new_hour: int
