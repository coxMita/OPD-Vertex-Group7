"""APScheduler jobs that fire when AM/PM session windows open."""

import logging
import os
from collections import defaultdict
from datetime import date, time
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_exchanges import APPOINTMENT_SESSION_STARTED
from src.models.db.appointment import AppointmentStatus, TimePreference
from src.models.msg.session_started_message import (
    AppointmentSlot,
    SessionStartedMessage,
)
from src.repositories.appointment_repository import AppointmentRepository

logger = logging.getLogger(__name__)

_am_notify = time(int(os.getenv("AM_NOTIFY_HOUR", "7")), 0)
_pm_notify = time(int(os.getenv("PM_NOTIFY_HOUR", "12")), 0)


async def _notify_session(
    repo: AppointmentRepository,
    messaging: MessagingManager,
    time_preference: TimePreference,
) -> None:
    today = date.today()
    appointments = repo.get_by_date_and_preference(today, time_preference)

    if not appointments:
        logger.info(
            "No %s appointments today (%s), skipping.", time_preference.value, today
        )
        return

    by_doctor: dict = defaultdict(list)
    for appt in appointments:
        by_doctor[appt.doctor_id].append(appt)  # stochează entitatea, nu doar id-ul

    pubsub = messaging.get_pubsub(APPOINTMENT_SESSION_STARTED)
    for doctor_id, doctor_appointments in by_doctor.items():
        slots = [
            AppointmentSlot(
                appointment_id=appt.id,
                patient_id=appt.patient_id,
                assigned_time=appt.assigned_time,
                notes=appt.notes,
            )
            for appt in doctor_appointments
        ]

        msg = SessionStartedMessage(
            doctor_id=doctor_id,
            appointment_date=today,
            time_preference=time_preference,
            appointments=slots,
        )
        await pubsub.publish(msg)
        logger.info(
            "Published session_started | doctor=%s | %s | %s | %d appointments",
            doctor_id,
            time_preference.value,
            today,
            len(slots),
        )

        for appt in doctor_appointments:
            repo.update_status(appt, AppointmentStatus.HANDED_OFF)
            logger.info("Marked appointment %s as HANDED_OFF", appt.id)


def build_scheduler(
    get_repo: Callable[[], AppointmentRepository],
    messaging: MessagingManager,
) -> AsyncIOScheduler:
    """Build and return a configured AsyncIOScheduler.

    Schedules two daily cron jobs — one at AM_START, one at PM_START.

    Args:
        get_repo (Callable[[], AppointmentRepository]): Factory that returns
            a fresh AppointmentRepository with its own Session each call.
        messaging (MessagingManager): The messaging manager.

    Returns:
        AsyncIOScheduler: Configured scheduler, not yet started.

    """
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        func=lambda: _notify_session(get_repo(), messaging, TimePreference.AM),
        trigger="cron",
        hour=_am_notify.hour,
        minute=_am_notify.minute,
        id="notify_am_session",
        replace_existing=True,
    )

    scheduler.add_job(
        func=lambda: _notify_session(get_repo(), messaging, TimePreference.PM),
        trigger="cron",
        hour=_pm_notify.hour,
        minute=_pm_notify.minute,
        id="notify_pm_session",
        replace_existing=True,
    )

    logger.info(
        "Scheduler configured: AM job at %s, PM job at %s", _am_notify, _pm_notify
    )
    return scheduler
