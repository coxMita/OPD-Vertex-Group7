"""Unit tests for src.messaging.subscriber — on_transcript_message callback."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.messaging.subscriber import on_transcript_message

_VALID_CONSULTATION_ID = str(uuid.uuid4())
_VALID_TRANSCRIPT = "Patient has fever and sore throat."
_VALID_FILENAME = "consultation_001.mp3"

_AI_RESULT = {
    "summary": "Patient had fever. Amoxicillin prescribed.",
    "prescription": {
        "medication_name": "Amoxicillin",
        "dosage": "500mg",
        "frequency": "three times a day",
        "duration": "7 days",
        "notes": None,
    },
    "clinical_alerts": ["Rash: Consider dermatologist referral."],
}


def _make_body(
    transcript: str = _VALID_TRANSCRIPT,
    filename: str = _VALID_FILENAME,
    consultation_id: str | None = _VALID_CONSULTATION_ID,
) -> bytes:
    """Build a valid JSON message body."""
    payload: dict = {"transcript": transcript, "filename": filename}
    if consultation_id is not None:
        payload["consultation_id"] = consultation_id
    return json.dumps(payload).encode()


def _mock_messaging_manager() -> MagicMock:
    """Return a mock messaging_manager with async publish support."""
    mock_pubsub = AsyncMock()
    mock_mgr = MagicMock()
    mock_mgr.get_pubsub.return_value = mock_pubsub
    return mock_mgr


class TestOnTranscriptMessageSkipCases:
    """Tests for invalid/missing input — callback should return without publishing."""

    @pytest.mark.asyncio
    async def test_skips_non_json_body(self) -> None:
        """Should log an error and return early for non-JSON message bodies."""
        with patch(
            "src.messaging.subscriber.process_transcript",
            new=AsyncMock(),
        ) as mock_process:
            await on_transcript_message(b"not valid json {{")

        mock_process.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_empty_transcript(self) -> None:
        """Should return early when transcript field is empty."""
        body = _make_body(transcript="")

        with patch(
            "src.messaging.subscriber.process_transcript",
            new=AsyncMock(),
        ) as mock_process:
            await on_transcript_message(body)

        mock_process.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_missing_consultation_id(self) -> None:
        """Should return early when consultation_id is absent from the payload."""
        body = _make_body(consultation_id=None)

        with patch(
            "src.messaging.subscriber.process_transcript",
            new=AsyncMock(),
        ) as mock_process:
            await on_transcript_message(body)

        mock_process.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_invalid_uuid_consultation_id(self) -> None:
        """Should return early when consultation_id is not a valid UUID."""
        body = _make_body(consultation_id="not-a-uuid")

        with patch(
            "src.messaging.subscriber.process_transcript",
            new=AsyncMock(),
        ) as mock_process:
            await on_transcript_message(body)

        mock_process.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_on_ai_processing_failure(self) -> None:
        """Should not publish when process_transcript raises RuntimeError."""
        body = _make_body()
        mock_mgr = _mock_messaging_manager()

        with (
            patch(
                "src.messaging.subscriber.process_transcript",
                new=AsyncMock(side_effect=RuntimeError("Ollama down")),
            ),
            patch("src.messaging.subscriber.messaging_manager", mock_mgr),
        ):
            await on_transcript_message(body)

        mock_mgr.get_pubsub.return_value.publish.assert_not_awaited()


class TestOnTranscriptMessageHappyPath:
    """Tests for valid inputs — callback should process and publish."""

    @pytest.mark.asyncio
    async def test_calls_process_transcript_with_correct_transcript(self) -> None:
        """Should call process_transcript with the transcript from the message."""
        body = _make_body()
        mock_mgr = _mock_messaging_manager()

        with (
            patch(
                "src.messaging.subscriber.process_transcript",
                new=AsyncMock(return_value=_AI_RESULT),
            ) as mock_process,
            patch("src.messaging.subscriber.messaging_manager", mock_mgr),
        ):
            await on_transcript_message(body)

        mock_process.assert_awaited_once_with(_VALID_TRANSCRIPT)

    @pytest.mark.asyncio
    async def test_publishes_ai_completed_message(self) -> None:
        """Should publish an AICompletedMessage after successful processing."""
        body = _make_body()
        mock_mgr = _mock_messaging_manager()

        with (
            patch(
                "src.messaging.subscriber.process_transcript",
                new=AsyncMock(return_value=_AI_RESULT),
            ),
            patch("src.messaging.subscriber.messaging_manager", mock_mgr),
        ):
            await on_transcript_message(body)

        mock_mgr.get_pubsub.return_value.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_published_message_contains_correct_fields(self) -> None:
        """Published AICompletedMessage should carry summary, prescription, alerts."""
        body = _make_body()
        mock_mgr = _mock_messaging_manager()

        with (
            patch(
                "src.messaging.subscriber.process_transcript",
                new=AsyncMock(return_value=_AI_RESULT),
            ),
            patch("src.messaging.subscriber.messaging_manager", mock_mgr),
        ):
            await on_transcript_message(body)

        published_msg = mock_mgr.get_pubsub.return_value.publish.call_args.args[0]
        assert published_msg.summary == _AI_RESULT["summary"]
        assert published_msg.prescription == _AI_RESULT["prescription"]
        assert published_msg.clinical_alerts == _AI_RESULT["clinical_alerts"]
        assert published_msg.filename == _VALID_FILENAME
        assert published_msg.consultation_id == uuid.UUID(_VALID_CONSULTATION_ID)

    @pytest.mark.asyncio
    async def test_published_message_clinical_alerts_defaults_to_empty(self) -> None:
        """Should default clinical_alerts to [] when not present in result."""
        body = _make_body()
        mock_mgr = _mock_messaging_manager()
        result_without_alerts = {
            "summary": "Summary.",
            "prescription": {"medication_name": "Aspirin"},
        }

        with (
            patch(
                "src.messaging.subscriber.process_transcript",
                new=AsyncMock(return_value=result_without_alerts),
            ),
            patch("src.messaging.subscriber.messaging_manager", mock_mgr),
        ):
            await on_transcript_message(body)

        published_msg = mock_mgr.get_pubsub.return_value.publish.call_args.args[0]
        assert published_msg.clinical_alerts == []

    @pytest.mark.asyncio
    async def test_handles_publish_failure_gracefully(self) -> None:
        """Should not raise when publishing the AICompletedMessage fails."""
        body = _make_body()
        mock_mgr = _mock_messaging_manager()
        mock_mgr.get_pubsub.return_value.publish.side_effect = RuntimeError(
            "RabbitMQ unavailable"
        )

        with (
            patch(
                "src.messaging.subscriber.process_transcript",
                new=AsyncMock(return_value=_AI_RESULT),
            ),
            patch("src.messaging.subscriber.messaging_manager", mock_mgr),
        ):
            await on_transcript_message(body)  # should not raise

    @pytest.mark.asyncio
    async def test_uses_unknown_filename_when_not_in_payload(self) -> None:
        """Should default filename to 'unknown' when absent from message."""
        payload = {
            "transcript": _VALID_TRANSCRIPT,
            "consultation_id": _VALID_CONSULTATION_ID,
        }
        body = json.dumps(payload).encode()
        mock_mgr = _mock_messaging_manager()

        with (
            patch(
                "src.messaging.subscriber.process_transcript",
                new=AsyncMock(return_value=_AI_RESULT),
            ),
            patch("src.messaging.subscriber.messaging_manager", mock_mgr),
        ):
            await on_transcript_message(body)

        published_msg = mock_mgr.get_pubsub.return_value.publish.call_args.args[0]
        assert published_msg.filename == "unknown"
