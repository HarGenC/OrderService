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


class Item(BaseModel):
    id: str
    name: str
    price: Decimal


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
