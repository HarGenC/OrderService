from app.core.models import CatalogItem
from decimal import Decimal

from app.infrastructure.base_client import BaseServiceClient


class CatalogServiceClient(BaseServiceClient):
    async def get_item(self, item_id) -> CatalogItem:
        result = await self.request_url(
            method="GET", url=f"{self.base_url}/api/catalog/items/{item_id}"
        )

        return CatalogItem(
            id=result["id"],
            name=result["name"],
            price=Decimal(str(result["price"])),
            available_qty=result["available_qty"],
            created_at=result["created_at"],
        )
