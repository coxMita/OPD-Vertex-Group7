"""Repository for appointment data access"""

from datetime import date

from sqlmodel import Session, select

from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference

class AppointmentRepository:
    """Repository for managing Appointment entities in the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session (Session): The database session.
        """
        self.session = session
    
    def create(self, appointment: Appointment) -> Appointment:
        """Create a new appointment in the database.

        Args:
            appointment (Appointment): The appointment entity to create.

        Returns:
            Appointment: The created appointment with updated fields.
        """
        self._save_and_refresh(appointment)
        return appointment
    
    def get_by_id(self, appointment_id: int) -> Appointment | None:
        """Retrive and appointment by its ID
        
        Args:
            appointment_id (int): The unique identifier of the appointment.
            
        Returns:
            Appointment | None: The appointment entity if found, otherwise None.
        """
        return self._session.get(Appointment, appointment_id)
    
    def get_by_doctor_and_date(
            self, doctor_id: int, appointment_date: date
    ) -> list[Appointment]:
        """Retrieve appointments for a specific doctor on a given date.

        Args:
            doctor_id (int): The unique identifier of the doctor.
            appointment_date (date): The date to filter appointments by.
        
        Returns:
            list[Appointment]: A list of appointment entities matching the criteria.
        """
        return list(
            self._session.exec(
                select(Appointment)
                .where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.appointment_date == appointment_date,
                    Appointment.status != AppointmentStatus.CANCELLED,
                )
                .order_by(Appointment.assigned_time)
            )
        )
    
    def get_by_doctor_date_and_preference(
            self,
            doctor_id: int,
            appointment_date: date,
            time_preference: TimePreference,
    ) -> list[Appointment]:
        """Retrive appointments for a specific doctor on a given date with a specific time preference.
        
        Args:
            doctor_id (int): The unique identifier of the doctor.
            appointment_date (date): The date to filter appointments by.
            time_preference (TimePreference): The time preference to filter appointments by.
            
        Returns:
            list[Appointment]: A list of appointment entities matching the criteria.
        """
        return list(
            self._session.exec(
                select(Appointment)
                .where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.appointment_date == appointment_date,
                    Appointment.time_preference == time_preference,
                    Appointment.status != AppointmentStatus.CANCELLED,
                )
                .order_by(Appointment.assigned_time)
            )
        )
    
    def get_by_patient_id(self, patient_id: int) -> list[Appointment]:
        """Retrieve appointments for a specific patient.

        Args:
            patient_id (int): The unique identifier of the patient.
        
        Returns:
            list[Appointment]: A list of appointment entities for the patient.
        """
        return list(
            self._session.exec(
                select(Appointment)
                .where(Appointment.patient_id == patient_id) 
            )
        )
    
    def update_status(
            self, appointment: Appointment, status: AppointmentStatus
    ) -> Appointment:
        """Update the status of an appointment.

        Args:
            appointment (Appointment): The appointment entity to update.
            status (AppointmentStatus): The new status to set.

        Returns:
            Appointment: The updated appointment entity.
        """
        appointment.status = status
        self._save_and_refresh(appointment)
        return appointment
    
    def reorder(self, appointments: list[Appointment]) -> list[Appointment]:
        """Reorder a list of appointments based on their assigned time.

        Args:
            appointment (list[Appointment]): The list of appointments to reorder.

        Returns:
            list[Appointment]: The reordered list of appointments.
        """
        for appointment in appointments:
            self._session.add(appointment)
        self._session.commit()
        for appointment in appointments:
            self._session.refresh(appointment)
        return appointments
    
    def _save_and_refresh(self, instance: Appointment) -> None:
        """Save and refresh an istance in the database
        
        Args:
            instance (Appointment): The instance to save and refresh.
            
        """
        self._session.add(instance)
        self._session.commit()
        self._session.refresh(instance)


    