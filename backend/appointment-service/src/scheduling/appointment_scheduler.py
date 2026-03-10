"""APScheduler jobs that fire when AM/PM session windows open."""

import logging
import os
from collections import defaultdict
from datetime import date, time
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_exchanges import APPOINTMENT_SESSION_STARTED
from src.models.db.appointment import TimePreference
from src.models.msg.session_started_message import SessionStartedMessage
from src.repositories.appointment_repository import AppointmentRepository

logger = logging.getLogger(__name__)

AM_START = time(int(os.getenv("AM_START_HOUR", "8")), 0)
PM_START = time(int(os.getenv("PM_START_HOUR", "13")), 0)


async def _notify_session(
    repo: AppointmentRepository,
    messaging: MessagingManager,
    time_preference: TimePreference,
) -> None:
    """Find all doctors with appointments today in this window and notify each.

    Groups appointments by doctor_id and publishes one SessionStartedMessage
    per doctor containing the ordered list of their appointment IDs.

    Args:
        repo (AppointmentRepository): A fresh repository instance for this call.
        messaging (MessagingManager): The messaging manager.
        time_preference (TimePreference): AM or PM.

    """
    today = date.today()
    appointments = repo.get_by_date_and_preference(today, time_preference)

    if not appointments:
        logger.info(
            "No %s appointments today (%s), skipping.", time_preference.value, today
        )
        return

    # Group appointment IDs by doctor, preserving assigned_time order
    by_doctor: dict[str, list] = defaultdict(list)
    for appt in appointments:
        by_doctor[appt.doctor_id].append(appt.id)

    pubsub = messaging.get_pubsub(APPOINTMENT_SESSION_STARTED)
    for doctor_id, appointment_ids in by_doctor.items():
        msg = SessionStartedMessage(
            doctor_id=doctor_id,
            appointment_date=today,
            time_preference=time_preference,
            appointment_ids=appointment_ids,
        )
        await pubsub.publish(msg)
        logger.info(
            "Published session_started | doctor=%s | %s | %s | appointments=%s",
            doctor_id,
            time_preference.value,
            today,
            appointment_ids,
        )


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
        hour=AM_START.hour,
        minute=AM_START.minute,
        id="notify_am_session",
        replace_existing=True,
    )

    scheduler.add_job(
        func=lambda: _notify_session(get_repo(), messaging, TimePreference.PM),
        trigger="cron",
        hour=PM_START.hour,
        minute=PM_START.minute,
        id="notify_pm_session",
        replace_existing=True,
    )

    logger.info("Scheduler configured: AM job at %s, PM job at %s", AM_START, PM_START)
    return scheduler
