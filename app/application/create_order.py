from uuid import UUID
from loguru import logger
from pydantic import BaseModel

from app.application.exceptions import InsufficientQuantity
from app.core.models import (
    CreateOutboxEventDTO,
    EventTypeEnum,
    PaymentDTO,
    Item,
    Order,
    OrderStatusEnum,
    RequestPaymentDTO,
)
from app.infrastructure.catalog_service_client import CatalogServiceClient
from app.infrastructure.payments_service_client import PaymentsServiceClient
from app.infrastructure.repositories import OrderRepository
from app.infrastructure.unit_of_work import UnitOfWork


class OrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: UUID
    idempotency_key: str


class CreateOrderUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        catalog_service_client: CatalogServiceClient,
        payments_service_client: PaymentsServiceClient,
        service_name: str,
        namespace: str,
    ):
        self._unit_of_work = unit_of_work
        self._catalog_service_client = catalog_service_client
        self._payments_service_client = payments_service_client
        self._service_name = service_name
        self._namespace = namespace

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
                logger.error("Error during order getting with idempotency_key: {}", e)
                raise

        item = await self._get_item(order.item_id)
        if order.quantity > item.available_qty:
            raise InsufficientQuantity(
                f"Requested quantity {order.quantity} exceeds available quantity {item.available_qty}"
            )

        async with self._unit_of_work() as uow:
            try:
                result_order = await uow.orders.create(
                    order=OrderRepository.CreateDTO(
                        user_id=order.user_id,
                        quantity=order.quantity,
                        item_id=order.item_id,
                        status=OrderStatusEnum.NEW,
                        idempotency_key=order.idempotency_key,
                    )
                )
                await uow.outbox.create(
                    CreateOutboxEventDTO(
                        event_type=EventTypeEnum.ORDER_CREATED,
                        payload={
                            "order_id": str(result_order.id),
                            "user_id": result_order.user_id,
                            "item_id": str(result_order.item_id),
                            "quantity": result_order.quantity,
                        },
                    )
                )
                await uow.commit()
            except Exception as e:
                logger.error("Error during order creation: {}", e)
                raise

        try:
            callback_url = f"http://{self._service_name}.{self._namespace}.svc:8000/api/orders/payment-callback"
            logger.debug("callback_url is {}", callback_url)
            payment = await self._payments_service_client.create_payment(
                RequestPaymentDTO(
                    order_id=str(result_order.id),
                    amount=str(item.price * result_order.quantity),
                    callback_url=callback_url,
                    idempotency_key=str(result_order.id),
                )
            )
        except Exception as e:
            logger.warning(e)
            async with self._unit_of_work() as uow:
                try:
                    result_order = await uow.orders.update(
                        order_id=result_order.id, status=OrderStatusEnum.CANCELLED
                    )
                    await uow.outbox.create(
                        CreateOutboxEventDTO(
                            event_type=EventTypeEnum.ORDER_CANCELLED,
                            payload={
                                "order_id": str(result_order.id),
                                "user_id": result_order.user_id,
                                "item_id": str(result_order.item_id),
                                "quantity": result_order.quantity,
                            },
                        )
                    )
                    await uow.commit()
                    return result_order
                except Exception as e:
                    logger.error("Error during order cancelation: {}", e)
                    raise

        async with self._unit_of_work() as uow:
            try:
                await uow.payments.create(
                    PaymentDTO(
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
            except Exception as e:
                logger.error("Error during payment creation: {}", e)
                raise

        return result_order

    async def _get_item(self, item_id: UUID) -> Item:
        item = await self._catalog_service_client.get_item(item_id)
        return item
