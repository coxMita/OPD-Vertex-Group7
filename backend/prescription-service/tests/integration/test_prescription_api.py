"""Integration tests for prescription API routes.

Spins up the full FastAPI app but mocks all external dependencies
(DB, RabbitMQ) — no running infrastructure required.
"""

import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from main import app as main_app
from src.api.dependencies import get_prescription_service
from src.api.routes.prescription_routes import router
from src.models.db.prescription import PrescriptionStatus
from src.models.dto.prescription_response import PrescriptionResponse
from src.services.prescription_service import PrescriptionService

# ── Minimal app without lifespan (no RabbitMQ/DB needed) ─────────────────────


@asynccontextmanager
async def _noop_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    yield


_app = FastAPI(lifespan=_noop_lifespan)
_app.include_router(router)

CONSULTATION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
PRESCRIPTION_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
PATIENT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
NIL_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")

_FAKE_RESPONSE = PrescriptionResponse(
    id=PRESCRIPTION_ID,
    consultation_id=CONSULTATION_ID,
    patient_id=NIL_UUID,
    doctor_id=NIL_UUID,
    status=PrescriptionStatus.DRAFT,
    prescription_json={"medication_name": "Amoxicillin", "dosage": "500mg"},
    summary_json={"summary": "Patient has tonsillitis."},
    approved_at=None,
)

_APPROVED_RESPONSE = PrescriptionResponse(
    id=PRESCRIPTION_ID,
    consultation_id=CONSULTATION_ID,
    patient_id=NIL_UUID,
    doctor_id=NIL_UUID,
    status=PrescriptionStatus.APPROVED,
    prescription_json={"medication_name": "Amoxicillin", "dosage": "500mg"},
    summary_json={"summary": "Patient has tonsillitis."},
    approved_at=None,
)


def _mock_service(
    get_by_id: object = None,
    get_by_consultation: object = None,
    get_by_patient: object = None,
    approve: object = None,
) -> MagicMock:
    svc = MagicMock(spec=PrescriptionService)
    svc.get_by_id.return_value = get_by_id
    svc.get_by_consultation_id.return_value = get_by_consultation
    svc.get_by_patient_id.return_value = get_by_patient or []
    svc.approve.return_value = approve
    return svc


def _override_service(service: MagicMock) -> object:
    def _get_service() -> MagicMock:
        return service

    return _get_service


# ── GET /api/v1/prescriptions/consultation/{id} ───────────────────────────────


@pytest.mark.asyncio
class TestGetByConsultationEndpoint:
    """Integration tests for GET /api/v1/prescriptions/consultation/{id}."""

    async def test_returns_200_when_found(self) -> None:
        """Should return 200 with prescription data."""
        svc = _mock_service(get_by_consultation=_FAKE_RESPONSE)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/prescriptions/consultation/{CONSULTATION_ID}"
            )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["id"] == str(PRESCRIPTION_ID)
        assert body["consultation_id"] == str(CONSULTATION_ID)
        assert body["status"] == "draft"

    async def test_returns_404_when_not_found(self) -> None:
        """Should return 404 when no prescription exists for consultation."""
        svc = _mock_service(get_by_consultation=None)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/prescriptions/consultation/{uuid.uuid4()}"
            )

        assert response.status_code == HTTPStatus.NOT_FOUND

    async def test_returns_422_for_invalid_uuid(self) -> None:
        """Should return 422 for non-UUID consultation_id."""
        _app.dependency_overrides[get_prescription_service] = _override_service(
            _mock_service()
        )

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/prescriptions/consultation/not-a-uuid")

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_response_contains_prescription_json(self) -> None:
        """Response body should include the prescription_json field."""
        svc = _mock_service(get_by_consultation=_FAKE_RESPONSE)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/prescriptions/consultation/{CONSULTATION_ID}"
            )

        assert response.json()["prescription_json"]["medication_name"] == "Amoxicillin"

    async def test_response_contains_summary_json(self) -> None:
        """Response body should include the summary_json field."""
        svc = _mock_service(get_by_consultation=_FAKE_RESPONSE)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/prescriptions/consultation/{CONSULTATION_ID}"
            )

        assert "summary" in response.json()["summary_json"]


# ── GET /api/v1/prescriptions/{id} ───────────────────────────────────────────


@pytest.mark.asyncio
class TestGetByIdEndpoint:
    """Integration tests for GET /api/v1/prescriptions/{prescription_id}."""

    async def test_returns_200_when_found(self) -> None:
        """Should return 200 with prescription data."""
        svc = _mock_service(get_by_id=_FAKE_RESPONSE)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/prescriptions/{PRESCRIPTION_ID}")

        assert response.status_code == HTTPStatus.OK
        assert response.json()["id"] == str(PRESCRIPTION_ID)

    async def test_returns_404_when_not_found(self) -> None:
        """Should return 404 when prescription does not exist."""
        svc = _mock_service(get_by_id=None)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/prescriptions/{uuid.uuid4()}")

        assert response.status_code == HTTPStatus.NOT_FOUND

    async def test_returns_422_for_invalid_uuid(self) -> None:
        """Should return 422 for non-UUID prescription_id."""
        _app.dependency_overrides[get_prescription_service] = _override_service(
            _mock_service()
        )

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/prescriptions/bad-id")

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ── GET /api/v1/prescriptions/patient/{id} ───────────────────────────────────


@pytest.mark.asyncio
class TestGetByPatientEndpoint:
    """Integration tests for GET /api/v1/prescriptions/patient/{patient_id}."""

    async def test_returns_200_with_list(self) -> None:
        """Should return 200 with list of prescriptions."""
        svc = _mock_service(get_by_patient=[_FAKE_RESPONSE, _FAKE_RESPONSE])
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/prescriptions/patient/{PATIENT_ID}")

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) == 2  # noqa: PLR2004

    async def test_returns_empty_list_when_none(self) -> None:
        """Should return 200 with empty list when patient has no prescriptions."""
        svc = _mock_service(get_by_patient=[])
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/prescriptions/patient/{uuid.uuid4()}")

        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    async def test_returns_422_for_invalid_uuid(self) -> None:
        """Should return 422 for non-UUID patient_id."""
        _app.dependency_overrides[get_prescription_service] = _override_service(
            _mock_service()
        )

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/prescriptions/patient/bad-uuid")

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ── PATCH /api/v1/prescriptions/{id}/approve ─────────────────────────────────


@pytest.mark.asyncio
class TestApproveEndpoint:
    """Integration tests for PATCH /api/v1/prescriptions/{id}/approve."""

    async def test_returns_200_with_approved_prescription(self) -> None:
        """Should return 200 with APPROVED status."""
        svc = _mock_service(approve=_APPROVED_RESPONSE)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/prescriptions/{PRESCRIPTION_ID}/approve"
            )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["status"] == "approved"

    async def test_returns_404_when_not_found(self) -> None:
        """Should return 404 when prescription does not exist."""
        svc = _mock_service(approve=None)
        _app.dependency_overrides[get_prescription_service] = lambda: svc

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/prescriptions/{uuid.uuid4()}/approve"
            )

        assert response.status_code == HTTPStatus.NOT_FOUND

    async def test_returns_422_for_invalid_uuid(self) -> None:
        """Should return 422 for non-UUID prescription_id."""
        _app.dependency_overrides[get_prescription_service] = _override_service(
            _mock_service()
        )

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.patch("/api/v1/prescriptions/bad-id/approve")

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ── Root & health ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestRootAndHealth:
    """Integration tests for root and health endpoints."""

    async def test_root_returns_200(self) -> None:
        """GET / should return 200."""
        async with AsyncClient(
            transport=ASGITransport(app=main_app), base_url="http://test"
        ) as client:
            response = await client.get("/")
        assert response.status_code == HTTPStatus.OK

    async def test_health_returns_ok(self) -> None:
        """GET /health should return {'status': 'ok'}."""
        async with AsyncClient(
            transport=ASGITransport(app=main_app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "ok"}
