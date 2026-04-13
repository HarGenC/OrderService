from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Order, OrderStatusEnum
from app.infrastructure.db_schema import Orders_tbl
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

    async def create(self, order: CreateDTO) -> Order:
        order_obj = Orders_tbl(
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            idempotency_key=order.idempotency_key,
        )
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
