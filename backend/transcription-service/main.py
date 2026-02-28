from fastapi import FastAPI

from src.transcription.router import router

app = FastAPI(title="transcription-service")
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "transcription-service"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Local testing only — requires: uv run --group dev python main.py
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

    transcript = transcribe_audio(audio_path)
    print("\n" + "=" * 50 + "\nFULL TRANSCRIPT:\n" + "=" * 50)
    print(transcript)
    save_transcript(transcript, "transcript.txt")
