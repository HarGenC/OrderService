from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import PaymentDTO
from app.infrastructure.db_schema import PaymentRow
from app.infrastructure.exceptions import NotFound


class PaymentRepository:
    class CreateDTO(BaseModel):
        id: UUID
        user_id: UUID
        order_id: UUID
        amount: Decimal
        status: str
        idempotency_key: str
        created_at: datetime

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, payment_data: CreateDTO) -> PaymentDTO:
        payment = PaymentRow(
            id=payment_data.id,
            user_id=payment_data.user_id,
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            status=payment_data.status,
            idempotency_key=payment_data.idempotency_key,
            created_at=payment_data.created_at,
        )

        self._session.add(payment)
        await self._session.flush()
        return payment

    async def get_by_id(self, payment_id: UUID) -> PaymentDTO:
        stmt = select(PaymentRow).where(PaymentRow.id == payment_id)

        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment is None:
            raise NotFound(f"Payment with id {payment_id} not found")

        return PaymentDTO(
            id=payment.id,
            user_id=payment.user_id,
            order_id=payment.order_id,
            amount=payment.amount,
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            created_at=payment.created_at,
        )

    async def update(self, payment_id: UUID, status: str, error_msg: str):
        stmt = select(PaymentRow).where(PaymentRow.id == payment_id).with_for_update()

        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment is None:
            raise NotFound(f"Payment with id {payment_id} not found")

        payment.status = status
        payment.error_msg = error_msg
        await self._session.flush()

        return payment
