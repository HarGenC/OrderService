from typing import Protocol
from uuid import UUID

from app.core.models import CatalogItem


class ICatalogServiceClient(Protocol):
    async def get_item(self, item_id: UUID) -> CatalogItem: ...
