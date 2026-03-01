"""Appointment event message."""

from datetime import date, time

from src.models.db.appointment import AppointmentStatus, TimePreference
from src.models.msg.abstract_message import AbstractMessage

class AppointmentMessage(AbstractMessage):
    """Message published when an appointment event occurs.
    
    Attributes:
        appointment_id (int): Unique identifier of the appointment.
        patient_id (int): Identifier of the patient.
        doctor_id (int): Identifier of the doctor.
        appointment_date (date): Date of the appointment.
        time_preference (TimePreference): AM or PM preference.
        assigned_time (time | None): The assigned time slot.
        status (AppointmentStatus): Current status of the appointment.
    """

    appointment_id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    time_preference: TimePreference
    assigned_time: time | None
    status: AppointmentStatus
    
    @classmethod
    def from_entity(cls, entity: "Appointment") -> "AppointmentMessage": # noqa: F821
        """Create an AppointmentMessage from an Appointment entity.

        Args:
            entity (Appointment): The appointment entity.
        
        Returns:
            AppointmentMessage: The created message instance.
        """
        return cls(
            appointment_id=entity.id,
            patient_id=entity.patient_id,
            doctor_id=entity.doctor_id,
            appointment_date=entity.appointment_date,
            time_preference=entity.time_preference,
            assigned_time=entity.assigned_time,
            status=entity.status,
        )