"""RabbitMQ subscriber callbacks for ai-service."""

import json
import logging

from src.ai.service import process_transcript

logger = logging.getLogger(__name__)


async def on_transcript_message(body: bytes) -> None:
    """Handle a raw TranscriptMessage payload from the transcription.completed exchange.

    Deserialises the JSON body, extracts the transcript text, and kicks off
    both AI inference passes (summary + prescription extraction).

    Args:
        body: Raw bytes of the incoming AMQP message.

    """
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        logger.error("Received non-JSON message body; skipping.")
        return

    transcript: str = payload.get("transcript", "")
    filename: str = payload.get("filename", "unknown")

    if not transcript:
        logger.warning(
            "Empty transcript in message from file '%s'; skipping.", filename
        )
        return

    logger.info(
        "Processing transcript from file '%s' (%d chars).", filename, len(transcript)
    )

    try:
        result = await process_transcript(transcript)
        logger.info(
            "AI processing complete for '%s'. Summary length: %d chars.",
            filename,
            len(result["summary"]),
        )
        logger.info("Summary: %s", result["summary"])
        logger.info("Prescription: %s", result["prescription"])
    except RuntimeError:
        logger.exception("AI processing failed for file '%s'.", filename)
