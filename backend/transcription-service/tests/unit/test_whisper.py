"""Unit tests for src/transcription/whisper.py."""

from unittest.mock import MagicMock, patch

import pytest

import src.transcription.whisper as whisper_module
from src.transcription.whisper import get_model, save_transcript, transcribe_audio

EXPECTED_TUPLE_LENGTH = 3


@pytest.fixture(autouse=True)
def reset_model_cache() -> None:
    """Reset the cached model before every test."""
    whisper_module._model_cache[0] = None
    yield
    whisper_module._model_cache[0] = None


# ── get_model ─────────────────────────────────────────────────────────────────


class TestGetModel:
    """Tests for get_model()."""

    @patch("src.transcription.whisper.WhisperModel")
    def test_loads_model_on_first_call(self, mock_cls: MagicMock) -> None:
        """WhisperModel is instantiated on the first call."""
        get_model()
        mock_cls.assert_called_once()

    @patch("src.transcription.whisper.WhisperModel")
    def test_returns_same_instance_on_second_call(self, mock_cls: MagicMock) -> None:
        """WhisperModel is only instantiated once across multiple calls."""
        first = get_model()
        second = get_model()
        assert first is second
        mock_cls.assert_called_once()

    @patch("src.transcription.whisper.WhisperModel")
    def test_uses_env_model_size(self, mock_cls: MagicMock) -> None:
        """WhisperModel is initialised with MODEL_SIZE from the environment."""
        whisper_module.MODEL_SIZE = "small"
        get_model()
        mock_cls.assert_called_once_with("small", device="cpu", compute_type="int8")

    @patch("src.transcription.whisper.WhisperModel")
    def test_returns_whisper_model_instance(self, mock_cls: MagicMock) -> None:
        """get_model() returns the WhisperModel instance."""
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = get_model()
        assert result is mock_instance


# ── transcribe_audio ──────────────────────────────────────────────────────────


class TestTranscribeAudio:
    """Tests for transcribe_audio()."""

    def _make_model_mock(
        self,
        mock_cls: MagicMock,
        segments: list,
        language: str = "en",
        probability: float = 0.99,
    ) -> MagicMock:
        mock_info = MagicMock(language=language, language_probability=probability)
        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = (segments, mock_info)
        mock_cls.return_value = mock_instance
        return mock_instance

    @patch("src.transcription.whisper.WhisperModel")
    def test_returns_tuple_of_three(self, mock_cls: MagicMock) -> None:
        """transcribe_audio returns a (str, str, float) tuple."""
        self._make_model_mock(mock_cls, [])
        result = transcribe_audio("fake.wav")
        assert isinstance(result, tuple)
        assert len(result) == EXPECTED_TUPLE_LENGTH

    @patch("src.transcription.whisper.WhisperModel")
    def test_returns_joined_segments(self, mock_cls: MagicMock) -> None:
        """Segments are concatenated into a single transcript string."""
        seg1 = MagicMock(text="Hello", start=0.0, end=1.0)
        seg2 = MagicMock(text="world", start=1.0, end=2.0)
        self._make_model_mock(mock_cls, [seg1, seg2])
        transcript, _, _ = transcribe_audio("fake.wav")
        assert transcript == "Hello world"

    @patch("src.transcription.whisper.WhisperModel")
    def test_empty_segments_returns_empty_string(self, mock_cls: MagicMock) -> None:
        """No segments produces an empty transcript string."""
        self._make_model_mock(mock_cls, [])
        transcript, _, _ = transcribe_audio("fake.wav")
        assert transcript == ""

    @patch("src.transcription.whisper.WhisperModel")
    def test_returns_language_from_model(self, mock_cls: MagicMock) -> None:
        """Detected language is returned from model info."""
        self._make_model_mock(mock_cls, [], language="ro", probability=0.95)
        _, lang, _ = transcribe_audio("fake.wav")
        assert lang == "ro"

    @patch("src.transcription.whisper.WhisperModel")
    def test_returns_language_probability(self, mock_cls: MagicMock) -> None:
        """Language probability is returned from model info."""
        self._make_model_mock(mock_cls, [], language="en", probability=0.87)
        _, _, prob = transcribe_audio("fake.wav")
        assert prob == pytest.approx(0.87)

    @patch("src.transcription.whisper.WhisperModel")
    def test_passes_language_to_model(self, mock_cls: MagicMock) -> None:
        """The language parameter is forwarded to model.transcribe()."""
        mock_instance = self._make_model_mock(mock_cls, [], language="ro")
        transcribe_audio("fake.wav", language="ro")
        mock_instance.transcribe.assert_called_once_with(
            "fake.wav", beam_size=5, language="ro"
        )

    @patch("src.transcription.whisper.WhisperModel")
    def test_strips_trailing_whitespace(self, mock_cls: MagicMock) -> None:
        """Leading/trailing whitespace is stripped from the final transcript."""
        seg = MagicMock(text="  padded  ", start=0.0, end=1.0)
        self._make_model_mock(mock_cls, [seg])
        transcript, _, _ = transcribe_audio("fake.wav")
        assert transcript == transcript.strip()

    @patch("src.transcription.whisper.WhisperModel")
    def test_reuses_cached_model(self, mock_cls: MagicMock) -> None:
        """Two calls to transcribe_audio do not load the model twice."""
        self._make_model_mock(mock_cls, [])
        transcribe_audio("fake.wav")
        transcribe_audio("fake.wav")
        mock_cls.assert_called_once()


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
        """The file contains a 'Transcript generated on:' header."""
        out = tmp_path / "transcript.txt"
        save_transcript("Test", filename=str(out))
        assert "Transcript generated on:" in out.read_text(encoding="utf-8")

    def test_separator_line_in_file(self, tmp_path: pytest.fixture) -> None:
        """The file contains the separator line of equals signs."""
        out = tmp_path / "transcript.txt"
        save_transcript("Test", filename=str(out))
        assert "=" * 50 in out.read_text(encoding="utf-8")

    def test_overwrites_existing_file(self, tmp_path: pytest.fixture) -> None:
        """Calling save_transcript twice overwrites previous content."""
        out = tmp_path / "transcript.txt"
        save_transcript("First", filename=str(out))
        save_transcript("Second", filename=str(out))
        content = out.read_text(encoding="utf-8")
        assert "Second" in content
        assert "First" not in content

    def test_empty_transcript(self, tmp_path: pytest.fixture) -> None:
        """Empty transcript string is written without error."""
        out = tmp_path / "transcript.txt"
        save_transcript("", filename=str(out))
        assert out.exists()
