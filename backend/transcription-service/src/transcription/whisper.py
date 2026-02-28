from datetime import datetime

from faster_whisper import WhisperModel


def transcribe_audio(
    audio_file: str, model_size: str = "medium", language: str = "en"
) -> str:
    """Transcribe an audio file using Faster-Whisper."""
    print(f"Loading Whisper model ({model_size})...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(audio_file, beam_size=5, language=language)

    lang = info.language
    prob = info.language_probability
    print(f"Detected language: {lang} (probability: {prob:.2f})")

    full_transcript = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        full_transcript += segment.text + " "

    return full_transcript.strip()


def save_transcript(transcript: str, filename: str = "transcript.txt") -> None:
    """Save the transcript to a text file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Transcript generated on: {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        f.write(transcript)
        f.write("\n")
    print(f"Transcript saved to: {filename}")
