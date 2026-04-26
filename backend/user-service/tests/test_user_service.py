"""Tests for user-service: repositories, services, and API routes."""

from datetime import date
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_doctor_service, get_patient_service
from src.api.routes.doctor_routes import router as doctor_router
from src.api.routes.patient_routes import router as patient_router
from src.models.db.doctor import Doctor
from src.models.db.patient import Patient
from src.models.dto.doctor_dto import DoctorDTO
from src.models.dto.patient_create_request import PatientCreateRequest
from src.models.dto.patient_dto import PatientDTO
from src.repositories.doctor_repository import DoctorRepository
from src.repositories.patient_repository import PatientRepository
from src.services.doctor_service import DoctorService
from src.services.patient_service import PatientService

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

DOCTOR_ID: UUID = uuid4()
KEYCLOAK_ID: UUID = uuid4()
PATIENT_ID: UUID = uuid4()

PHONE_NUMBER: int = 4512345678
DOCTOR_COUNT: int = 2

HTTP_200 = 200
HTTP_201 = 201
HTTP_404 = 404
HTTP_422 = 422


# ─────────────────────────────────────────────
# Factories
# ─────────────────────────────────────────────


def make_doctor(**kwargs: object) -> Doctor:
    """Create a Doctor instance with sensible defaults."""
    defaults: dict[str, object] = {
        "doctor_id": DOCTOR_ID,
        "full_name": "Anders Hansen",
        "department_name": "General Practice",
        "email": "a.hansen@opd-vertex.dk",
        "keycloak_id": KEYCLOAK_ID,
    }
    defaults.update(kwargs)
    return Doctor(**defaults)


def make_patient(**kwargs: object) -> Patient:
    """Create a Patient instance with sensible defaults."""
    defaults: dict[str, object] = {
        "patient_id": PATIENT_ID,
        "first_name": "Maria",
        "last_name": "Andersen",
        "date_of_birth": date(2000, 1, 15),
        "gender": "female",
        "phone_number": PHONE_NUMBER,
        "email": "maria@example.com",
    }
    defaults.update(kwargs)
    return Patient(**defaults)


def make_patient_dto(**kwargs: object) -> PatientDTO:
    """Create a PatientDTO with sensible defaults."""
    defaults: dict[str, object] = {
        "patient_id": PATIENT_ID,
        "first_name": "Maria",
        "last_name": "Andersen",
        "date_of_birth": date(2000, 1, 15),
        "gender": "female",
        "phone_number": PHONE_NUMBER,
        "email": "maria@example.com",
    }
    defaults.update(kwargs)
    return PatientDTO(**defaults)


def make_doctor_dto(**kwargs: object) -> DoctorDTO:
    """Create a DoctorDTO with sensible defaults."""
    defaults: dict[str, object] = {
        "doctor_id": DOCTOR_ID,
        "full_name": "Anders Hansen",
        "department_name": "General Practice",
        "email": "a.hansen@opd-vertex.dk",
        "keycloak_id": KEYCLOAK_ID,
    }
    defaults.update(kwargs)
    return DoctorDTO(**defaults)


def make_test_app_user() -> tuple[FastAPI, MagicMock, MagicMock]:
    """Build a test FastAPI app with mocked services."""
    mock_doctor_service = MagicMock(spec=DoctorService)
    mock_patient_service = MagicMock(spec=PatientService)

    app = FastAPI()
    app.include_router(doctor_router)
    app.include_router(patient_router)
    app.dependency_overrides[get_doctor_service] = lambda: mock_doctor_service
    app.dependency_overrides[get_patient_service] = lambda: mock_patient_service

    return app, mock_doctor_service, mock_patient_service


# ─────────────────────────────────────────────
# DoctorRepository
# ─────────────────────────────────────────────


class TestDoctorRepository:
    """Unit tests for DoctorRepository."""

    def setup_method(self) -> None:
        """Set up mocked session and repository."""
        self.session = MagicMock()
        self.repo = DoctorRepository(self.session)

    def test_get_by_id_found(self) -> None:
        """Returns doctor when found by ID."""
        doctor = make_doctor()
        self.session.get.return_value = doctor
        result = self.repo.get_by_id(DOCTOR_ID)
        self.session.get.assert_called_once_with(Doctor, DOCTOR_ID)
        assert result == doctor

    def test_get_by_id_not_found(self) -> None:
        """Returns None when doctor ID does not exist."""
        self.session.get.return_value = None
        result = self.repo.get_by_id(uuid4())
        assert result is None

    def test_get_all_by_department_returns_list(self) -> None:
        """Returns list of doctors for a given department."""
        doctors = [
            make_doctor(),
            make_doctor(doctor_id=uuid4(), full_name="Sofia Popa"),
        ]
        exec_result = MagicMock()
        exec_result.all.return_value = doctors
        self.session.exec.return_value = exec_result
        result = self.repo.get_all_by_department("General Practice")
        assert result == doctors
        assert len(result) == DOCTOR_COUNT

    def test_get_all_by_department_empty(self) -> None:
        """Returns empty list when no doctors in department."""
        exec_result = MagicMock()
        exec_result.all.return_value = []
        self.session.exec.return_value = exec_result
        result = self.repo.get_all_by_department("Psychiatry")
        assert result == []

    def test_get_by_keycloak_id_found(self) -> None:
        """Returns doctor when found by Keycloak ID."""
        doctor = make_doctor()
        exec_result = MagicMock()
        exec_result.first.return_value = doctor
        self.session.exec.return_value = exec_result
        result = self.repo.get_by_keycloak_id(KEYCLOAK_ID)
        assert result == doctor

    def test_get_by_keycloak_id_not_found(self) -> None:
        """Returns None when doctor Keycloak ID does not exist."""
        exec_result = MagicMock()
        exec_result.first.return_value = None
        self.session.exec.return_value = exec_result
        result = self.repo.get_by_keycloak_id(uuid4())
        assert result is None


# ─────────────────────────────────────────────
# PatientRepository
# ─────────────────────────────────────────────


class TestPatientRepository:
    """Unit tests for PatientRepository."""

    def setup_method(self) -> None:
        """Set up mocked session and repository."""
        self.session = MagicMock()
        self.repo = PatientRepository(self.session)

    def test_create_patient(self) -> None:
        """Creates patient and calls add/commit/refresh."""
        patient = make_patient()
        result = self.repo.create(patient)
        self.session.add.assert_called_once_with(patient)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(patient)
        assert result == patient

    def test_get_by_id_found(self) -> None:
        """Returns patient when found by ID."""
        patient = make_patient()
        self.session.get.return_value = patient
        result = self.repo.get_by_id(PATIENT_ID)
        self.session.get.assert_called_once_with(Patient, PATIENT_ID)
        assert result == patient

    def test_get_by_id_not_found(self) -> None:
        """Returns None when patient ID does not exist."""
        self.session.get.return_value = None
        result = self.repo.get_by_id(uuid4())
        assert result is None

    def test_get_by_email_found(self) -> None:
        """Returns patient when found by email."""
        patient = make_patient()
        exec_result = MagicMock()
        exec_result.first.return_value = patient
        self.session.exec.return_value = exec_result
        result = self.repo.get_by_email("maria@example.com")
        assert result == patient

    def test_get_by_email_not_found(self) -> None:
        """Returns None when email does not match any patient."""
        exec_result = MagicMock()
        exec_result.first.return_value = None
        self.session.exec.return_value = exec_result
        result = self.repo.get_by_email("nobody@example.com")
        assert result is None


# ─────────────────────────────────────────────
# DoctorService
# ─────────────────────────────────────────────


class TestDoctorService:
    """Unit tests for DoctorService."""

    def setup_method(self) -> None:
        """Set up mocked repository and service."""
        self.repo = MagicMock(spec=DoctorRepository)
        self.service = DoctorService(self.repo)

    def test_get_doctors_by_department_returns_dtos(self) -> None:
        """Returns list of DoctorDTOs for a given department."""
        doctors = [
            make_doctor(),
            make_doctor(doctor_id=uuid4(), full_name="Sofia Popa"),
        ]
        self.repo.get_all_by_department.return_value = doctors
        result = self.service.get_doctors_by_department("General Practice")
        assert len(result) == DOCTOR_COUNT
        assert all(isinstance(r, DoctorDTO) for r in result)
        assert result[0].full_name == "Anders Hansen"
        assert result[1].full_name == "Sofia Popa"

    def test_get_doctors_by_department_empty(self) -> None:
        """Returns empty list when department has no doctors."""
        self.repo.get_all_by_department.return_value = []
        result = self.service.get_doctors_by_department("Psychiatry")
        assert result == []

    def test_get_doctor_found(self) -> None:
        """Returns DoctorDTO when doctor exists."""
        self.repo.get_by_id.return_value = make_doctor()
        result = self.service.get_doctor(DOCTOR_ID)
        assert isinstance(result, DoctorDTO)
        assert result.doctor_id == DOCTOR_ID
        assert result.full_name == "Anders Hansen"
        assert result.department_name == "General Practice"

    def test_get_doctor_not_found(self) -> None:
        """Returns None when doctor does not exist."""
        self.repo.get_by_id.return_value = None
        result = self.service.get_doctor(uuid4())
        assert result is None

    def test_get_doctor_dto_fields_match(self) -> None:
        """All DTO fields correctly map from entity."""
        doctor = make_doctor(email="test@opd.dk")
        self.repo.get_by_id.return_value = doctor
        result = self.service.get_doctor(DOCTOR_ID)
        assert result is not None
        assert result.email == "test@opd.dk"
        assert result.keycloak_id == KEYCLOAK_ID

    def test_get_doctor_by_keycloak_id_found(self) -> None:
        """Returns DoctorDTO when doctor exists by Keycloak ID."""
        self.repo.get_by_keycloak_id.return_value = make_doctor()
        result = self.service.get_doctor_by_keycloak_id(KEYCLOAK_ID)
        assert isinstance(result, DoctorDTO)
        assert result.keycloak_id == KEYCLOAK_ID

    def test_get_doctor_by_keycloak_id_not_found(self) -> None:
        """Returns None when Keycloak ID does not match a doctor."""
        self.repo.get_by_keycloak_id.return_value = None
        result = self.service.get_doctor_by_keycloak_id(uuid4())
        assert result is None


# ─────────────────────────────────────────────
# PatientService
# ─────────────────────────────────────────────


class TestPatientService:
    """Unit tests for PatientService."""

    def setup_method(self) -> None:
        """Set up mocked repository and service."""
        self.repo = MagicMock(spec=PatientRepository)
        self.service = PatientService(self.repo)

    def _make_request(self, **kwargs: object) -> PatientCreateRequest:
        """Build a PatientCreateRequest with defaults."""
        defaults: dict[str, object] = {
            "first_name": "Maria",
            "last_name": "Andersen",
            "date_of_birth": date(2000, 1, 15),
            "gender": "female",
            "phone_number": PHONE_NUMBER,
            "email": "maria@example.com",
        }
        defaults.update(kwargs)
        return PatientCreateRequest(**defaults)

    def test_find_or_create_returns_existing(self) -> None:
        """Returns existing patient without calling create."""
        existing = make_patient()
        self.repo.get_by_email.return_value = existing
        request = self._make_request()
        result = self.service.find_or_create_patient(request)
        self.repo.create.assert_not_called()
        assert isinstance(result, PatientDTO)
        assert result.patient_id == PATIENT_ID

    def test_find_or_create_creates_new_when_not_found(self) -> None:
        """Creates and returns new patient when email not found."""
        self.repo.get_by_email.return_value = None
        new_patient = make_patient()
        self.repo.create.return_value = new_patient
        request = self._make_request()
        result = self.service.find_or_create_patient(request)
        self.repo.create.assert_called_once()
        assert isinstance(result, PatientDTO)
        assert result.first_name == "Maria"

    def test_find_or_create_passes_correct_fields(self) -> None:
        """DTO fields match the created patient entity."""
        self.repo.get_by_email.return_value = None
        new_patient = make_patient(first_name="Lars", email="lars@example.com")
        self.repo.create.return_value = new_patient
        request = self._make_request(first_name="Lars", email="lars@example.com")
        result = self.service.find_or_create_patient(request)
        assert result.first_name == "Lars"
        assert result.email == "lars@example.com"

    def test_get_patient_found(self) -> None:
        """Returns PatientDTO when patient exists."""
        self.repo.get_by_id.return_value = make_patient()
        result = self.service.get_patient(PATIENT_ID)
        assert isinstance(result, PatientDTO)
        assert result.patient_id == PATIENT_ID

    def test_get_patient_not_found(self) -> None:
        """Returns None when patient does not exist."""
        self.repo.get_by_id.return_value = None
        result = self.service.get_patient(uuid4())
        assert result is None

    def test_get_patient_by_email_found(self) -> None:
        """Returns PatientDTO when email matches."""
        self.repo.get_by_email.return_value = make_patient()
        result = self.service.get_patient_by_email("maria@example.com")
        assert isinstance(result, PatientDTO)
        assert result.email == "maria@example.com"

    def test_get_patient_by_email_not_found(self) -> None:
        """Returns None when email has no match."""
        self.repo.get_by_email.return_value = None
        result = self.service.get_patient_by_email("nobody@example.com")
        assert result is None

    def test_get_patient_dto_all_fields(self) -> None:
        """All PatientDTO fields correctly map from entity."""
        self.repo.get_by_id.return_value = make_patient()
        result = self.service.get_patient(PATIENT_ID)
        assert result is not None
        assert result.first_name == "Maria"
        assert result.last_name == "Andersen"
        assert result.gender == "female"
        assert result.phone_number == PHONE_NUMBER
        assert result.date_of_birth == date(2000, 1, 15)


# ─────────────────────────────────────────────
# API Routes — Doctor
# ─────────────────────────────────────────────


class TestDoctorRoutes:
    """Integration tests for doctor API routes."""

    def setup_method(self) -> None:
        """Set up test client with mocked services."""
        self.app, self.doctor_svc, self.patient_svc = make_test_app_user()
        self.client = TestClient(self.app)

    def test_get_doctors_by_department_200(self) -> None:
        """Returns 200 with doctor list for a valid department."""
        self.doctor_svc.get_doctors_by_department.return_value = [make_doctor_dto()]
        resp = self.client.get("/api/v1/user/doctor/General Practice/doctors")
        assert resp.status_code == HTTP_200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["full_name"] == "Anders Hansen"
        assert data[0]["department_name"] == "General Practice"

    def test_get_doctors_by_department_empty(self) -> None:
        """Returns 200 with empty list when department has no doctors."""
        self.doctor_svc.get_doctors_by_department.return_value = []
        resp = self.client.get("/api/v1/user/doctor/Psychiatry/doctors")
        assert resp.status_code == HTTP_200
        assert resp.json() == []

    def test_get_doctors_calls_service_with_correct_department(self) -> None:
        """Passes department name correctly to service."""
        self.doctor_svc.get_doctors_by_department.return_value = []
        self.client.get("/api/v1/user/doctor/Cardiology/doctors")
        self.doctor_svc.get_doctors_by_department.assert_called_once_with("Cardiology")

    def test_get_doctor_by_id_200(self) -> None:
        """Returns 200 with doctor data for valid ID."""
        self.doctor_svc.get_doctor.return_value = make_doctor_dto()
        resp = self.client.get(f"/api/v1/user/doctors/{DOCTOR_ID}")
        assert resp.status_code == HTTP_200
        assert resp.json()["doctor_id"] == str(DOCTOR_ID)

    def test_get_doctor_by_id_404(self) -> None:
        """Returns 404 when doctor ID not found."""
        self.doctor_svc.get_doctor.return_value = None
        resp = self.client.get(f"/api/v1/user/doctors/{uuid4()}")
        assert resp.status_code == HTTP_404
        assert resp.json()["message"] == "Doctor not found"

    def test_get_doctor_response_fields(self) -> None:
        """Response includes all expected doctor fields."""
        self.doctor_svc.get_doctor.return_value = make_doctor_dto()
        resp = self.client.get(f"/api/v1/user/doctors/{DOCTOR_ID}")
        data = resp.json()
        assert "doctor_id" in data
        assert "full_name" in data
        assert "department_name" in data
        assert "email" in data
        assert "keycloak_id" in data

    def test_get_doctor_by_keycloak_id_200(self) -> None:
        """Returns 200 with doctor data for valid Keycloak ID."""
        self.doctor_svc.get_doctor_by_keycloak_id.return_value = make_doctor_dto()
        resp = self.client.get(f"/api/v1/user/doctors/by-keycloak/{KEYCLOAK_ID}")
        assert resp.status_code == HTTP_200
        assert resp.json()["keycloak_id"] == str(KEYCLOAK_ID)

    def test_get_doctor_by_keycloak_id_404(self) -> None:
        """Returns 404 when doctor Keycloak ID is not found."""
        self.doctor_svc.get_doctor_by_keycloak_id.return_value = None
        resp = self.client.get(f"/api/v1/user/doctors/by-keycloak/{uuid4()}")
        assert resp.status_code == HTTP_404
        assert resp.json()["message"] == "Doctor not found"

    def test_get_doctor_by_keycloak_id_calls_service(self) -> None:
        """Passes Keycloak ID correctly to service."""
        self.doctor_svc.get_doctor_by_keycloak_id.return_value = make_doctor_dto()
        self.client.get(f"/api/v1/user/doctors/by-keycloak/{KEYCLOAK_ID}")
        self.doctor_svc.get_doctor_by_keycloak_id.assert_called_once_with(KEYCLOAK_ID)


# ─────────────────────────────────────────────
# API Routes — Patient
# ─────────────────────────────────────────────


class TestPatientRoutes:
    """Integration tests for patient API routes."""

    def setup_method(self) -> None:
        """Set up test client with mocked services."""
        self.app, self.doctor_svc, self.patient_svc = make_test_app_user()
        self.client = TestClient(self.app)

    def _create_payload(self, **kwargs: object) -> dict[str, object]:
        """Build a valid patient create request payload."""
        defaults: dict[str, object] = {
            "first_name": "Maria",
            "last_name": "Andersen",
            "date_of_birth": "2000-01-15",
            "gender": "female",
            "phone_number": PHONE_NUMBER,
            "email": "maria@example.com",
        }
        defaults.update(kwargs)
        return defaults

    def test_find_or_create_patient_201(self) -> None:
        """Returns 201 with patient ID on successful create."""
        self.patient_svc.find_or_create_patient.return_value = make_patient_dto()
        resp = self.client.post("/api/v1/user/patients", json=self._create_payload())
        assert resp.status_code == HTTP_201
        assert resp.json()["patient_id"] == str(PATIENT_ID)

    def test_find_or_create_patient_response_fields(self) -> None:
        """Response includes all expected patient fields."""
        self.patient_svc.find_or_create_patient.return_value = make_patient_dto()
        resp = self.client.post("/api/v1/user/patients", json=self._create_payload())
        data = resp.json()
        assert data["first_name"] == "Maria"
        assert data["last_name"] == "Andersen"
        assert data["email"] == "maria@example.com"
        assert data["gender"] == "female"
        assert data["phone_number"] == PHONE_NUMBER

    def test_find_or_create_patient_invalid_payload_422(self) -> None:
        """Returns 422 when required fields are missing."""
        resp = self.client.post(
            "/api/v1/user/patients", json={"email": "only@email.com"}
        )
        assert resp.status_code == HTTP_422

    def test_get_patient_by_id_200(self) -> None:
        """Returns 200 with patient data for valid ID."""
        self.patient_svc.get_patient.return_value = make_patient_dto()
        resp = self.client.get(f"/api/v1/user/patients/{PATIENT_ID}")
        assert resp.status_code == HTTP_200
        assert resp.json()["patient_id"] == str(PATIENT_ID)

    def test_get_patient_by_id_404(self) -> None:
        """Returns 404 when patient ID not found."""
        self.patient_svc.get_patient.return_value = None
        resp = self.client.get(f"/api/v1/user/patients/{uuid4()}")
        assert resp.status_code == HTTP_404
        assert resp.json()["message"] == "Patient not found"

    def test_get_patient_by_email_200(self) -> None:
        """Returns 200 with patient data when email matches."""
        self.patient_svc.get_patient_by_email.return_value = make_patient_dto()
        resp = self.client.get(
            "/api/v1/user/patients/by-email", params={"email": "maria@example.com"}
        )
        assert resp.status_code == HTTP_200
        assert resp.json()["email"] == "maria@example.com"

    def test_get_patient_by_email_404(self) -> None:
        """Returns 404 when email not found."""
        self.patient_svc.get_patient_by_email.return_value = None
        resp = self.client.get(
            "/api/v1/user/patients/by-email", params={"email": "nobody@example.com"}
        )
        assert resp.status_code == HTTP_404
        assert resp.json()["message"] == "Patient not found"

    def test_get_patient_by_email_calls_service(self) -> None:
        """Passes email correctly to service."""
        self.patient_svc.get_patient_by_email.return_value = make_patient_dto()
        self.client.get(
            "/api/v1/user/patients/by-email", params={"email": "maria@example.com"}
        )
        self.patient_svc.get_patient_by_email.assert_called_once_with(
            "maria@example.com"
        )

    def test_by_email_route_not_intercepted_by_id_route(self) -> None:
        """Ensures /by-email is not matched as a UUID patient_id."""
        self.patient_svc.get_patient_by_email.return_value = make_patient_dto()
        resp = self.client.get(
            "/api/v1/user/patients/by-email", params={"email": "test@test.com"}
        )
        assert resp.status_code in (HTTP_200, HTTP_404)
        self.patient_svc.get_patient.assert_not_called()
