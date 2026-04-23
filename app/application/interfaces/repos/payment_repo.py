from typing import Protocol
from uuid import UUID

from app.application.dto.payment import CreatePaymentDTO
from app.core.models import PaymentDTO


class IPaymentRepository(Protocol):
    async def create(self, payment_data: CreatePaymentDTO) -> PaymentDTO: ...

    async def get_by_id(self, payment_id: UUID) -> PaymentDTO: ...

    async def update(self, payment_id: UUID, status: str, error_msg: str): ...
