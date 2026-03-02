"""Dependency injection for appointment-service."""

import logging
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, create_engine

from src.messaging.messaging_manager import MessagingManager, messaging_manager
from src.repositories.appointment_repository import AppointmentRepository
from src.services.appointment_service import AppointmentService

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please set it in the environment variables.")
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL, echo=True)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session.

    Yields:
        Session: A SQLModel database session.

    """
    with Session(engine) as session:
        yield session


def get_appointment_repository(
    session: Session = Depends(get_db_session),
) -> AppointmentRepository:
    """Dependency injection for AppointmentRepository.

    Args:
        session (Session): The database session.

    Returns:
        AppointmentRepository: An instance of AppointmentRepository.

    """
    return AppointmentRepository(session)


def get_appointment_service(
    repo: AppointmentRepository = Depends(get_appointment_repository),
    messaging: MessagingManager = Depends(lambda: messaging_manager),
) -> AppointmentService:
    """Dependency injection for AppointmentService.

    Args:
        repo (AppointmentRepository): The appointment repository.
        messaging (MessagingManager): The messaging manager.

    Returns:
        AppointmentService: An instance of AppointmentService.

    """
    return AppointmentService(repo, messaging)
