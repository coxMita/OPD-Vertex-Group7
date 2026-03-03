"""Unit tests for src/transcription/router.py."""

import os
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from src.models.msg.transcript_message import TranscriptMessage

# ── App bootstrap (mock heavy deps before importing main) ─────────────────────

_mock_facade = MagicMock()
_mock_facade.connect = AsyncMock()
_mock_facade.close = AsyncMock()
_mock_facade.publish = AsyncMock()
_mock_facade.exchange_name = "transcription.completed"

with (
    patch("src.messaging.pubsub_facade.PubSubFacade", return_value=_mock_facade),
    patch("src.transcription.whisper.get_model", return_value=MagicMock()),
):
    from main import app

client = TestClient(app)

FAKE_AUDIO: tuple[str, bytes, str] = ("audio.wav", b"fake-audio-bytes", "audio/wav")
FAKE_TRANSCRIPTION: tuple[str, str, float] = ("Hello world", "en", 0.99)
EXPECTED_TUPLE_LENGTH = 3


def _post_audio(audio: tuple[str, bytes, str] = FAKE_AUDIO) -> Response:
    return client.post("/transcription/", files={"file": audio})


# ── GET / ─────────────────────────────────────────────────────────────────────


class TestRoot:
    """Tests for GET /."""

    def test_returns_200(self) -> None:
        """Root endpoint returns HTTP 200."""
        response = client.get("/")
        assert response.status_code == HTTPStatus.OK

    def test_returns_service_name(self) -> None:
        """Root endpoint identifies the service."""
        response = client.get("/")
        assert response.json() == {"service": "transcription-service"}


# ── GET /health ───────────────────────────────────────────────────────────────


class TestHealth:
    """Tests for GET /health."""

    def test_returns_200(self) -> None:
        """Health endpoint returns HTTP 200."""
        response = client.get("/health")
        assert response.status_code == HTTPStatus.OK

    def test_returns_ok(self) -> None:
        """Health endpoint reports status ok."""
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


# ── POST /transcription/ ──────────────────────────────────────────────────────


class TestTranscribeEndpoint:
    """Tests for POST /transcription/."""

    @patch("src.transcription.router.messaging_manager")
    @patch("src.transcription.router.transcribe_audio", return_value=FAKE_TRANSCRIPTION)
    def test_returns_transcript(
        self, _mock_transcribe: MagicMock, mock_mm: MagicMock
    ) -> None:
        """Endpoint returns the transcript text in the response body."""
        mock_mm.get_pubsub.return_value.publish = AsyncMock()
        response = _post_audio()
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"transcript": "Hello world"}

    @patch("src.transcription.router.messaging_manager")
    @patch("src.transcription.router.transcribe_audio", return_value=("", "en", 0.99))
    def test_returns_empty_transcript(
        self, _mock_transcribe: MagicMock, mock_mm: MagicMock
    ) -> None:
        """Endpoint handles an empty transcript gracefully."""
        mock_mm.get_pubsub.return_value.publish = AsyncMock()
        response = _post_audio()
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"transcript": ""}

    @patch(
        "src.transcription.router.transcribe_audio",
        side_effect=RuntimeError("model error"),
    )
    def test_returns_500_on_transcription_failure(self, _mock: MagicMock) -> None:
        """Endpoint returns HTTP 500 when transcription raises an exception."""
        response = _post_audio()
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "model error" in response.json()["detail"]

    def test_returns_422_without_file(self) -> None:
        """Endpoint returns HTTP 422 when no file is provided."""
        response = client.post("/transcription/")
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @patch("src.transcription.router.messaging_manager")
    @patch("src.transcription.router.transcribe_audio", return_value=FAKE_TRANSCRIPTION)
    def test_temp_file_is_cleaned_up(
        self, _mock_transcribe: MagicMock, mock_mm: MagicMock
    ) -> None:
        """Temporary file is deleted after transcription."""
        mock_mm.get_pubsub.return_value.publish = AsyncMock()
        created_paths: list[str] = []
        original_unlink = os.unlink

        def tracking_unlink(path: str) -> None:
            created_paths.append(path)
            original_unlink(path)

        with patch("src.transcription.router.os.unlink", side_effect=tracking_unlink):
            _post_audio()

        assert len(created_paths) == 1
        assert not os.path.exists(created_paths[0])

    @patch("src.transcription.router.messaging_manager")
    @patch(
        "src.transcription.router.transcribe_audio",
        side_effect=RuntimeError("fail"),
    )
    def test_temp_file_cleaned_up_on_transcription_error(
        self, _mock_transcribe: MagicMock, mock_mm: MagicMock
    ) -> None:
        """Temporary file is deleted even when transcription raises."""
        created_paths: list[str] = []
        original_unlink = os.unlink

        def tracking_unlink(path: str) -> None:
            created_paths.append(path)
            original_unlink(path)

        with patch("src.transcription.router.os.unlink", side_effect=tracking_unlink):
            _post_audio()

        assert len(created_paths) == 1

    @patch("src.transcription.router.messaging_manager")
    @patch("src.transcription.router.transcribe_audio", return_value=FAKE_TRANSCRIPTION)
    def test_publishes_message_to_rabbitmq(
        self, _mock_transcribe: MagicMock, mock_mm: MagicMock
    ) -> None:
        """A TranscriptMessage is published after transcription."""
        mock_publish = AsyncMock()
        mock_mm.get_pubsub.return_value.publish = mock_publish
        _post_audio()
        mock_publish.assert_awaited_once()

    @patch("src.transcription.router.messaging_manager")
    @patch("src.transcription.router.transcribe_audio", return_value=FAKE_TRANSCRIPTION)
    def test_publish_failure_returns_500(
        self, _mock_transcribe: MagicMock, mock_mm: MagicMock
    ) -> None:
        """Returns HTTP 500 with detail when RabbitMQ publish fails."""
        mock_mm.get_pubsub.return_value.publish = AsyncMock(
            side_effect=RuntimeError("broker down")
        )
        response = _post_audio()
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "broker down" in response.json()["detail"]

    @patch("src.transcription.router.messaging_manager")
    @patch("src.transcription.router.transcribe_audio", return_value=FAKE_TRANSCRIPTION)
    def test_published_message_contains_transcript(
        self, _mock_transcribe: MagicMock, mock_mm: MagicMock
    ) -> None:
        """The published TranscriptMessage carries the correct fields."""
        mock_publish = AsyncMock()
        mock_mm.get_pubsub.return_value.publish = mock_publish
        _post_audio()

        published_msg: TranscriptMessage = mock_publish.call_args[0][0]
        assert published_msg.transcript == "Hello world"
        assert published_msg.language == "en"
        assert published_msg.language_probability == pytest.approx(0.99)
