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
                        message = "Ваш заказ отправлен в доставку"
                    else:
                        status = OrderStatusEnum.CANCELLED
                        message = f"Ваш заказ отменен. Причина: {event.payload.get('reason', 'неизвестная причина')}"
                    await uow.notification.create(
                        uow.notification.CreateDTO(
                            message=message, reference_id=event.order_id
                        )
                    )
                    await uow.orders.update(event.order_id, status)
                    await uow.inbox.mark_as_processed(event.id)
                    await uow.commit()
                    logger.info("Event {} processed successfully", event.id)
                except Exception as e:
                    logger.info("Error processing order {}: {}", event.order_id, e)
