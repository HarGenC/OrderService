from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CreatePaymentDTO(BaseModel):
    id: UUID
    user_id: UUID
    order_id: UUID
    amount: Decimal
    status: str
    idempotency_key: str
    created_at: datetime
