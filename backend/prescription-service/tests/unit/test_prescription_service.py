"""Unit tests for PrescriptionService."""

import uuid
from unittest.mock import MagicMock

import pytest

from src.models.db.prescription import Prescription, PrescriptionStatus
from src.models.dto.prescription_response import PrescriptionResponse
from src.services.prescription_service import NIL_UUID, PrescriptionService

CONSULTATION_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
PATIENT_ID = uuid.UUID("00000000-0000-0000-0002-000000000001")
PRESCRIPTION_ID = uuid.UUID("00000000-0000-0000-0004-000000000001")

_FAKE_RX_JSON: dict = {
    "medication_name": "Amoxicillin",
    "dosage": "500mg",
    "frequency": "3x daily",
}
_FAKE_SUMMARY = "Patient has bacterial tonsillitis. Amoxicillin prescribed."


def _make_prescription(
    prescription_id: uuid.UUID = PRESCRIPTION_ID,
    consultation_id: uuid.UUID = CONSULTATION_ID,
    status: PrescriptionStatus = PrescriptionStatus.DRAFT,
    prescription_json: dict | None = None,
    summary_json: dict | None = None,
) -> Prescription:
    """Create a test Prescription entity."""
    p = Prescription(
        consultation_id=consultation_id,
        patient_id=NIL_UUID,
        doctor_id=NIL_UUID,
        status=status,
        prescription_json=prescription_json or _FAKE_RX_JSON,
        summary_json=summary_json or {"summary": _FAKE_SUMMARY},
    )
    p.id = prescription_id
    return p


@pytest.fixture
def repo() -> MagicMock:
    """Return a mocked PrescriptionRepository."""
    return MagicMock()


@pytest.fixture
def service(repo: MagicMock) -> PrescriptionService:
    """Return a PrescriptionService with mocked repo."""
    return PrescriptionService(repo)


# ── create_from_ai ────────────────────────────────────────────────────────────


class TestCreateFromAi:
    """Unit tests for PrescriptionService.create_from_ai()."""

    def test_creates_prescription_with_draft_status(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should create a prescription with DRAFT status."""
        prescription = _make_prescription()
        repo.create.return_value = prescription

        service.create_from_ai(CONSULTATION_ID, _FAKE_RX_JSON, _FAKE_SUMMARY)

        repo.create.assert_called_once()
        created_entity: Prescription = repo.create.call_args[0][0]
        assert created_entity.status == PrescriptionStatus.DRAFT

    def test_uses_nil_uuid_for_patient_and_doctor(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should use NIL_UUID for patient_id and doctor_id."""
        prescription = _make_prescription()
        repo.create.return_value = prescription

        service.create_from_ai(CONSULTATION_ID, _FAKE_RX_JSON, _FAKE_SUMMARY)

        created_entity: Prescription = repo.create.call_args[0][0]
        assert created_entity.patient_id == NIL_UUID
        assert created_entity.doctor_id == NIL_UUID

    def test_stores_prescription_json(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should store the prescription_json from the AI response."""
        prescription = _make_prescription()
        repo.create.return_value = prescription

        service.create_from_ai(CONSULTATION_ID, _FAKE_RX_JSON, _FAKE_SUMMARY)

        created_entity: Prescription = repo.create.call_args[0][0]
        assert created_entity.prescription_json == _FAKE_RX_JSON

    def test_wraps_summary_in_summary_json(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should wrap summary string in {'summary': ...} dict."""
        prescription = _make_prescription()
        repo.create.return_value = prescription

        service.create_from_ai(CONSULTATION_ID, _FAKE_RX_JSON, _FAKE_SUMMARY)

        created_entity: Prescription = repo.create.call_args[0][0]
        assert created_entity.summary_json == {"summary": _FAKE_SUMMARY}

    def test_returns_prescription_response(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return a PrescriptionResponse DTO."""
        prescription = _make_prescription()
        repo.create.return_value = prescription

        result = service.create_from_ai(CONSULTATION_ID, _FAKE_RX_JSON, _FAKE_SUMMARY)

        assert isinstance(result, PrescriptionResponse)
        assert result.id == prescription.id
        assert result.consultation_id == CONSULTATION_ID

    def test_sets_correct_consultation_id(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should use the provided consultation_id."""
        prescription = _make_prescription()
        repo.create.return_value = prescription

        service.create_from_ai(CONSULTATION_ID, _FAKE_RX_JSON, _FAKE_SUMMARY)

        created_entity: Prescription = repo.create.call_args[0][0]
        assert created_entity.consultation_id == CONSULTATION_ID


# ── get_by_id ─────────────────────────────────────────────────────────────────


class TestGetById:
    """Unit tests for PrescriptionService.get_by_id()."""

    def test_returns_response_when_found(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return PrescriptionResponse when prescription exists."""
        prescription = _make_prescription()
        repo.get_by_id.return_value = prescription

        result = service.get_by_id(PRESCRIPTION_ID)

        assert isinstance(result, PrescriptionResponse)
        assert result.id == PRESCRIPTION_ID

    def test_returns_none_when_not_found(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return None when prescription does not exist."""
        repo.get_by_id.return_value = None

        result = service.get_by_id(uuid.uuid4())

        assert result is None

    def test_delegates_to_repo(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should call repo.get_by_id() with the correct ID."""
        repo.get_by_id.return_value = None
        service.get_by_id(PRESCRIPTION_ID)
        repo.get_by_id.assert_called_once_with(PRESCRIPTION_ID)


# ── get_by_consultation_id ────────────────────────────────────────────────────


class TestGetByConsultationId:
    """Unit tests for PrescriptionService.get_by_consultation_id()."""

    def test_returns_response_when_found(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return PrescriptionResponse when prescription exists."""
        prescription = _make_prescription()
        repo.get_by_consultation_id.return_value = prescription

        result = service.get_by_consultation_id(CONSULTATION_ID)

        assert isinstance(result, PrescriptionResponse)
        assert result.consultation_id == CONSULTATION_ID

    def test_returns_none_when_not_found(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return None when no prescription for consultation."""
        repo.get_by_consultation_id.return_value = None

        result = service.get_by_consultation_id(uuid.uuid4())

        assert result is None

    def test_delegates_to_repo(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should call repo.get_by_consultation_id() with correct ID."""
        repo.get_by_consultation_id.return_value = None
        service.get_by_consultation_id(CONSULTATION_ID)
        repo.get_by_consultation_id.assert_called_once_with(CONSULTATION_ID)

    def test_response_contains_correct_status(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Response should reflect the actual status from DB."""
        prescription = _make_prescription(status=PrescriptionStatus.APPROVED)
        repo.get_by_consultation_id.return_value = prescription

        result = service.get_by_consultation_id(CONSULTATION_ID)

        assert result is not None
        assert result.status == PrescriptionStatus.APPROVED


# ── get_by_patient_id ─────────────────────────────────────────────────────────


class TestGetByPatientId:
    """Unit tests for PrescriptionService.get_by_patient_id()."""

    def test_returns_list_of_responses(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return a list of PrescriptionResponse DTOs."""
        prescriptions = [
            _make_prescription(),
            _make_prescription(prescription_id=uuid.uuid4()),
        ]
        repo.get_by_patient_id.return_value = prescriptions

        result = service.get_by_patient_id(PATIENT_ID)

        assert len(result) == 2  # noqa: PLR2004
        assert all(isinstance(r, PrescriptionResponse) for r in result)

    def test_returns_empty_list_when_none(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return empty list when patient has no prescriptions."""
        repo.get_by_patient_id.return_value = []

        result = service.get_by_patient_id(uuid.uuid4())

        assert result == []

    def test_delegates_to_repo(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should call repo.get_by_patient_id() with correct ID."""
        repo.get_by_patient_id.return_value = []
        service.get_by_patient_id(PATIENT_ID)
        repo.get_by_patient_id.assert_called_once_with(PATIENT_ID)


# ── approve ───────────────────────────────────────────────────────────────────


class TestApprove:
    """Unit tests for PrescriptionService.approve()."""

    def test_returns_none_when_not_found(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return None if prescription does not exist."""
        repo.get_by_id.return_value = None

        result = service.approve(uuid.uuid4())

        assert result is None

    def test_updates_status_to_approved(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should call update_status with APPROVED."""
        prescription = _make_prescription(status=PrescriptionStatus.DRAFT)
        updated = _make_prescription(status=PrescriptionStatus.APPROVED)
        repo.get_by_id.return_value = prescription
        repo.update_status.return_value = updated

        result = service.approve(PRESCRIPTION_ID)

        repo.update_status.assert_called_once_with(
            prescription, PrescriptionStatus.APPROVED
        )
        assert result is not None
        assert result.status == PrescriptionStatus.APPROVED

    def test_returns_prescription_response(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should return a PrescriptionResponse DTO after approval."""
        prescription = _make_prescription()
        approved = _make_prescription(status=PrescriptionStatus.APPROVED)
        repo.get_by_id.return_value = prescription
        repo.update_status.return_value = approved

        result = service.approve(PRESCRIPTION_ID)

        assert isinstance(result, PrescriptionResponse)

    def test_does_not_call_update_when_not_found(
        self, service: PrescriptionService, repo: MagicMock
    ) -> None:
        """Should not call update_status if prescription not found."""
        repo.get_by_id.return_value = None

        service.approve(uuid.uuid4())

        repo.update_status.assert_not_called()
