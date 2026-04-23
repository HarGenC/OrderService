from pydantic import BaseModel


class CreateRequestPaymentDTO(BaseModel):
    order_id: str
    amount: str
    callback_url: str
    idempotency_key: str
