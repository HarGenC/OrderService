from app.application.dto.payment_client import CreateRequestPaymentDTO
from app.core.models import PaymentDTO
from app.infrastructure.base_client import BaseServiceClient


class PaymentsServiceClient(BaseServiceClient):
    async def create_payment(
        self, create_payment_dto: CreateRequestPaymentDTO
    ) -> PaymentDTO:
        result = await self.request_url(
            method="POST",
            url=f"{self.base_url}/api/payments",
            json_data=create_payment_dto.model_dump(),
        )
        payment = PaymentDTO(**result)
        return payment
