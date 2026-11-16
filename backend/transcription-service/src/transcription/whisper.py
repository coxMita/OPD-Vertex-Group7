"""Faster-Whisper transcription — remote (UCloud GPU) or local (CPU).

If WHISPER_API_URL is set, audio is sent to the OpenAI-compatible
faster-whisper server on UCloud (behind nginx + Bearer token).
Otherwise the model is loaded locally on the CPU, as before.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import httpx
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

WHISPER_API_URL = os.getenv("WHISPER_API_URL", "").rstrip("/")
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY", "")
WHISPER_TIMEOUT = float(os.getenv("WHISPER_TIMEOUT", "900"))

_model_cache: list[WhisperModel | None] = [None]


def use_remote() -> bool:
    """Return True when a remote Whisper endpoint is configured."""
    return bool(WHISPER_API_URL)


def get_model() -> WhisperModel:
    """Return the cached local WhisperModel, loading it if necessary."""
    if _model_cache[0] is None:
        logger.info("Loading Whisper model (%s)...", MODEL_SIZE)
        _model_cache[0] = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded.")
    return _model_cache[0]  # type: ignore[return-value]


def _transcribe_remote(audio_file: str, language: str) -> tuple[str, str, float]:
    """Send the audio file to the remote faster-whisper server."""
    url = f"{WHISPER_API_URL}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {WHISPER_API_KEY}"} if WHISPER_API_KEY else {}
    data = {"response_format": "verbose_json"}
    if language:
        data["language"] = language

    logger.info("Sending audio to remote Whisper at %s...", WHISPER_API_URL)
    with Path(audio_file).open("rb") as f:
        response = httpx.post(
            url,
            headers=headers,
            data=data,
            files={"file": (Path(audio_file).name, f, "application/octet-stream")},
            timeout=WHISPER_TIMEOUT,
        )
    response.raise_for_status()
    body = response.json()
    lang = body.get("language") or language or "unknown"
    prob = float(body.get("language_probability", 1.0))
    logger.info("Remote transcription received (%d chars).", len(body["text"]))
    return body["text"].strip(), lang, prob


def transcribe_audio(
    audio_file: str,
    language: str = LANGUAGE,
) -> tuple[str, str, float]:
    """Transcribe an audio file using Faster-Whisper (remote or local)."""
    if use_remote():
        return _transcribe_remote(audio_file, language)

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
