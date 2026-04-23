from datetime import datetime
from typing import List, Protocol
from uuid import UUID

from app.application.dto.outbox import CreateOutboxDTO
from app.core.models import OutboxEvent


class IOutboxRepository(Protocol):
    async def create(self, outbox: CreateOutboxDTO) -> OutboxEvent: ...

    async def claim_events(self, limit: int) -> List[OutboxEvent]: ...

    async def update_retry_count(
        self, id: UUID, retry_count: int, next_retry_at: datetime | None
    ) -> OutboxEvent: ...

    async def mark_as_sent(self, id: UUID): ...
