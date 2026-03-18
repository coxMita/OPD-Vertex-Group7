"""Integration tests for appointment API flow."""

import uuid
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from testcontainers.postgres import PostgresContainer

from main import app
from src.api.dependencies import get_appointment_repository
from src.messaging.messaging_manager import MessagingManager
from src.repositories.appointment_repository import AppointmentRepository

HTTP_200 = 200
HTTP_201 = 201
HTTP_404 = 404
HTTP_409 = 409
MIN_EXPECTED_APPOINTMENTS = 2

PATIENT_ID_1 = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
PATIENT_ID_2 = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))
PATIENT_ID_42 = str(uuid.UUID("00000000-0000-0000-0000-000000000042"))
PATIENT_ID_99 = str(uuid.UUID("00000000-0000-0000-0000-000000000099"))

DOCTOR_ID_1 = str(uuid.UUID("00000000-0000-0000-0001-000000000001"))
DOCTOR_ID_2 = str(uuid.UUID("00000000-0000-0000-0001-000000000002"))
DOCTOR_ID_3 = str(uuid.UUID("00000000-0000-0000-0001-000000000003"))
DOCTOR_ID_4 = str(uuid.UUID("00000000-0000-0000-0001-000000000004"))
DOCTOR_ID_5 = str(uuid.UUID("00000000-0000-0000-0001-000000000005"))
DOCTOR_ID_6 = str(uuid.UUID("00000000-0000-0000-0001-000000000006"))
DOCTOR_ID_7 = str(uuid.UUID("00000000-0000-0000-0001-000000000007"))


class DummyMessaging:
    """Stub for MessagingManager."""

    @staticmethod
    def get_pubsub(exchange_name: str) -> "DummyPubSub":
        """Return a dummy pubsub."""
        return DummyPubSub()


class DummyPubSub:
    """Stub for PubSubFacade."""

    async def publish(self, message: object) -> None:
        """Do nothing."""


@pytest.fixture(scope="module")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a Postgres testcontainer for the module."""
    container = PostgresContainer("postgres:17-alpine")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def db_session(postgres_container: PostgresContainer) -> Generator[Session, None, None]:
    """Create tables and yield a session."""
    db_url = postgres_container.get_connection_url()
    engine = create_engine(db_url, echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Return a TestClient with overridden dependencies."""

    def override_repo() -> AppointmentRepository:
        return AppointmentRepository(db_session)

    mock_messaging = MagicMock(spec=MessagingManager)
    mock_messaging.start_all = AsyncMock()
    mock_messaging.stop_all = AsyncMock()
    mock_messaging.get_pubsub = MagicMock(return_value=MagicMock(publish=AsyncMock()))

    app.dependency_overrides[get_appointment_repository] = override_repo

    with (
        patch("main.messaging_manager", mock_messaging),
        TestClient(app, raise_server_exceptions=False) as c,
    ):
        yield c

    app.dependency_overrides.clear()


# ── POST /api/v1/appointments


def test_create_appointment_returns_201(client: TestClient) -> None:
    """Creating a valid appointment should return 201."""
    response = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": PATIENT_ID_1,
            "doctor_id": DOCTOR_ID_1,
            "appointment_date": "2026-03-10",
            "time_preference": "AM",
        },
    )
    assert response.status_code == HTTP_201
    data = response.json()
    assert data["assigned_time"] == "08:00:00"
    assert data["status"] == "scheduled"


def test_create_appointment_assigns_sequential_slots(client: TestClient) -> None:
    """Sequential bookings should get sequential slots."""
    patient_ids = [PATIENT_ID_1, PATIENT_ID_2]
    for patient_id in patient_ids:
        client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": DOCTOR_ID_2,
                "appointment_date": "2026-03-11",
                "time_preference": "AM",
            },
        )

    response = client.get(
        "/api/v1/appointments/queue/day",
        params={"doctor_id": DOCTOR_ID_2, "appointment_date": "2026-03-11"},
    )
    assert response.status_code == HTTP_200
    slots = [a["assigned_time"] for a in response.json()]
    assert slots == ["08:00:00", "09:00:00"]


def test_create_appointment_returns_409_when_full(client: TestClient) -> None:
    """Should return 409 when all slots are taken."""
    patient_ids = [
        str(uuid.UUID(f"00000000-0000-0000-0000-{i:012d}")) for i in range(1, 5)
    ]
    for patient_id in patient_ids:
        client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": DOCTOR_ID_3,
                "appointment_date": "2026-03-12",
                "time_preference": "PM",
            },
        )

    response = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": PATIENT_ID_99,
            "doctor_id": DOCTOR_ID_3,
            "appointment_date": "2026-03-12",
            "time_preference": "PM",
        },
    )
    assert response.status_code == HTTP_409


# ── GET /api/v1/appointments/{id}


def test_get_appointment_returns_200(client: TestClient) -> None:
    """Should return appointment details."""
    create = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": PATIENT_ID_1,
            "doctor_id": DOCTOR_ID_4,
            "appointment_date": "2026-03-13",
            "time_preference": "AM",
        },
    )
    appointment_id = create.json()["id"]
    response = client.get(f"/api/v1/appointments/{appointment_id}")
    assert response.status_code == HTTP_200
    assert response.json()["id"] == appointment_id


def test_get_appointment_returns_404(client: TestClient) -> None:
    """Should return 404 for non-existent appointment."""
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/appointments/{random_uuid}")
    assert response.status_code == HTTP_404


# ── PATCH /api/v1/appointments/{id}/status


def test_update_status_returns_updated_appointment(client: TestClient) -> None:
    """Should update and return appointment with new status."""
    create = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": PATIENT_ID_1,
            "doctor_id": DOCTOR_ID_5,
            "appointment_date": "2026-03-14",
            "time_preference": "AM",
        },
    )
    appointment_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "handed_off"},
    )
    assert response.status_code == HTTP_200
    assert response.json()["status"] == "handed_off"


def test_update_status_returns_404_when_not_found(client: TestClient) -> None:
    """Should return 404 for non-existent appointment."""
    random_uuid = str(uuid.uuid4())
    response = client.patch(
        f"/api/v1/appointments/{random_uuid}/status",
        json={"status": "completed"},
    )
    assert response.status_code == HTTP_404


# ── GET /api/v1/appointments/patient/{id}


def test_get_patient_appointments_returns_list(client: TestClient) -> None:
    """Should return all appointments for a patient."""
    for doctor_id in [DOCTOR_ID_6, DOCTOR_ID_7]:
        client.post(
            "/api/v1/appointments",
            json={
                "patient_id": PATIENT_ID_42,
                "doctor_id": doctor_id,
                "appointment_date": "2026-03-15",
                "time_preference": "AM",
            },
        )
    response = client.get(f"/api/v1/appointments/patient/{PATIENT_ID_42}")
    assert response.status_code == HTTP_200
    assert len(response.json()) >= MIN_EXPECTED_APPOINTMENTS
