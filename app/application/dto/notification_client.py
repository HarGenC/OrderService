from pydantic import BaseModel


class CreateRequestDTO(BaseModel):
    message: str
    reference_id: str
    idempotency_key: str
