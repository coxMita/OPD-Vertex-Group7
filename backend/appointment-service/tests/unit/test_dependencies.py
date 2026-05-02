"""Unit tests for API dependency factories."""

from contextlib import suppress
from unittest.mock import MagicMock, patch

from src.api import dependencies
from src.messaging.messaging_manager import messaging_manager
from src.repositories.appointment_repository import AppointmentRepository
from src.services.appointment_service import AppointmentService


def test_get_db_session_yields_session() -> None:
    """The database dependency should yield a session and close it afterward."""
    session = MagicMock()
    session_context = MagicMock()
    session_context.__enter__.return_value = session
    with patch("src.api.dependencies.Session", return_value=session_context) as cls:
        generator = dependencies.get_db_session()
        yielded = next(generator)
        try:
            assert yielded == session
            cls.assert_called_once_with(dependencies.engine)
        finally:
            with suppress(StopIteration):
                next(generator)


def test_get_appointment_repository_wraps_session() -> None:
    """The repository dependency should wrap the provided session."""
    session = MagicMock()

    repo = dependencies.get_appointment_repository(session)

    assert isinstance(repo, AppointmentRepository)
    assert repo._session == session


def test_get_appointment_service_wraps_repo_and_messaging() -> None:
    """The service dependency should wrap repository and messaging dependencies."""
    repo = MagicMock(spec=AppointmentRepository)

    service = dependencies.get_appointment_service(repo, messaging_manager)

    assert isinstance(service, AppointmentService)
    assert service._repo == repo
    assert service._messaging == messaging_manager
