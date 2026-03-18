"""Pytest configuration and shared fixtures."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.messaging.messaging_manager import MessagingManager
from src.models.db.consultation import Consultation
from src.repositories.consultation_repository import ConsultationRepository
from src.services.consultation_service import ConsultationService


@pytest.fixture
def mock_messaging_manager():
    """Create a mock messaging manager."""
    manager = MagicMock(spec=MessagingManager)
    mock_pubsub = MagicMock()
    manager.get_pubsub.return_value = mock_pubsub
    return manager


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(in_memory_db):
    """Create a database session for testing."""
    with Session(in_memory_db) as session:
        yield session


@pytest.fixture
def consultation_repository(db_session):
    """Create a consultation repository for testing."""
    return ConsultationRepository(db_session)


@pytest.fixture
def consultation_service(consultation_repository, mock_messaging_manager):
    """Create a consultation service for testing."""
    return ConsultationService(consultation_repository, mock_messaging_manager)


@pytest.fixture
def test_consultation_data():
    """Create test consultation data."""
    return {
        "appointment_id": uuid.uuid4(),
        "doctor_id": uuid.uuid4(),
    }


@pytest.fixture
def test_consultation(consultation_repository, test_consultation_data):
    """Create a test consultation in the database."""
    consultation = Consultation(**test_consultation_data)
    return consultation_repository.create(consultation)
