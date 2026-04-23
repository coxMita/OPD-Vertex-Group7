"""DTO for email events consumed from the message queue."""

from pydantic import BaseModel


class EmailEvent(BaseModel):
    """Payload for an email job (queue or test publish endpoint)."""

    to_email: str
    subject: str
    message: str
    is_html: bool = False
    document_title: str | None = None
    document_content: dict | str | None = None
