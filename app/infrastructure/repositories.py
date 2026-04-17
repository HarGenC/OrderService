from datetime import datetime, timezone
from typing import List
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    CreateOutboxEventDTO,
    InboxEvent,
    InboxEventStatus,
    Order,
    OrderStatusEnum,
    OutboxEvent,
    OutboxEventStatus,
    PaymentDTO,
)
from app.infrastructure.db_schema import Inbox, Orders_tbl, Outbox, Payments_tbl
from app.infrastructure.exceptions import DuplicateEventError, NotFound


class OrderRepository:
    class CreateDTO(BaseModel):
        user_id: str
        quantity: int
        item_id: UUID
        status: OrderStatusEnum
        idempotency_key: str

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, order: CreateDTO, order_id: UUID | None = None) -> Order:
        order_obj = Orders_tbl(
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            idempotency_key=order.idempotency_key,
        )
        if order_id is not None:
            order_obj.id = order_id

        self._session.add(order_obj)
        await self._session.flush()
        return Order(
            id=order_obj.id,
            user_id=order_obj.user_id,
            quantity=order_obj.quantity,
            item_id=order_obj.item_id,
            status=order_obj.status,
            created_at=order_obj.created_at,
            updated_at=order_obj.updated_at,
        )

    async def get_by_id(self, order_id: UUID) -> Order:
        stmt = select(Orders_tbl).where(Orders_tbl.id == order_id)

        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise NotFound(f"Order with id {order_id} not found")

        return Order(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def get_by_idempotency_key(self, idempotency_key: UUID):
        result = await self._session.execute(
            select(Orders_tbl).where(Orders_tbl.idempotency_key == idempotency_key)
        )
        order = result.scalar_one_or_none()

        if order is None:
            return None

        return Order(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def update(self, order_id: UUID, status: OrderStatusEnum) -> Order:
        stmt = select(Orders_tbl).where(Orders_tbl.id == order_id).with_for_update()

        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise NotFound(f"Order with id {order_id} not found")

        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

        return Order(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, payment_data: PaymentDTO) -> PaymentDTO:
        payment = Payments_tbl(
            id=payment_data.id,
            user_id=payment_data.user_id,
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            status=payment_data.status,
            idempotency_key=payment_data.idempotency_key,
            created_at=payment_data.created_at,
        )

        self._session.add(payment)
        await self._session.flush()
        return payment

    async def get_by_id(self, payment_id: UUID) -> PaymentDTO:
        stmt = select(Payments_tbl).where(Payments_tbl.id == payment_id)

        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment is None:
            raise NotFound(f"Payment with id {payment_id} not found")

        return PaymentDTO(
            id=payment.id,
            user_id=payment.user_id,
            order_id=payment.order_id,
            amount=payment.amount,
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            created_at=payment.created_at,
        )

    async def update(self, payment_id: UUID, status: str, error_msg: str):
        stmt = (
            select(Payments_tbl).where(Payments_tbl.id == payment_id).with_for_update()
        )

        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment is None:
            raise NotFound(f"Payment with id {payment_id} not found")

        payment.status = status
        payment.error_msg = error_msg
        await self._session.flush()

        return payment


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, outbox: CreateOutboxEventDTO) -> OutboxEvent:
        outbox_event = Outbox(
            event_type=outbox.event_type,
            payload=outbox.payload,
        )

        self._session.add(outbox_event)
        await self._session.flush()
        return outbox_event

    async def claim_events(self, limit: int) -> List[OutboxEvent]:
        result = await self._session.execute(
            select(Outbox)
            .where(
                Outbox.status == OutboxEventStatus.PENDING,
                Outbox.retry_count < 5,
                or_(Outbox.next_retry_at.is_(None), Outbox.next_retry_at <= func.now()),
            )
            .order_by(Outbox.created_at)
            .limit(limit)
        )
        events = result.scalars().all()
        return [
            OutboxEvent(
                id=event.id,
                event_type=event.event_type,
                payload=event.payload,
                status=event.status,
                created_at=event.created_at,
                idempotency_key=event.idempotency_key,
                retry_count=event.retry_count,
                next_retry_at=event.next_retry_at,
            )
            for event in events
        ]

    async def update_retry_count(
        self, id: UUID, retry_count: int, next_retry_at: datetime | None
    ) -> OutboxEvent:
        result = await self._session.execute(select(Outbox).where(Outbox.id == id))
        outbox_item = result.scalar_one_or_none()

        if outbox_item is None:
            raise ValueError("Event not found")

        outbox_item.retry_count = retry_count
        outbox_item.next_retry_at = next_retry_at

        await self._session.flush()
        return outbox_item

    async def mark_as_sent(self, id: UUID):
        result = await self._session.execute(select(Outbox).where(Outbox.id == id))
        outbox_item = result.scalar_one_or_none()

        if outbox_item is None:
            raise ValueError("Event not found")

        outbox_item.status = OutboxEventStatus.SENT
        await self._session.flush()


class InboxRepository:
    class CreateDTO(BaseModel):
        order_id: str
        event_type: str
        payload: dict

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: CreateDTO) -> InboxEvent:
        stmt = (
            insert(Inbox)
            .values(
                order_id=event.order_id,
                event_type=event.event_type,
                payload=event.payload,
            )
            .on_conflict_do_nothing(index_elements=["order_id"])
            .returning(Inbox)
        )
        result = await self._session.execute(stmt)

        row = result.scalar_one_or_none()

        if row is None:
            raise DuplicateEventError(f"Event {event.order_id} already processed")

        await self._session.flush()

        return InboxEvent(
            id=row.id,
            order_id=row.order_id,
            status=row.status,
            event_type=row.event_type,
            payload=row.payload,
            created_at=row.created_at,
            processed_at=row.processed_at,
        )

    async def claim_events(self, limit: int) -> List[InboxEvent]:
        result = await self._session.execute(
            select(Inbox)
            .where(
                Inbox.status == InboxEventStatus.PENDING,
            )
            .order_by(Inbox.created_at)
            .limit(limit)
        )
        events = result.scalars().all()
        return [
            InboxEvent(
                id=event.id,
                order_id=event.order_id,
                event_type=event.event_type,
                payload=event.payload,
                status=event.status,
                created_at=event.created_at,
                processed_at=event.processed_at,
            )
            for event in events
        ]

    async def mark_as_processed(self, id: UUID):
        result = await self._session.execute(select(Inbox).where(Inbox.id == id))
        inbox_item = result.scalar_one_or_none()

        if inbox_item is None:
            raise ValueError("Event not found")

        inbox_item.status = InboxEventStatus.PROCESSED
        inbox_item.processed_at = datetime.now(timezone.utc)
        await self._session.flush()
