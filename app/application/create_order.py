from uuid import UUID
from loguru import logger
from pydantic import BaseModel

from app.application.dto.notification import CreateNotificationDTO
from app.application.dto.order import CreateOrderDTO
from app.application.dto.outbox import CreateOutboxDTO
from app.application.dto.payment import CreatePaymentDTO
from app.application.dto.payment_client import CreateRequestPaymentDTO
from app.application.exceptions import InsufficientQuantity
from app.application.interfaces.uow import IUnitOfWork
from app.core.models import (
    EventTypeEnum,
    PaymentDTO,
    Item,
    Order,
    OrderStatusEnum,
)
from app.application.interfaces.catalog_client import ICatalogServiceClient
from app.application.interfaces.payments import IPaymentsService


class OrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: UUID
    idempotency_key: str


class CreateOrderUseCase:
    def __init__(
        self,
        unit_of_work: IUnitOfWork,
        catalog_service_client: ICatalogServiceClient,
        payments_service_client: IPaymentsService,
        service_name: str,
        namespace: str,
    ):
        self._unit_of_work = unit_of_work
        self._catalog_service_client = catalog_service_client
        self._payments_service_client = payments_service_client
        self._service_name = service_name
        self._namespace = namespace

    async def __call__(self, order: OrderDTO) -> Order:
        result = await self._check_idempotency_key(order)
        if result is not None:
            return result

        item = await self._get_item(order.item_id)
        if order.quantity > item.available_qty:
            raise InsufficientQuantity(
                f"Requested quantity {order.quantity} exceeds available quantity {item.available_qty}"
            )

        result_order = await self._create_order(order)

        try:
            payment = await self._create_payment_in_external_service(result_order, item)
            await self._record_payment(payment, result_order)
        except Exception as e:
            logger.error("Error during payment creation in external service: {}", e)
            return await self._cancel_order_on_payment_failure(result_order.id)

        return result_order

    async def _record_payment(self, payment: PaymentDTO, result_order: Order) -> None:
        async with self._unit_of_work as uow:
            try:
                await uow.payments.create(
                    CreatePaymentDTO(
                        id=payment.id,
                        user_id=payment.user_id,
                        order_id=payment.order_id,
                        amount=payment.amount,
                        status=payment.status,
                        idempotency_key=payment.idempotency_key,
                        created_at=payment.created_at,
                    )
                )

                await uow.commit()
                logger.info(
                    "Payment with id {} created successfully for order id {}",
                    payment.id,
                    result_order.id,
                )
            except Exception as e:
                logger.error("Error during payment creation: {}", e)

                raise

    async def _cancel_order_on_payment_failure(self, order_id: UUID) -> Order:
        logger.warning("Cancelling order due to payment service error")
        async with self._unit_of_work as uow:
            try:
                result_order = await uow.orders.update(
                    order_id=order_id, status=OrderStatusEnum.CANCELLED
                )
                await uow.outbox.create(
                    CreateOutboxDTO(
                        event_type=EventTypeEnum.ORDER_CANCELLED,
                        payload={
                            "order_id": str(result_order.id),
                            "user_id": result_order.user_id,
                            "item_id": str(result_order.item_id),
                            "quantity": result_order.quantity,
                        },
                    )
                )

                await uow.notification.create(
                    CreateNotificationDTO(
                        message="CANCELLED: Ваш заказ отменен. Причина: ошибка при обработке платежа",
                        reference_id=result_order.id,
                        idempotency_key=str(f"{result_order.id}:CANCELLED"),
                    )
                )
                await uow.commit()
                logger.info(
                    "Order with id {} cancelled successfully due to payment service error",
                    result_order.id,
                )
                return result_order
            except Exception as e:
                logger.error("Error during order cancelation: {}", e)
                raise

    async def _create_payment_in_external_service(
        self, order: Order, item: Item
    ) -> PaymentDTO:
        callback_url = f"http://{self._service_name}.{self._namespace}.svc:8000/api/orders/payment-callback"
        payment = await self._payments_service_client.create_payment(
            CreateRequestPaymentDTO(
                order_id=str(order.id),
                amount=str(item.price * order.quantity),
                callback_url=callback_url,
                idempotency_key=str(order.id),
            )
        )
        logger.info(
            "Payment with id {} created in external service successfully for order id {}",
            payment.id,
            order.id,
        )
        return payment

    async def _check_idempotency_key(self, order: OrderDTO) -> None | Order:
        async with self._unit_of_work as uow:
            try:
                order_result = await uow.orders.get_by_idempotency_key(
                    order.idempotency_key
                )
                if order_result is not None:
                    logger.info(
                        "Order with idempotency_key {} already exists.",
                        order.idempotency_key,
                    )
                    if (
                        order_result.user_id != order.user_id
                        or order_result.quantity != order.quantity
                        or order_result.item_id != order.item_id
                    ):
                        logger.warning(
                            "Order with idempotency_key {} has different data than the current request.",
                            order.idempotency_key,
                        )
                        raise Exception(
                            "Order with the same idempotency_key but different data already exists."
                        )
                    return order_result

            except Exception as e:
                logger.error("Error during order getting with idempotency_key: {}", e)
                raise

    async def _create_order(self, order: OrderDTO) -> Order:
        async with self._unit_of_work as uow:
            try:
                result_order = await uow.orders.create(
                    CreateOrderDTO(
                        user_id=order.user_id,
                        quantity=order.quantity,
                        item_id=order.item_id,
                        status=OrderStatusEnum.NEW,
                        idempotency_key=order.idempotency_key,
                    )
                )
                await uow.outbox.create(
                    CreateOutboxDTO(
                        event_type=EventTypeEnum.ORDER_CREATED,
                        payload={
                            "order_id": str(result_order.id),
                            "user_id": result_order.user_id,
                            "item_id": str(result_order.item_id),
                            "quantity": result_order.quantity,
                        },
                    )
                )
                await uow.notification.create(
                    CreateNotificationDTO(
                        message="NEW: Ваш заказ создан и ожидает оплаты",
                        reference_id=result_order.id,
                        idempotency_key=str(f"{result_order.id}:NEW"),
                    )
                )
                await uow.commit()
                logger.info("Order with id {} created successfully", result_order.id)
            except Exception as e:
                logger.error("Error during order creation: {}", e)
                raise

            return result_order

    async def _get_item(self, item_id: UUID) -> Item:
        item = await self._catalog_service_client.get_item(item_id)
        return item
