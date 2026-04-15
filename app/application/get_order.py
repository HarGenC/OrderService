from uuid import UUID

from app.application.exceptions import OrderNotFound
from app.infrastructure.exceptions import NotFound
from app.infrastructure.unit_of_work import UnitOfWork


class GetOrderUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, order_id: UUID):
        async with self._unit_of_work() as uow:
            try:
                order = await uow.orders.get_by_id(order_id=order_id)
                return order
            except NotFound:
                raise OrderNotFound(f"Order with id {order_id} not found")
