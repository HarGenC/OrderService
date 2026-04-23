from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Order, OrderStatusEnum
from app.infrastructure.db_schema import OrderRow
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
        order_obj = OrderRow(
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
        stmt = select(OrderRow).where(OrderRow.id == order_id)

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
            select(OrderRow).where(OrderRow.idempotency_key == idempotency_key)
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
        stmt = select(OrderRow).where(OrderRow.id == order_id).with_for_update()

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
