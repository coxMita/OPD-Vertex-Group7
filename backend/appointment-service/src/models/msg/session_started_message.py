"""Message published when an AM or PM session window opens for a doctor."""

import uuid
from datetime import date

from src.models.db.appointment import TimePreference
from src.models.msg.abstract_message import AbstractMessage


class SessionStartedMessage(AbstractMessage):
    """Published when the AM or PM window starts for a doctor on a given date.

    Attributes:
        doctor_id (uuid.UUID): The doctor whose session is starting.
        appointment_date (date): The date of the session.
        time_preference (TimePreference): AM or PM.
        appointment_ids (list[uuid.UUID]): IDs of all active appointments
            in this session window, ordered by assigned_time.

    """

    doctor_id: uuid.UUID
    appointment_date: date
    time_preference: TimePreference
    appointment_ids: list[uuid.UUID]
