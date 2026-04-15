from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Order, OrderStatusEnum, PaymentDTO
from app.infrastructure.db_schema import Orders_tbl, Payments_tbl
from app.infrastructure.exceptions import NotFound


class OrderRepository:
    class CreateDTO(BaseModel):
        user_id: str
        quantity: int
        item_id: UUID
        status: OrderStatusEnum
        idempotency_key: str

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, order: CreateDTO, order_id: UUID | None = None) -> Order:
        order_obj = Orders_tbl(
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            idempotency_key=order.idempotency_key,
        )
        if order_id is not None:
            order_obj.id = order_id

        self._session.add(order_obj)
        await self._session.flush()
        return Order(
            id=order_obj.id,
            user_id=order_obj.user_id,
            quantity=order_obj.quantity,
            item_id=order_obj.item_id,
            status=order_obj.status,
            created_at=order_obj.created_at,
            updated_at=order_obj.updated_at,
        )

    async def get_by_id(self, order_id: UUID) -> Order:
        stmt = select(Orders_tbl).where(Orders_tbl.id == order_id)

        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise NotFound(f"Order with id {order_id} not found")

        return Order(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def get_by_idempotency_key(self, idempotency_key: UUID):
        result = await self._session.execute(
            select(Orders_tbl).where(Orders_tbl.idempotency_key == idempotency_key)
        )
        order = result.scalar_one_or_none()

        if order is None:
            return None

        return Order(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def update(self, order_id: UUID, status: OrderStatusEnum) -> Order:
        stmt = select(Orders_tbl).where(Orders_tbl.id == order_id).with_for_update()

        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise NotFound(f"Order with id {order_id} not found")

        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

        return Order(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, payment_data: PaymentDTO) -> PaymentDTO:
        payment = Payments_tbl(
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
        stmt = select(Payments_tbl).where(Payments_tbl.id == payment_id)

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
        stmt = (
            select(Payments_tbl).where(Payments_tbl.id == payment_id).with_for_update()
        )

        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment is None:
            raise NotFound(f"Payment with id {payment_id} not found")

        payment.status = status
        payment.error_msg = error_msg
        await self._session.flush()

        return payment
