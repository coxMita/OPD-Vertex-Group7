import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.transcription.whisper import transcribe_audio

router = APIRouter(prefix="/transcription", tags=["transcription"])


@router.post("/")
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    """Receive an audio file and return its transcript."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        transcript = transcribe_audio(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        os.unlink(tmp_path)

    return {"transcript": transcript}
