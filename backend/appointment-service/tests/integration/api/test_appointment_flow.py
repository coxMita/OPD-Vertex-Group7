"""Integration tests for appointment API flow."""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from testcontainers.postgres import PostgresContainer

from main import app
from src.api.dependencies import get_appointment_repository
from src.repositories.appointment_repository import AppointmentRepository

HTTP_200 = 200
HTTP_201 = 201
HTTP_404 = 404
HTTP_409 = 409
MIN_EXPECTED_APPOINTMENTS = 2


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

    app.dependency_overrides[get_appointment_repository] = override_repo
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── POST /api/v1/appointments


def test_create_appointment_returns_201(client: TestClient) -> None:
    """Creating a valid appointment should return 201."""
    response = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": 1,
            "doctor_id": 1,
            "appointment_date": "2026-03-10",
            "time_preference": "AM",
        },
    )
    assert response.status_code == HTTP_201
    data = response.json()
    assert data["assigned_time"] == "08:00:00"
    assert data["status"] == "SCHEDULED"


def test_create_appointment_assigns_sequential_slots(client: TestClient) -> None:
    """Sequential bookings should get sequential slots."""
    for i in range(2):
        client.post(
            "/api/v1/appointments",
            json={
                "patient_id": i + 1,
                "doctor_id": 2,
                "appointment_date": "2026-03-11",
                "time_preference": "AM",
            },
        )

    response = client.get(
        "/api/v1/appointments/queue/day",
        params={"doctor_id": 2, "appointment_date": "2026-03-11"},
    )
    assert response.status_code == HTTP_200
    slots = [a["assigned_time"] for a in response.json()]
    assert slots == ["08:00:00", "09:00:00"]


def test_create_appointment_returns_409_when_full(client: TestClient) -> None:
    """Should return 409 when all slots are taken."""
    for i in range(4):
        client.post(
            "/api/v1/appointments",
            json={
                "patient_id": i + 1,
                "doctor_id": 3,
                "appointment_date": "2026-03-12",
                "time_preference": "PM",
            },
        )

    response = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": 99,
            "doctor_id": 3,
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
            "patient_id": 1,
            "doctor_id": 4,
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
    response = client.get("/api/v1/appointments/99999")
    assert response.status_code == HTTP_404


# ── PATCH /api/v1/appointments/{id}/status


def test_update_status_returns_updated_appointment(client: TestClient) -> None:
    """Should update and return appointment with new status."""
    create = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": 1,
            "doctor_id": 5,
            "appointment_date": "2026-03-14",
            "time_preference": "AM",
        },
    )
    appointment_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "IN_PROGRESS"},
    )
    assert response.status_code == HTTP_200
    assert response.json()["status"] == "IN_PROGRESS"


def test_update_status_returns_404_when_not_found(client: TestClient) -> None:
    """Should return 404 for non-existent appointment."""
    response = client.patch(
        "/api/v1/appointments/99999/status",
        json={"status": "DONE"},
    )
    assert response.status_code == HTTP_404


# ── GET /api/v1/appointments/patient/{id}


def test_get_patient_appointments_returns_list(client: TestClient) -> None:
    """Should return all appointments for a patient."""
    for i in range(2):
        client.post(
            "/api/v1/appointments",
            json={
                "patient_id": 42,
                "doctor_id": 6 + i,
                "appointment_date": "2026-03-15",
                "time_preference": "AM",
            },
        )
    response = client.get("/api/v1/appointments/patient/42")
    assert response.status_code == HTTP_200
    assert len(response.json()) >= MIN_EXPECTED_APPOINTMENTS
