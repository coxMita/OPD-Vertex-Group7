"""Unit tests for src/transcription/whisper.py."""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from src.transcription.whisper import save_transcript, transcribe_audio


# ── transcribe_audio ──────────────────────────────────────────────────────────

class TestTranscribeAudio:
    """Tests for transcribe_audio()."""

    @patch("src.transcription.whisper.WhisperModel")
    def test_returns_joined_segments(self, mock_model_cls: MagicMock) -> None:
        """Segments are concatenated into a single transcript string."""
        seg1 = MagicMock(text="Hello", start=0.0, end=1.0)   # no leading space
        seg2 = MagicMock(text="world", start=1.0, end=2.0)   # no leading space

        mock_info = MagicMock(language="en", language_probability=0.99)
        mock_model_cls.return_value.transcribe.return_value = ([seg1, seg2], mock_info)

        result = transcribe_audio("fake.wav")

        assert result == "Hello world"

    @patch("src.transcription.whisper.WhisperModel")
    def test_empty_segments_returns_empty_string(self, mock_model_cls: MagicMock) -> None:
        """No segments produces an empty string."""
        mock_info = MagicMock(language="en", language_probability=0.99)
        mock_model_cls.return_value.transcribe.return_value = ([], mock_info)

        result = transcribe_audio("fake.wav")

        assert result == ""

    @patch("src.transcription.whisper.WhisperModel")
    def test_uses_correct_model_size(self, mock_model_cls: MagicMock) -> None:
        """WhisperModel is initialised with the requested model size."""
        mock_info = MagicMock(language="en", language_probability=0.99)
        mock_model_cls.return_value.transcribe.return_value = ([], mock_info)

        transcribe_audio("fake.wav", model_size="small")

        mock_model_cls.assert_called_once_with("small", device="cpu", compute_type="int8")

    @patch("src.transcription.whisper.WhisperModel")
    def test_passes_language_to_model(self, mock_model_cls: MagicMock) -> None:
        """The language parameter is forwarded to model.transcribe()."""
        mock_info = MagicMock(language="ro", language_probability=0.95)
        mock_model_cls.return_value.transcribe.return_value = ([], mock_info)

        transcribe_audio("fake.wav", language="ro")

        mock_model_cls.return_value.transcribe.assert_called_once_with(
            "fake.wav", beam_size=5, language="ro"
        )

    @patch("src.transcription.whisper.WhisperModel")
    def test_strips_whitespace(self, mock_model_cls: MagicMock) -> None:
        """Leading/trailing whitespace is stripped from the final transcript."""
        seg = MagicMock(text="  padded  ", start=0.0, end=1.0)
        mock_info = MagicMock(language="en", language_probability=0.99)
        mock_model_cls.return_value.transcribe.return_value = ([seg], mock_info)

        result = transcribe_audio("fake.wav")

        assert result == result.strip()


# ── save_transcript ───────────────────────────────────────────────────────────

class TestSaveTranscript:
    """Tests for save_transcript()."""

    def test_file_is_created(self, tmp_path: pytest.fixture) -> None:
        """A file is created at the given path."""
        out = tmp_path / "transcript.txt"
        save_transcript("Hello world", filename=str(out))
        assert out.exists()

    def test_transcript_content_in_file(self, tmp_path: pytest.fixture) -> None:
        """The transcript text appears in the saved file."""
        out = tmp_path / "transcript.txt"
        save_transcript("Hello world", filename=str(out))
        assert "Hello world" in out.read_text(encoding="utf-8")

    def test_timestamp_header_in_file(self, tmp_path: pytest.fixture) -> None:
        """The file contains a timestamp header."""
        out = tmp_path / "transcript.txt"
        save_transcript("Test", filename=str(out))
        content = out.read_text(encoding="utf-8")
        assert "Transcript generated on:" in content

    def test_overwrites_existing_file(self, tmp_path: pytest.fixture) -> None:
        """Calling save_transcript twice overwrites the previous content."""
        out = tmp_path / "transcript.txt"
        save_transcript("First", filename=str(out))
        save_transcript("Second", filename=str(out))
        content = out.read_text(encoding="utf-8")
        assert "Second" in content
        assert "First" not in content