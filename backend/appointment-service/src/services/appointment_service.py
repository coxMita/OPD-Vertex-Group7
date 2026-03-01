"""Appointment service - business logic and slot assignment."""

import asyncio
import logging
import os
from datetime import date, time

from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_exchanges import (
    APPOINTMENT_CREATED,
    APPOINTMENT_STATUS_CHANGED,
)
from src.models.db.appointment import Appointment, TimePreference
from src.models.dto.appointment_create_request import AppointmentCreateRequest
from src.models.dto.appointment_response import AppointmentResponse
from src.models.dto.appointment_status_update_request import (
    AppointmentStatusUpdateRequest,
)
from src.models.dto.queue_reorder_request import QueueReorderRequest
from src.models.msg.appointment_message import AppointmentMessage
from src.repositories.appointment_repository import AppointmentRepository

logger = logging.getLogger(__name__)

# Slot windows - configurable via environment variables
AM_SLOTS: list[time] = [
    time(h, 0)
    for h in range(
        int(os.getenv("AM_START_HOUR", "8")),
        int(os.getenv("AM_END_HOUR", "12")),
    )
]
PM_SLOTS: list[time] = [
    time(h, 0)
    for h in range(
        int(os.getenv("PM_START_HOUR", "13")),
        int(os.getenv("PM_END_HOUR", "17")),
    )
]

SLOTS: dict[TimePreference, list[time]] = {
    TimePreference.AM: AM_SLOTS,
    TimePreference.PM: PM_SLOTS,
}


class AppointmentService:
    """Service for managing appointments."""

    def __init__(
        self,
        repo: AppointmentRepository,
        messaging: MessagingManager,
    ) -> None:
        """Initialize the AppointmentService.

        Args:
            repo (AppointmentRepository): The appointment repository for database.
            messaging (MessagingManager): The messaging manager for event publishing.

        """
        self._repo = repo
        self._messaging = messaging

    def create_appointment(
        self, request: AppointmentCreateRequest
    ) -> AppointmentResponse:
        """Book a new appointment and assign the next available time slot.

        Args:
            request (AppointmentCreateRequest): the booking request.

        Returns:
            AppointmentResponse: the created appointment details.

        Raises:
            ValueError: If no time slots are available for the given doctor and date.

        """
        assigned_time = self._assign_time_slot(
            request.doctor_id, request.appointment_date, request.time_preference
        )
        appointment = Appointment(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            appointment_date=request.appointment_date,
            time_preference=request.time_preference,
            assigned_time=assigned_time,
            notes=request.notes,
        )
        created = self._repo.create(appointment)
        self._publish_event(created, APPOINTMENT_CREATED)
        return AppointmentResponse.from_entity(created)

    def get_appointment(self, appointment_id: int) -> AppointmentResponse | None:
        """Retrieve an appointment by its ID.

        Args:
            appointment_id (int): The unique identifier of the appointment.

        Returns:
            AppointmentResponse | None: The appointment details if found else None.

        """
        appointment = self._repo.get_by_id(appointment_id)
        return AppointmentResponse.from_entity(appointment) if appointment else None

    def get_queue(
        self, doctor_id: int, appointment_date: date
    ) -> list[AppointmentResponse]:
        """Get the queue of appointments for a specific doctor and date.

        Args:
            doctor_id (int): The unique identifier of the doctor.
            appointment_date (date): The date to filter appointments by.

        Returns:
            list[AppointmentResponse]: Appointments ordered by assigned_time.

        """
        appointments = self._repo.get_by_doctor_and_date(doctor_id, appointment_date)
        return [AppointmentResponse.from_entity(a) for a in appointments]

    def get_patient_appointments(self, patient_id: int) -> list[AppointmentResponse]:
        """Get all appointments for a specific patient.

        Args:
            patient_id (int): The unique identifier of the patient.

        Returns:
            list[AppointmentResponse]: A list of the patient's appointments.

        """
        appointments = self._repo.get_by_patient_id(patient_id)
        return [AppointmentResponse.from_entity(a) for a in appointments]

    def update_status(
        self, appointment_id: int, request: AppointmentStatusUpdateRequest
    ) -> AppointmentResponse | None:
        """Update the status of the appointment.

        Args:
            appointment_id (int): The unique identifier of the appointment.
            request (AppointmentStatusUpdateRequest): The status update request.

        Returns:
            AppointmentResponse | None: The updated appointment if found else None.

        """
        appointment = self._repo.get_by_id(appointment_id)
        if appointment is None:
            return None
        updated = self._repo.update_status(appointment, request.status)
        self._publish(updated, APPOINTMENT_STATUS_CHANGED)
        return AppointmentResponse.from_entity(updated)

    def reorder_queue(
        self, doctor_id: int, appointment_date: date, request: QueueReorderRequest
    ) -> list[AppointmentResponse]:
        """Reorder the queue for a doctor session by reassigning time slots.

        The request contains an ordered list of appointment IDs. The service
        reassigns time slots in order within each preference half (AM/PM).

        Args:
            doctor_id (int): The doctor's ID.
            appointment_date (date): The date of the session.
            request (QueueReorderRequest): Ordered list of appointment IDs.

        Returns:
            list[AppointmentResponse]: The reordered appointments.

        Raises:
            ValueError: If any appointment ID is not found or does not belong
                        to the given doctor and date.

        """
        appointments = self._repo.get_by_doctor_and_date(doctor_id, appointment_date)
        appointments_by_id = {a.id: a for a in appointments}

        if set(request.appointment_ids) != set(appointments_by_id.keys()):
            raise ValueError(
                "appointment_ids must contain exactly the IDs of all active "
                "appointments for this doctor on this date."
            )

        # Split into AM and PM preserving requested order
        am_ids = [
            i
            for i in request.appointment_ids
            if appointments_by_id[i].time_preference == TimePreference.AM
        ]
        pm_ids = [
            i
            for i in request.appointment_ids
            if appointments_by_id[i].time_preference == TimePreference.PM
        ]

        updated: list[Appointment] = []
        for ids, preference in (
            (am_ids, TimePreference.AM),
            (pm_ids, TimePreference.PM),
        ):
            slots = SLOTS[preference]
            for position, appointment_id in enumerate(ids):
                appointment = appointments_by_id[appointment_id]
                appointment.assigned_time = slots[position]
                updated.append(appointment)

        saved = self._repo.reorder(updated)
        return [AppointmentResponse.from_entity(a) for a in saved]

    def _assign_next_slot(
        self,
        doctor_id: int,
        appointment_date: date,
        time_preference: TimePreference,
    ) -> time:
        """Find and return the next available time slot.

        Args:
            doctor_id (int): The doctor's ID.
            appointment_date (date): The requested date.
            time_preference (TimePreference): AM or PM.

        Returns:
            time: The assigned time slot.

        Raises:
            ValueError: If all slots for this preference are taken.

        """
        existing = self._repo.get_by_doctor_date_and_preference(
            doctor_id, appointment_date, time_preference
        )
        taken_times = {a.assigned_time for a in existing}
        available_slots = SLOTS[time_preference]

        for slot in available_slots:
            if slot not in taken_times:
                return slot

        raise ValueError(
            f"No available {time_preference} slots for doctor {doctor_id} "
            f"on {appointment_date}. All {len(available_slots)} slots are taken."
        )

    def _publish(self, appointment: Appointment, exchange: str) -> None:
        """Publish an appointment event to RabbitMQ.

        Args:
            appointment (Appointment): The appointment entity.
            exchange (str): The exchange name to publish to.

        """
        task = asyncio.create_task(
            self._messaging.get_pubsub(exchange).publish(
                AppointmentMessage.from_entity(appointment)
            )
        )
        task.add_done_callback(AppointmentService._log_task_exception)

    @staticmethod
    def _log_task_exception(task: asyncio.Task) -> None:
        """Log exceptions from background publish tasks.

        Args:
            task (asyncio.Task): The completed task.

        """
        try:
            task.result()
        except Exception as e:
            logger.exception("Background publish failed: %s", e)
