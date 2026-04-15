"""RabbitMQ subscriber callbacks for ai-service."""

import json
import logging
import uuid

from src.ai.service import process_transcript
from src.messaging.messaging_manager import messaging_manager
from src.messaging.pubsub_exchanges import AI_COMPLETED
from src.models.msg.ai_completed_message import AICompletedMessage

logger = logging.getLogger(__name__)


async def on_transcript_message(body: bytes) -> None:
    """Handle a raw TranscriptMessage payload from the transcription.completed exchange.

    Deserialises the JSON body, runs the full AI pipeline (summary + prescription
    extraction), then publishes an AICompletedMessage to the ai.completed exchange
    for downstream services to consume.

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
    consultation_id_raw: str | None = payload.get("consultation_id")

    if not transcript:
        logger.warning(
            "Empty transcript in message from file '%s'; skipping.", filename
        )
        return

    if not consultation_id_raw:
        logger.warning(
            "Missing consultation_id in message from file '%s'; skipping.", filename
        )
        return

    try:
        consultation_id = uuid.UUID(consultation_id_raw)
    except ValueError:
        logger.error(
            "Invalid consultation_id '%s' in message from file '%s'; skipping.",
            consultation_id_raw,
            filename,
        )
        return

    logger.info(
        "Processing transcript from file '%s' (%d chars) for consultation '%s'.",
        filename,
        len(transcript),
        consultation_id,
    )

    try:
        result = await process_transcript(transcript)
    except RuntimeError:
        logger.exception(
            "AI processing failed for file '%s'; message will not be published.",
            filename,
        )
        return

    logger.info(
        "AI processing complete for '%s'. Summary length: %d chars.",
        filename,
        len(result["summary"]),  # type: ignore[arg-type]
    )

    message = AICompletedMessage(
        filename=filename,
        summary=result["summary"],  # type: ignore[arg-type]
        prescription=result["prescription"],  # type: ignore[arg-type]
        consultation_id=consultation_id,
        clinical_alerts=result.get("clinical_alerts", []),
    )

    try:
        await messaging_manager.get_pubsub(AI_COMPLETED).publish(message)
        logger.info(
            "Published AICompletedMessage for file '%s' to '%s' (consultation: '%s').",
            filename,
            AI_COMPLETED,
            consultation_id,
        )
    except RuntimeError:
        logger.exception(
            "Failed to publish AICompletedMessage for file '%s'.", filename
        )
