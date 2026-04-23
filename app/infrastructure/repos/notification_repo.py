from datetime import datetime, timezone
from typing import List
from uuid import UUID

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import NotificationDTO
from app.infrastructure.db_schema import Notification
from app.infrastructure.exceptions import DuplicateEventError


class NotificationRepository:
    class CreateDTO(BaseModel):
        message: str
        reference_id: UUID
        idempotency_key: str

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: CreateDTO) -> NotificationDTO:
        stmt = (
            insert(Notification)
            .values(
                message=event.message,
                reference_id=event.reference_id,
                idempotency_key=event.idempotency_key,
            )
            .on_conflict_do_nothing(index_elements=["idempotency_key"])
            .returning(Notification)
        )
        result = await self._session.execute(stmt)

        row = result.scalar_one_or_none()

        if row is None:
            raise DuplicateEventError(
                f"Notification for reference_id {event.reference_id} already exists"
            )

        await self._session.flush()

        logger.info(
            "Notification with reference_id {} created successfully with message: {} and wait commit",
            event.reference_id,
            event.message,
        )
        return NotificationDTO(
            id=row.id,
            message=row.message,
            reference_id=row.reference_id,
            idempotency_key=row.idempotency_key,
            status=row.status,
            sent_at=row.sent_at,
            created_at=row.created_at,
            retry_count=row.retry_count,
            next_retry_at=row.next_retry_at,
        )

    async def claim_notifications(self, limit: int) -> List[NotificationDTO]:
        result = await self._session.execute(
            select(Notification)
            .where(
                Notification.status == "PENDING",
            )
            .order_by(Notification.created_at)
            .limit(limit)
        )
        notifications = result.scalars().all()
        return [
            NotificationDTO(
                id=notification.id,
                message=notification.message,
                reference_id=notification.reference_id,
                idempotency_key=notification.idempotency_key,
                status=notification.status,
                created_at=notification.created_at,
                sent_at=notification.sent_at,
                retry_count=notification.retry_count,
                next_retry_at=notification.next_retry_at,
            )
            for notification in notifications
        ]

    async def update_retry_count(
        self, id: UUID, retry_count: int, next_retry_at: datetime | None
    ) -> NotificationDTO:
        result = await self._session.execute(
            select(Notification).where(Notification.id == id)
        )
        notification_item = result.scalar_one_or_none()

        if notification_item is None:
            raise ValueError("Notification not found")

        notification_item.retry_count = retry_count
        notification_item.next_retry_at = next_retry_at

        await self._session.flush()
        return notification_item

    async def mark_as_sent(self, id: UUID):
        result = await self._session.execute(
            select(Notification).where(Notification.id == id)
        )
        notification_item = result.scalar_one_or_none()

        if notification_item is None:
            raise ValueError("Notification not found")

        notification_item.status = "SENT"
        notification_item.sent_at = datetime.now(timezone.utc)
        await self._session.flush()
