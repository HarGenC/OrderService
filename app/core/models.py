from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID
from pydantic import BaseModel


class OrderStatusEnum(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OutboxEventStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"


class InboxEventStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"


class EventTypeEnum(StrEnum):
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_SHIPPED = "order.shipped"
    ORDER_CANCELLED = "order.cancelled"


class Order(BaseModel):
    id: UUID
    user_id: str
    quantity: int
    item_id: UUID
    status: OrderStatusEnum
    created_at: datetime
    updated_at: datetime


class CatalogItem(BaseModel):
    id: UUID
    name: str
    price: Decimal
    available_qty: int
    created_at: datetime


class Item(BaseModel):
    id: UUID
    name: str
    price: Decimal
    available_qty: int
    created_at: datetime


class RequestPaymentDTO(BaseModel):
    order_id: str
    amount: str
    callback_url: str
    idempotency_key: str


class PaymentDTO(BaseModel):
    id: UUID
    user_id: UUID
    order_id: UUID
    amount: Decimal
    status: str
    idempotency_key: str
    created_at: datetime


class RequestCallback(BaseModel):
    payment_id: UUID
    order_id: UUID
    status: str
    amount: Decimal
    error_message: str | None


class CreateOutboxEventDTO(BaseModel):
    event_type: EventTypeEnum
    payload: dict


class OutboxEvent(BaseModel):
    id: UUID
    event_type: EventTypeEnum
    payload: dict
    status: OutboxEventStatus
    created_at: datetime
    idempotency_key: UUID
    retry_count: int
    next_retry_at: datetime | None


class InboxEvent(BaseModel):
    id: UUID
    order_id: UUID
    event_type: EventTypeEnum
    payload: dict
    status: InboxEventStatus
    created_at: datetime
    processed_at: datetime | None


class NotificationDTO(BaseModel):
    id: UUID
    message: str
    reference_id: UUID
    idempotency_key: str
    status: str
    created_at: datetime
    sent_at: datetime | None
    retry_count: int
    next_retry_at: datetime | None


class ResponseNotificationDTO(BaseModel):
    id: UUID
    user_id: UUID
    message: str
    reference_id: UUID
    created_at: datetime
