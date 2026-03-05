"""FastAPI router for the AI service."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.ai.service import process_transcript

router = APIRouter(prefix="/ai", tags=["ai"])


class PromptRequest(BaseModel):
    """Request body for the manual prompt endpoint."""

    transcript: str = Field(
        ...,
        min_length=1,
        description="Consultation transcript text to process.",
        examples=["Patient presents with a 3-day history of fever and sore throat."],
    )


class AIResponse(BaseModel):
    """Response returned by the AI processing pipeline."""

    summary: str = Field(..., description="Clinical summary of the consultation.")
    prescription: dict[str, object] = Field(
        ..., description="Extracted prescription data as structured JSON."
    )


@router.post("/prompt", response_model=AIResponse)
async def run_prompt(body: PromptRequest) -> AIResponse:
    """Manually trigger the AI pipeline with a transcript string.

    Useful for local testing without RabbitMQ. Runs both the summary
    and prescription extraction passes and returns the results.

    Args:
        body: Request body containing the transcript.

    Returns:
        AIResponse with summary and prescription fields.

    Raises:
        HTTPException: If the Ollama inference call fails.

    """
    try:
        result = await process_transcript(body.transcript)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AIResponse(
        summary=result["summary"],
        prescription=result["prescription"],  # type: ignore[arg-type]
    )
