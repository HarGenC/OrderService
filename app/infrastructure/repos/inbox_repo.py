from datetime import datetime, timezone
from typing import List
from uuid import UUID


from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    InboxEvent,
    InboxEventStatus,
)
from app.infrastructure.db_schema import Inbox
from app.infrastructure.exceptions import DuplicateEventError


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
