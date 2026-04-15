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
