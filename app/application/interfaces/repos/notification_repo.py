from datetime import datetime
from typing import List, Protocol
from uuid import UUID

from app.application.dto.notification import CreateNotificationDTO
from app.core.models import NotificationDTO


class INotificationRepository(Protocol):
    async def create(self, event: CreateNotificationDTO) -> NotificationDTO: ...

    async def claim_notifications(self, limit: int) -> List[NotificationDTO]: ...

    async def update_retry_count(
        self, id: UUID, retry_count: int, next_retry_at: datetime | None
    ) -> NotificationDTO: ...

    async def mark_as_sent(self, id: UUID): ...
