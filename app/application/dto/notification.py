from uuid import UUID

from pydantic import BaseModel


class CreateNotificationDTO(BaseModel):
    message: str
    reference_id: UUID
    idempotency_key: str
