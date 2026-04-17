from loguru import logger

from app.core.models import EventTypeEnum, OrderStatusEnum
from app.infrastructure.unit_of_work import UnitOfWork


class ProcessInboxEventsUseCase:
    def __init__(self, unit_of_work: UnitOfWork, batch_size: int = 10):
        self._unit_of_work = unit_of_work
        self._batch_size = batch_size

    async def __call__(self):
        async with self._unit_of_work() as uow:
            events = await uow.inbox.claim_events(self._batch_size)
            if not events:
                return
            for event in events:
                try:
                    if event.event_type == EventTypeEnum.ORDER_SHIPPED:
                        status = OrderStatusEnum.SHIPPED
                    else:
                        status = OrderStatusEnum.CANCELLED
                    await uow.orders.update(event.order_id, status)
                    await uow.inbox.mark_as_processed(event.id)
                    await uow.commit()
                    logger.info(f"Event {event.id} processed successfully")
                except Exception as e:
                    print(f"Error processing order {event.order_id}: {e}")
