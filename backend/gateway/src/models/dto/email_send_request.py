"""Request body for queueing an email (matches email-service ``EmailEvent``)."""

from pydantic import BaseModel, Field


class EmailSendRequest(BaseModel):
    """Payload forwarded to email-service ``POST /api/send``."""

    to_email: str = Field(examples=["patient@example.com"])
    subject: str = Field(examples=["Appointment reminder"])
    message: str = Field(examples=["Your consultation is scheduled for tomorrow."])
    is_html: bool = False
    document_title: str | None = None
    document_content: dict | str | None = None


class EmailAcceptedResponse(BaseModel):
    """Response from email-service when the event is accepted onto the queue."""

    status: str
    message: str
