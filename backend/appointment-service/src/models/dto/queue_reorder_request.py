"""DTO for reordering the appointment queue."""

from pydantic import BaseModel


class QueueReorderRequest(BaseModel):
    """Request DTO for reordering the queue.

    appointment_ids should be an ordered list of appointment IDs
    representing the desired queue order.
    """

    appointment_ids: list[int]