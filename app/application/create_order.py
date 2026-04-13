from uuid import UUID
from loguru import logger
from pydantic import BaseModel

from app.application.exceptions import InsufficientQuantity
from app.core.models import Order, OrderStatusEnum
from app.infrastructure.catalog_service_client import CatalogServiceClient
from app.infrastructure.repositories import OrderRepository
from app.infrastructure.unit_of_work import UnitOfWork


class OrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: UUID
    idempotency_key: str


class CreateOrderUseCase:
    def __init__(
        self, unit_of_work: UnitOfWork, catalog_service_client: CatalogServiceClient
    ):
        self._unit_of_work = unit_of_work
        self._catalog_service_client = catalog_service_client

    async def __call__(self, order: OrderDTO) -> Order:
        async with self._unit_of_work() as uow:
            try:
                order_result = await uow.orders.get_by_idempotency_key(
                    order.idempotency_key
                )
                if order_result is not None:
                    logger.info(
                        f"Order with idempotency_key {order.idempotency_key} already exists."
                    )
                    if (
                        order_result.user_id != order.user_id
                        or order_result.quantity != order.quantity
                        or order_result.item_id != order.item_id
                    ):
                        logger.warning(
                            f"Order with idempotency_key {order.idempotency_key} has different data than the current request."
                        )
                        raise Exception(
                            "Order with the same idempotency_key but different data already exists."
                        )
                    return order_result

            except Exception as e:
                logger.error(f"Error during order getting with idempotency_key: {e}")
                raise

        available_qty = await self._get_available_qty(order.item_id)
        if order.quantity > available_qty:
            raise InsufficientQuantity(
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
