"""Repository for appointment data access."""

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
        self._session = session

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
        """Retrieve an appointment by its ID.

        Args:
            appointment_id (int): The ID of the appointment.

        Returns:
            Appointment | None: The appointment if found, else None.

        """
        return self._session.get(Appointment, appointment_id)

    def get_by_doctor_and_date(
        self, doctor_id: int, appointment_date: date
    ) -> list[Appointment]:
        """Retrieve all appointments for a doctor on a specific date.

        Args:
            doctor_id (int): The ID of the doctor.
            appointment_date (date): The date to query.

        Returns:
            list[Appointment]: List of appointments ordered by assigned_time.

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
        """Retrieve appointments for a doctor on a date filtered by AM/PM preference.

        Args:
            doctor_id (int): The ID of the doctor.
            appointment_date (date): The date to query.
            time_preference (TimePreference): AM or PM preference.

        Returns:
            list[Appointment]: List of matching appointments ordered by assigned_time.

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
        """Retrieve all appointments for a specific patient.

        Args:
            patient_id (int): The ID of the patient.

        Returns:
            list[Appointment]: List of the patient's appointments.

        """
        return list(
            self._session.exec(
                select(Appointment).where(Appointment.patient_id == patient_id)
            )
        )

    def update_status(
        self, appointment: Appointment, status: AppointmentStatus
    ) -> Appointment:
        """Update the status of an appointment.

        Args:
            appointment (Appointment): The appointment entity to update.
            status (AppointmentStatus): The new status.

        Returns:
            Appointment: The updated appointment.

        """
        appointment.status = status
        self._save_and_refresh(appointment)
        return appointment

    def reorder(self, appointments: list[Appointment]) -> list[Appointment]:
        """Persist a reordered list of appointments with updated assigned times.

        Args:
            appointments (list[Appointment]): Appointments with updated assigned_time.

        Returns:
            list[Appointment]: The updated appointments.

        """
        for appointment in appointments:
            self._session.add(appointment)
        self._session.commit()
        for appointment in appointments:
            self._session.refresh(appointment)
        return appointments

    def _save_and_refresh(self, instance: Appointment) -> None:
        """Save and refresh an instance in the database.

        Args:
            instance (Appointment): The appointment instance to save and refresh.

        """
        self._session.add(instance)
        self._session.commit()
        self._session.refresh(instance)
