"""Integration tests for src/transcription/router.py."""

import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


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

    @patch("src.transcription.router.transcribe_audio", return_value="Hello world")
    def test_returns_transcript(self, _mock: object) -> None:
        """Endpoint returns the transcript produced by transcribe_audio."""
        response = client.post(
            "/transcription/",
            files={"file": ("audio.wav", b"fake-audio-bytes", "audio/wav")},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"transcript": "Hello world"}

    @patch("src.transcription.router.transcribe_audio", return_value="")
    def test_returns_empty_transcript(self, _mock: object) -> None:
        """Endpoint handles an empty transcript gracefully."""
        response = client.post(
            "/transcription/",
            files={"file": ("audio.wav", b"fake-audio-bytes", "audio/wav")},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"transcript": ""}

    @patch(
        "src.transcription.router.transcribe_audio",
        side_effect=RuntimeError("model error"),
    )
    def test_returns_500_on_transcription_failure(self, _mock: object) -> None:
        """Endpoint returns HTTP 500 when transcription raises an exception."""
        response = client.post(
            "/transcription/",
            files={"file": ("audio.wav", b"fake-audio-bytes", "audio/wav")},
        )
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "model error" in response.json()["detail"]

    def test_returns_422_without_file(self) -> None:
        """Endpoint returns HTTP 422 when no file is provided."""
        response = client.post("/transcription/")
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @patch("src.transcription.router.transcribe_audio", return_value="Hello")
    def test_temp_file_is_cleaned_up(self, _mock: object) -> None:
        """Temporary file is deleted after transcription."""
        created_paths: list[str] = []
        original_unlink = os.unlink

        def tracking_unlink(path: str) -> None:
            created_paths.append(path)
            original_unlink(path)

        with patch("src.transcription.router.os.unlink", side_effect=tracking_unlink):
            client.post(
                "/transcription/",
                files={"file": ("audio.wav", b"fake-audio-bytes", "audio/wav")},
            )

        assert len(created_paths) == 1
        assert not os.path.exists(created_paths[0])
