"""DTO for appointment responses."""

from datetime import date, time

from pydantic import BaseModel

from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference


class AppointmentResponse(BaseModel):
    """Response DTO for an appointment."""

    id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    time_preference: TimePreference
    assigned_time: time | None
    status: AppointmentStatus
    notes: str | None

    @classmethod
    def from_entity(cls, entity: Appointment) -> "AppointmentResponse":
        """Create an AppointmentResponse from an Appointment entity.

        Args:
            entity (Appointment): The appointment entity.

        Returns:
            AppointmentResponse: The response DTO.

        """
        return cls(
            id=entity.id,
            patient_id=entity.patient_id,
            doctor_id=entity.doctor_id,
            appointment_date=entity.appointment_date,
            time_preference=entity.time_preference,
            assigned_time=entity.assigned_time,
            status=entity.status,
            notes=entity.notes,
        )