"""Transcription router for transcription-service."""

import os
import tempfile
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import TRANSCRIPTION_COMPLETED
from src.models.msg.transcript_message import TranscriptMessage
from src.transcription.whisper import transcribe_audio

router = APIRouter(prefix="/transcription", tags=["transcription"])


@router.post("/")
async def transcribe(
    consultation_id: uuid.UUID,
    file: UploadFile = File(...),
) -> dict[str, str]:
    """Receive an audio file, return its transcript, and publish it to RabbitMQ.

    Args:
        consultation_id: UUID of the consultation this recording belongs to.
        file: The uploaded audio file to transcribe.

    Returns:
        dict with the transcript text.

    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        transcript, language, language_probability = transcribe_audio(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        os.unlink(tmp_path)

    message = TranscriptMessage(
        filename=file.filename or "unknown",
        transcript=transcript,
        language=language,
        language_probability=language_probability,
        consultation_id=consultation_id,
    )

    try:
        await messaging_manager.get_pubsub(TRANSCRIPTION_COMPLETED).publish(message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription succeeded but failed to publish message: {e}",
        ) from e

    return {"transcript": transcript}
