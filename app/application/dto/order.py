from uuid import UUID

from pydantic import BaseModel

from app.core.models import OrderStatusEnum


class CreateOrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: UUID
    status: OrderStatusEnum
    idempotency_key: str
