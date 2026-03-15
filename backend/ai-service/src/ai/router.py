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
        examples=[
            "Patient presents with a 3-day fever and sore throat. "
            "Doctor diagnoses bacterial tonsillitis and prescribes "
            "Amoxicillin 500mg three times daily for 7 days."
        ],
    )


class AIResponse(BaseModel):
    """Response returned by the AI processing pipeline."""

    summary: str = Field(..., description="Clinical summary of the consultation.")
    prescription: dict[str, object] = Field(
        ..., description="Extracted prescription data as structured JSON."
    )


@router.post(
    "/prompt",
    response_model=AIResponse,
    summary="Process a transcript through the RAG-augmented AI pipeline",
    description=(
        "Embeds the transcript, retrieves similar past consultations from pgvector, "
        "injects them as context, then runs clinical summary and prescription "
        "extraction via llama3.2:3b. Each call also stores the transcript embedding "
        "for future RAG lookups."
    ),
)
async def run_prompt(body: PromptRequest) -> AIResponse:
    """Manually trigger the RAG AI pipeline with a transcript string.

    Args:
        body: Request body containing the transcript.

    Returns:
        AIResponse with summary and prescription fields.

    Raises:
        HTTPException: If Ollama inference or pgvector operations fail.

    """
    try:
        result = await process_transcript(body.transcript)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AIResponse(
        summary=result["summary"],
        prescription=result["prescription"],  # type: ignore[arg-type]
    )
