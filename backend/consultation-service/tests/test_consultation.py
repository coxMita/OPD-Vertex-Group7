"""Tests for consultation service."""

import uuid
from datetime import time

import pytest

from src.models.db.consultation import Consultation, ConsultationStatus
from src.models.dto.consultation_create_request import ConsultationCreateRequest
from src.models.dto.consultation_status_update_request import (
    ConsultationUpdateRequest,
)


class TestConsultationRepository:
    """Tests for ConsultationRepository."""

    def test_create_consultation(self, consultation_repository, test_consultation_data):
        """Test creating a consultation."""
        consultation = Consultation(**test_consultation_data)
        created = consultation_repository.create(consultation)

        assert created.id is not None
        assert created.appointment_id == test_consultation_data["appointment_id"]
        assert created.doctor_id == test_consultation_data["doctor_id"]
        assert created.status == ConsultationStatus.ACTIVE

    def test_get_by_id(self, consultation_repository, test_consultation):
        """Test getting a consultation by ID."""
        result = consultation_repository.get_by_id(test_consultation.id)
        assert result is not None
        assert result.id == test_consultation.id

    def test_get_by_id_not_found(self, consultation_repository):
        """Test getting a non-existent consultation."""
        result = consultation_repository.get_by_id(uuid.uuid4())
        assert result is None

    def test_get_by_appointment_id(self, consultation_repository, test_consultation):
        """Test getting a consultation by appointment ID."""
        result = consultation_repository.get_by_appointment_id(
            test_consultation.appointment_id
        )
        assert result is not None
        assert result.appointment_id == test_consultation.appointment_id

    def test_get_by_doctor_id(self, consultation_repository, test_consultation):
        """Test getting consultations by doctor ID."""
        results = consultation_repository.get_by_doctor_id(test_consultation.doctor_id)
        assert len(results) > 0
        assert all(c.doctor_id == test_consultation.doctor_id for c in results)

    def test_update_consultation(self, consultation_repository, test_consultation):
        """Test updating a consultation."""
        updated = consultation_repository.update(
            test_consultation,
            start_time=time(8, 0),
        )
        assert updated.start_time == time(8, 0)

    def test_update_status(self, consultation_repository, test_consultation):
        """Test updating consultation status."""
        updated = consultation_repository.update_status(
            test_consultation, ConsultationStatus.COMPLETED
        )
        assert updated.status == ConsultationStatus.COMPLETED


class TestConsultationService:
    """Tests for ConsultationService."""

    def test_create_consultation(self, consultation_service, test_consultation_data):
        """Test creating a consultation via service."""
        request = ConsultationCreateRequest(**test_consultation_data)
        result = consultation_service.create_consultation(request)

        assert result.id is not None
        assert result.appointment_id == request.appointment_id
        assert result.doctor_id == request.doctor_id

    def test_create_consultation_duplicate(
        self, consultation_service, test_consultation
    ):
        """Test creating a duplicate consultation fails."""
        request = ConsultationCreateRequest(
            appointment_id=test_consultation.appointment_id,
            doctor_id=test_consultation.doctor_id,
        )
        with pytest.raises(ValueError, match="already exists"):
            consultation_service.create_consultation(request)

    def test_get_consultation(self, consultation_service, test_consultation):
        """Test getting a consultation."""
        result = consultation_service.get_consultation(test_consultation.id)
        assert result is not None
        assert result.id == test_consultation.id

    def test_get_consultation_not_found(self, consultation_service):
        """Test getting a non-existent consultation."""
        result = consultation_service.get_consultation(uuid.uuid4())
        assert result is None

    def test_get_by_appointment_id(self, consultation_service, test_consultation):
        """Test getting a consultation by appointment ID."""
        result = consultation_service.get_by_appointment_id(
            test_consultation.appointment_id
        )
        assert result is not None

    def test_get_doctor_consultations(self, consultation_service, test_consultation):
        """Test getting doctor consultations."""
        results = consultation_service.get_doctor_consultations(
            test_consultation.doctor_id
        )
        assert len(results) > 0

    def test_update_consultation(self, consultation_service, test_consultation):
        """Test updating a consultation."""
        request = ConsultationUpdateRequest(
            start_time=time(9, 0),
            end_time=time(9, 30),
        )
        result = consultation_service.update_consultation(test_consultation.id, request)
        assert result is not None
        assert result.start_time == time(9, 0)
        assert result.end_time == time(9, 30)

    def test_update_consultation_not_found(self, consultation_service):
        """Test updating a non-existent consultation."""
        request = ConsultationUpdateRequest(start_time=time(10, 0))
        result = consultation_service.update_consultation(uuid.uuid4(), request)
        assert result is None

    def test_update_status(self, consultation_service, test_consultation):
        """Test updating consultation status."""
        result = consultation_service.update_status(
            test_consultation.id, ConsultationStatus.COMPLETED
        )
        assert result is not None
        assert result.status == ConsultationStatus.COMPLETED
