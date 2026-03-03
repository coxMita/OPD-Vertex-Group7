"""Transcript message published after a successful audio transcription."""

from datetime import datetime, timezone

from src.models.msg.abstract_message import AbstractMessage


class TranscriptMessage(AbstractMessage):
    """Message published when an audio file has been transcribed.

    Attributes:
        filename (str): Original name of the uploaded audio file.
        transcript (str): The full transcription text.
        language (str): Detected language code (e.g. "en").
        language_probability (float): Confidence score for the detected language.
        transcribed_at (datetime): UTC timestamp of when transcription completed.

    """

    filename: str
    transcript: str
    language: str
    language_probability: float
    transcribed_at: datetime = None

    def model_post_init(self, __context: object) -> None:
        """Set transcribed_at to current UTC time if not provided."""
        if self.transcribed_at is None:
            object.__setattr__(self, "transcribed_at", datetime.now(tz=timezone.utc))
