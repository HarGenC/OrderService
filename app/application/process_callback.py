from loguru import logger

from app.application.dto.notification import CreateNotificationDTO
from app.application.dto.outbox import CreateOutboxDTO
from app.application.exceptions import PaymentNotFound
from app.application.interfaces.uow import IUnitOfWork
from app.core.models import (
    EventTypeEnum,
    OrderStatusEnum,
    RequestCallback,
)
from app.infrastructure.exceptions import NotFound


class CallbackProcessingUseCase:
    def __init__(self, unit_of_work: IUnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, request_callback: RequestCallback):
        async with self._unit_of_work as uow:
            try:
                payment = await uow.payments.get_by_id(request_callback.payment_id)
                if payment.status != "pending":
                    return
                await uow.payments.update(
                    request_callback.payment_id,
                    request_callback.status,
                    request_callback.error_message,
                )
                if request_callback.status == "failed":
                    order_status = OrderStatusEnum.CANCELLED
                    event_type = EventTypeEnum.ORDER_CANCELLED
                    message = f"CANCELLED: Ваш заказ отменен. Причина:{request_callback.error_message}"
                else:
                    order_status = OrderStatusEnum.PAID
                    event_type = EventTypeEnum.ORDER_PAID
                    message = "PAID: Ваш заказ успешно оплачен и готов к отправке"

                order = await uow.orders.update(request_callback.order_id, order_status)
                await uow.outbox.create(
                    CreateOutboxDTO(
                        event_type=event_type,
                        payload={
                            "order_id": str(order.id),
                            "item_id": str(order.item_id),
                            "quantity": order.quantity,
                        },
                    )
                )
                await uow.notification.create(
                    CreateNotificationDTO(
                        message=message,
                        reference_id=order.id,
                        idempotency_key=f"{order.id}:{str(order_status)}",
                    )
                )
                await uow.commit()
                logger.info(
                    "Order with id {} updated to status {} and event {} created",
                    order.id,
                    order_status,
                    event_type,
                )
            except NotFound:
                raise PaymentNotFound(
                    f"Payment with id {request_callback.payment_id} not found"
                )
