"""Minimal OpenAI-compatible faster-whisper server for the OPD-Vertex UCloud job.

Exposes:
    POST /v1/audio/transcriptions   (multipart: file, [language], [response_format])
    GET  /v1/models
    GET  /health

It listens on 127.0.0.1 only; nginx in front of it handles the Bearer token.
"""

import logging
import os
import tempfile
import threading
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
import av
from faster_whisper import WhisperModel

# Newer PyAV (>=15) removed the `metadata_errors` argument that faster-whisper
# still passes to av.open() -> drop it so audio decoding works with any version.
_av_open = av.open


def _av_open_compat(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
    kwargs.pop("metadata_errors", None)
    return _av_open(*args, **kwargs)


av.open = _av_open_compat

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("whisper-server")

MODEL_SIZE = os.getenv("WHISPER_MODEL", "large-v3")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
VAD_FILTER = os.getenv("WHISPER_VAD", "true").lower() == "true"

logger.info(
    "Loading faster-whisper '%s' on %s (%s)...", MODEL_SIZE, DEVICE, COMPUTE_TYPE
)
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
logger.info("Model loaded.")
_lock = threading.Lock()  # one transcription at a time on the small GPU slice

app = FastAPI(title="opd-whisper")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok", "model": MODEL_SIZE}


@app.get("/v1/models")
def models() -> dict:
    """List the single served model (OpenAI format)."""
    return {"object": "list", "data": [{"id": MODEL_SIZE, "object": "model"}]}


@app.post("/v1/audio/transcriptions", response_model=None)
def transcribe(
    file: UploadFile = File(...),
    model_name: str | None = Form(None, alias="model"),  # accepted, ignored
    language: str | None = Form(None),
    response_format: str = Form("json"),
) -> dict | PlainTextResponse:
    """Transcribe an uploaded audio file."""
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        with _lock:
            segments, info = model.transcribe(
                tmp_path,
                beam_size=BEAM_SIZE,
                language=language or None,  # empty -> auto-detect
                vad_filter=VAD_FILTER,
            )
            segs = list(segments)  # transcription actually runs here
    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        os.unlink(tmp_path)

    text = " ".join(s.text.strip() for s in segs).strip()
    logger.info(
        "Transcribed %.1fs of audio, lang=%s (%.2f), %d chars",
        info.duration,
        info.language,
        info.language_probability,
        len(text),
    )

    if response_format == "text":
        return PlainTextResponse(text)
    if response_format == "verbose_json":
        return {
            "task": "transcribe",
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": [
                {"id": i, "start": s.start, "end": s.end, "text": s.text}
                for i, s in enumerate(segs)
            ],
        }
    return {"text": text}
