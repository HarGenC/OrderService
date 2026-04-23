from typing import List, Protocol
from uuid import UUID

from app.application.dto.inbox import CreateInboxDTO
from app.core.models import InboxEvent


class IInboxRepository(Protocol):
    async def create(self, event: CreateInboxDTO) -> InboxEvent: ...

    async def claim_events(self, limit: int) -> List[InboxEvent]: ...

    async def mark_as_processed(self, id: UUID): ...
