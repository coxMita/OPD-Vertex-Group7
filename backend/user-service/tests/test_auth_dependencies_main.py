"""Tests for auth, dependency wiring, and app lifecycle helpers."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

import main as app_main
from src.api import auth, dependencies
from src.repositories.doctor_repository import DoctorRepository
from src.repositories.patient_repository import PatientRepository
from src.services.doctor_service import DoctorService
from src.services.patient_service import PatientService

HTTP_500 = 500
HTTP_401 = 401
EXPECTED_JWKS_FETCHES = 2


@pytest.fixture(autouse=True)
def reset_auth_cache() -> Generator[None, None, None]:
    """Reset cached auth state between tests."""
    auth._jwks = None
    auth._keycloak_certs_url = None
    yield
    auth._jwks = None
    auth._keycloak_certs_url = None


def test_get_certs_url_uses_environment_and_caches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Certs URL should be derived from env vars and cached."""
    monkeypatch.setenv("KEYCLOAK_REALM", "realm-a")
    monkeypatch.setenv("KEYCLOAK_EXTERNAL_URL", "http://kc:8089")

    first = auth.get_certs_url()
    monkeypatch.setenv("KEYCLOAK_REALM", "realm-b")
    second = auth.get_certs_url()

    assert first == "http://kc:8089/realms/realm-a/protocol/openid-connect/certs"
    assert second == first


@pytest.mark.asyncio
@patch("src.api.auth.httpx.AsyncClient")
async def test_get_jwks_fetches_and_caches_keys(mock_client_cls: MagicMock) -> None:
    """JWKS should be fetched once and then served from cache."""
    response = MagicMock()
    response.json.return_value = {"keys": [{"kid": "kid-1"}]}
    response.raise_for_status.return_value = None

    client = AsyncMock()
    client.get.return_value = response
    mock_client_cls.return_value.__aenter__.return_value = client

    first = await auth.get_jwks()
    second = await auth.get_jwks()

    assert first == {"keys": [{"kid": "kid-1"}]}
    assert second == first
    client.get.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.api.auth.httpx.AsyncClient")
async def test_get_jwks_raises_500_when_fetch_fails(mock_client_cls: MagicMock) -> None:
    """JWKS fetch failures should become a 500 HTTP error."""
    client = AsyncMock()
    client.get.side_effect = RuntimeError("network down")
    mock_client_cls.return_value.__aenter__.return_value = client

    with pytest.raises(HTTPException) as exc_info:
        await auth.get_jwks()

    assert exc_info.value.status_code == HTTP_500
    assert exc_info.value.detail == "Could not fetch authentication keys"


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_kid() -> None:
    """Token headers without a kid should be rejected."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with (
        patch("src.api.auth.jwt.get_unverified_header", return_value={}),
        patch("src.api.auth.get_jwks", new=AsyncMock(return_value={"keys": []})),
        pytest.raises(HTTPException) as exc_info,
    ):
        await auth.get_current_user(credentials)

    assert exc_info.value.status_code == HTTP_401
    assert exc_info.value.detail == "Invalid token header"


@pytest.mark.asyncio
async def test_get_current_user_refreshes_jwks_when_key_missing() -> None:
    """A missing key should trigger a JWKS refresh before decoding."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    jwks_first = {"keys": []}
    jwks_second = {"keys": [{"kid": "abc", "kty": "RSA"}]}

    with (
        patch("src.api.auth.jwt.get_unverified_header", return_value={"kid": "abc"}),
        patch(
            "src.api.auth.get_jwks",
            new=AsyncMock(side_effect=[jwks_first, jwks_second]),
        ) as get_jwks_mock,
        patch(
            "src.api.auth.jwt.decode", return_value={"sub": "doctor-1"}
        ) as decode_mock,
    ):
        payload = await auth.get_current_user(credentials)

    assert payload == {"sub": "doctor-1"}
    assert get_jwks_mock.await_count == EXPECTED_JWKS_FETCHES
    decode_mock.assert_called_once_with(
        "token",
        {"kid": "abc", "kty": "RSA"},
        algorithms=["RS256"],
        options={"verify_aud": False},
    )


@pytest.mark.asyncio
async def test_get_current_user_rejects_unknown_key_after_refresh() -> None:
    """A token should be rejected if no matching signing key exists."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with (
        patch(
            "src.api.auth.jwt.get_unverified_header", return_value={"kid": "missing"}
        ),
        patch(
            "src.api.auth.get_jwks",
            new=AsyncMock(side_effect=[{"keys": []}, {"keys": []}]),
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await auth.get_current_user(credentials)

    assert exc_info.value.status_code == HTTP_401
    assert exc_info.value.detail == "Unable to find appropriate key"


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_jwt() -> None:
    """JWT decode failures should be translated to 401."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with (
        patch("src.api.auth.jwt.get_unverified_header", return_value={"kid": "abc"}),
        patch(
            "src.api.auth.get_jwks",
            new=AsyncMock(return_value={"keys": [{"kid": "abc"}]}),
        ),
        patch("src.api.auth.jwt.decode", side_effect=JWTError("bad token")),
        pytest.raises(HTTPException) as exc_info,
    ):
        await auth.get_current_user(credentials)

    assert exc_info.value.status_code == HTTP_401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_db_session_yields_context_session() -> None:
    """Database dependency should yield the session from the context manager."""
    fake_session = object()
    session_factory = MagicMock()
    session_factory.return_value.__enter__.return_value = fake_session
    session_factory.return_value.__exit__.return_value = False

    with patch("src.api.dependencies.Session", session_factory):
        session_gen = dependencies.get_db_session()
        yielded = next(session_gen)

        assert yielded is fake_session
        with pytest.raises(StopIteration):
            next(session_gen)


def test_dependency_factories_build_expected_types() -> None:
    """Repository and service dependencies should wrap their inputs correctly."""
    session = MagicMock()
    patient_repo = dependencies.get_patient_repository(session)
    doctor_repo = dependencies.get_doctor_repository(session)

    assert isinstance(patient_repo, PatientRepository)
    assert isinstance(doctor_repo, DoctorRepository)
    assert patient_repo._session is session
    assert doctor_repo._session is session

    patient_service = dependencies.get_patient_service(patient_repo)
    doctor_service = dependencies.get_doctor_service(doctor_repo)

    assert isinstance(patient_service, PatientService)
    assert isinstance(doctor_service, DoctorService)
    assert patient_service._repo is patient_repo
    assert doctor_service._repo is doctor_repo


def test_main_root_and_health_endpoints() -> None:
    """Root and health endpoints should return static service metadata."""
    assert app_main.get_root() == {"service": "User Service"}
    assert app_main.get_health() == {"status": "ok"}


@pytest.mark.asyncio
async def test_lifespan_starts_and_stops_messaging() -> None:
    """App lifespan should wire the pubsub facade and manage startup/shutdown."""
    manager = MagicMock()
    manager.start_all = AsyncMock()
    manager.stop_all = AsyncMock()
    facade = object()

    with (
        patch.object(app_main, "messaging_manager", manager),
        patch.object(app_main, "PubSubFacade", return_value=facade) as facade_cls,
    ):
        async with app_main.lifespan(FastAPI()):
            pass

    facade_cls.assert_called_once_with(app_main.AMQP_URL, app_main.USER_CREATED)
    manager.add_pubsub.assert_called_once_with(facade)
    manager.start_all.assert_awaited_once()
    manager.stop_all.assert_awaited_once()
