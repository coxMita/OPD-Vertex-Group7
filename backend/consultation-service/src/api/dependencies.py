"""Dependency injection for consultation-service."""

import logging
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, create_engine

from src.messaging.messaging_manager import MessagingManager, messaging_manager
from src.repositories.consultation_repository import ConsultationRepository
from src.services.consultation_service import ConsultationService

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


def get_consultation_repository(
    session: Session = Depends(get_db_session),
) -> ConsultationRepository:
    """Dependency injection for ConsultationRepository.

    Args:
        session (Session): The database session.

    Returns:
        ConsultationRepository: An instance of ConsultationRepository.

    """
    return ConsultationRepository(session)


def get_consultation_service(
    repo: ConsultationRepository = Depends(get_consultation_repository),
    messaging: MessagingManager = Depends(lambda: messaging_manager),
) -> ConsultationService:
    """Dependency injection for ConsultationService.

    Args:
        repo (ConsultationRepository): The consultation repository.
        messaging (MessagingManager): The messaging manager.

    Returns:
        ConsultationService: An instance of ConsultationService.

    """
    return ConsultationService(repo, messaging)
