"""Unit tests for PrescriptionRepository."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.models.db.prescription import Prescription, PrescriptionStatus
from src.repositories.prescription_repository import PrescriptionRepository

CONSULTATION_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
PATIENT_ID = uuid.UUID("00000000-0000-0000-0002-000000000001")
DOCTOR_ID = uuid.UUID("00000000-0000-0000-0003-000000000001")
NIL_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")


def _make_prescription(
    prescription_id: uuid.UUID | None = None,
    consultation_id: uuid.UUID = CONSULTATION_ID,
    status: PrescriptionStatus = PrescriptionStatus.DRAFT,
    payload: tuple[dict, dict] | None = None,
    approved_at: datetime | None = None,
) -> Prescription:
    """Create a test Prescription entity."""
    prescription_json, summary_json = payload or (
        {"medication_name": "Amoxicillin"},
        {"summary": "Patient has fever."},
    )
    p = Prescription(
        consultation_id=consultation_id,
        patient_id=NIL_UUID,
        doctor_id=NIL_UUID,
        status=status,
        prescription_json=prescription_json,
        summary_json=summary_json,
        approved_at=approved_at,
    )
    p.id = prescription_id or uuid.uuid4()
    return p


@pytest.fixture
def session() -> MagicMock:
    """Return a mocked SQLModel Session."""
    return MagicMock()


@pytest.fixture
def repo(session: MagicMock) -> PrescriptionRepository:
    """Return a PrescriptionRepository with mocked session."""
    return PrescriptionRepository(session)


# ── create ────────────────────────────────────────────────────────────────────


class TestCreate:
    """Unit tests for PrescriptionRepository.create()."""

    def test_create_adds_commits_and_refreshes(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """create() should add, commit and refresh the prescription."""
        prescription = _make_prescription()
        result = repo.create(prescription)
        session.add.assert_called_once_with(prescription)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(prescription)
        assert result is prescription

    def test_create_returns_same_instance(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """create() should return the same entity it received."""
        prescription = _make_prescription()
        result = repo.create(prescription)
        assert result is prescription


# ── get_by_id ─────────────────────────────────────────────────────────────────


class TestGetById:
    """Unit tests for PrescriptionRepository.get_by_id()."""

    def test_returns_prescription_when_found(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should return the prescription when it exists."""
        prescription_id = uuid.uuid4()
        prescription = _make_prescription(prescription_id)
        session.get.return_value = prescription

        result = repo.get_by_id(prescription_id)

        session.get.assert_called_once_with(Prescription, prescription_id)
        assert result is prescription

    def test_returns_none_when_not_found(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should return None when prescription does not exist."""
        session.get.return_value = None
        result = repo.get_by_id(uuid.uuid4())
        assert result is None

    def test_passes_correct_id_to_session(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should pass the exact UUID to session.get()."""
        prescription_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        session.get.return_value = None
        repo.get_by_id(prescription_id)
        session.get.assert_called_once_with(Prescription, prescription_id)


# ── get_by_consultation_id ────────────────────────────────────────────────────


class TestGetByConsultationId:
    """Unit tests for PrescriptionRepository.get_by_consultation_id()."""

    def test_returns_prescription_when_found(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should return the first result from exec().first()."""
        prescription = _make_prescription()
        mock_result = MagicMock()
        mock_result.first.return_value = prescription
        session.exec.return_value = mock_result

        result = repo.get_by_consultation_id(CONSULTATION_ID)
        assert result is prescription

    def test_returns_none_when_not_found(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should return None when no prescription exists for the consultation."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        session.exec.return_value = mock_result

        result = repo.get_by_consultation_id(uuid.uuid4())
        assert result is None

    def test_calls_exec_with_query(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should call session.exec() exactly once."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        session.exec.return_value = mock_result

        repo.get_by_consultation_id(CONSULTATION_ID)
        session.exec.assert_called_once()


# ── get_by_patient_id ─────────────────────────────────────────────────────────


class TestGetByPatientId:
    """Unit tests for PrescriptionRepository.get_by_patient_id()."""

    def test_returns_list_of_prescriptions(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should return a list of all prescriptions for the patient."""
        prescriptions = [_make_prescription(), _make_prescription()]
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter(prescriptions))
        session.exec.return_value = mock_result

        result = repo.get_by_patient_id(PATIENT_ID)
        assert len(result) == 2  # noqa: PLR2004

    def test_returns_empty_list_when_none_found(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should return an empty list when patient has no prescriptions."""
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        session.exec.return_value = mock_result

        result = repo.get_by_patient_id(uuid.uuid4())
        assert result == []

    def test_calls_exec_once(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should call session.exec() exactly once."""
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        session.exec.return_value = mock_result

        repo.get_by_patient_id(PATIENT_ID)
        session.exec.assert_called_once()


# ── update_status ─────────────────────────────────────────────────────────────


class TestUpdateStatus:
    """Unit tests for PrescriptionRepository.update_status()."""

    def test_updates_status_field(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should set the new status on the prescription before saving."""
        prescription = _make_prescription(status=PrescriptionStatus.DRAFT)
        result = repo.update_status(prescription, PrescriptionStatus.APPROVED)
        assert result.status == PrescriptionStatus.APPROVED

    def test_saves_and_refreshes(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should add, commit and refresh after status update."""
        prescription = _make_prescription()
        repo.update_status(prescription, PrescriptionStatus.SENT)
        session.add.assert_called_once_with(prescription)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(prescription)

    def test_returns_updated_prescription(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """Should return the prescription instance with updated status."""
        prescription = _make_prescription(status=PrescriptionStatus.DRAFT)
        result = repo.update_status(prescription, PrescriptionStatus.APPROVED)
        assert result is prescription
        assert result.status == PrescriptionStatus.APPROVED

    def test_draft_to_approved(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """DRAFT → APPROVED transition should persist correctly."""
        prescription = _make_prescription(status=PrescriptionStatus.DRAFT)
        repo.update_status(prescription, PrescriptionStatus.APPROVED)
        assert prescription.status == PrescriptionStatus.APPROVED

    def test_approved_to_sent(
        self, repo: PrescriptionRepository, session: MagicMock
    ) -> None:
        """APPROVED → SENT transition should persist correctly."""
        prescription = _make_prescription(status=PrescriptionStatus.APPROVED)
        repo.update_status(prescription, PrescriptionStatus.SENT)
        assert prescription.status == PrescriptionStatus.SENT
