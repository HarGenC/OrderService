from uuid import UUID
from loguru import logger
from pydantic import BaseModel

from app.core.models import Order, OrderStatusEnum
from app.infrastructure.catalog_service_client import CatalogServiceClient
from app.infrastructure.repositories import OrderRepository
from app.infrastructure.unit_of_work import UnitOfWork


class OrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: UUID
    idempotency_key: UUID


class CreateOrderUseCase:
    def __init__(
        self, unit_of_work: UnitOfWork, catalog_service_client: CatalogServiceClient
    ):
        self._unit_of_work = unit_of_work
        self._catalog_service_client = catalog_service_client

    async def __call__(self, order: OrderDTO) -> Order:
        available_qty = await self._get_available_qty(order.item_id)
        if order.quantity > available_qty:
            raise ValueError(
                f"Requested quantity {order.quantity} exceeds available quantity {available_qty}"
            )

        async with self._unit_of_work() as uow:
            try:
                order_result = await uow.orders.create(
                    order=OrderRepository.CreateDTO(
                        user_id=order.user_id,
                        quantity=order.quantity,
                        item_id=order.item_id,
                        status=OrderStatusEnum.NEW,
                        idempotency_key=order.idempotency_key,
                    )
                )
                await uow.commit()
            except Exception as e:
                logger.error(f"Error during order creation: {e}")
                raise
            return order_result

    async def _get_available_qty(self, item_id: UUID) -> int:
        item = await self._catalog_service_client.get_item(item_id)
        return item.available_qty
