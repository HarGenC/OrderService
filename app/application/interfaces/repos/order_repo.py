from typing import Protocol
from uuid import UUID

from app.application.dto.order import CreateOrderDTO
from app.core.models import Order, OrderStatusEnum


class IOrderRepository(Protocol):
    async def create(
        self, order: CreateOrderDTO, order_id: UUID | None = None
    ) -> Order: ...

    async def get_by_id(self, order_id: UUID) -> Order: ...

    async def get_by_idempotency_key(self, idempotency_key: UUID) -> Order | None: ...

    async def update(self, order_id: UUID, status: OrderStatusEnum) -> Order: ...
