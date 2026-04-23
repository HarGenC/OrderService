from typing import Protocol

from app.application.dto.payment_client import CreateRequestPaymentDTO
from app.core.models import PaymentDTO


class IPaymentsService(Protocol):
    async def create_payment(
        self, create_payment_dto: CreateRequestPaymentDTO
    ) -> PaymentDTO: ...
