import logging
import os
from datetime import datetime

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

_model_cache: list[WhisperModel | None] = [None]


def get_model() -> WhisperModel:
    """Return the cached WhisperModel, loading it if necessary."""
    if _model_cache[0] is None:
        logger.info("Loading Whisper model (%s)...", MODEL_SIZE)
        _model_cache[0] = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded.")
    return _model_cache[0]  # type: ignore[return-value]


def transcribe_audio(
    audio_file: str,
    language: str = LANGUAGE,
) -> tuple[str, str, float]:
    """Transcribe an audio file using Faster-Whisper."""
    model = get_model()
    segments, info = model.transcribe(audio_file, beam_size=5, language=language)

    lang = info.language
    prob = info.language_probability
    logger.info("Detected language: %s (probability: %.2f)", lang, prob)

    full_transcript = ""
    for segment in segments:
        logger.debug("[%.2fs -> %.2fs] %s", segment.start, segment.end, segment.text)
        full_transcript += segment.text + " "

    return full_transcript.strip(), lang, prob


def save_transcript(transcript: str, filename: str = "transcript.txt") -> None:
    """Save the transcript to a text file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Transcript generated on: {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        f.write(transcript)
        f.write("\n")
    logger.info("Transcript saved to: %s", filename)
