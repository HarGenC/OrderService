from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import EventTypeEnum, OutboxEvent, OutboxEventStatus
from app.infrastructure.db_schema import Outbox


class OutboxRepository:
    class CreateDTO(BaseModel):
        event_type: EventTypeEnum
        payload: dict

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, outbox: CreateDTO) -> OutboxEvent:
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
