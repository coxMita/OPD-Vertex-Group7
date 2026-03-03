import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI

from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import TRANSCRIPTION_COMPLETED
from src.messaging.pubsub_facade import PubSubFacade
from src.transcription.router import router
from src.transcription.whisper import get_model

logger = logging.getLogger(__name__)

load_dotenv()
AMQP_URL = os.getenv("AMQP_URL")
if not AMQP_URL:
    logger.error("AMQP_URL is not set. Please set it in the environment variables.")
    raise ValueError("AMQP_URL is not set.")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """Manage application startup and shutdown lifecycle."""
    messaging_manager.add_pubsub(PubSubFacade(AMQP_URL, TRANSCRIPTION_COMPLETED))

    logger.info("Starting up messaging manager...")
    await messaging_manager.start_all()
    logger.info("Messaging manager started.")

    logger.info("Pre-loading Whisper model...")
    await asyncio.to_thread(get_model)  # runs blocking load off the event loop
    logger.info("Whisper model ready.")

    yield

    logger.info("Shutting down messaging manager...")
    await messaging_manager.stop_all()
    logger.info("Messaging manager shut down.")


app = FastAPI(title="transcription-service", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "transcription-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}

    # Local testing only — requires: uv run --group dev python main.py
    # swagger ui uv run fastapi dev main.py


if __name__ == "__main__":
    import sounddevice as sd  # noqa: PLC0415
    import soundfile as sf  # noqa: PLC0415

    from src.transcription.whisper import (  # noqa: PLC0415
        save_transcript,
        transcribe_audio,
    )

    RATE = 16000
    DURATION = 30

    print(f"Recording for {DURATION} seconds... Speak now!")
    audio = sd.rec(int(DURATION * RATE), samplerate=RATE, channels=1, dtype="int16")
    sd.wait()
    print("Recording finished!")

    audio_path = "test_audio.wav"
    sf.write(audio_path, audio, RATE)

    transcript, lang, prob = transcribe_audio(audio_path)
    print("\n" + "=" * 50 + "\nFULL TRANSCRIPT:\n" + "=" * 50)
    print(transcript)
    save_transcript(transcript, "transcript.txt")
