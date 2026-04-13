from app.core.models import CatalogItem
import httpx
from decimal import Decimal
from loguru import logger

from app.infrastructure.async_retry import AsyncRetry


class CatalogServiceClient:
    def __init__(
        self, api_key: str, base_url: str, async_retry: AsyncRetry | None = None
    ):
        self._client = httpx.AsyncClient(
            follow_redirects=True, timeout=10.0, headers={"x-api-key": api_key}
        )
        self.base_url = base_url
        if async_retry is None:
            self.async_retry = AsyncRetry()
        else:
            self.async_retry = async_retry

    async def request_url(self, method: str, url: str, json_data: dict | None = None):
        async def request():
            response = await self._client.request(method, url, json=json_data)
            response.raise_for_status()
            return response.json()

        try:
            return await self.async_retry.execute(request)
        except httpx.ReadTimeout:
            logger.error("Timeout while requesting {}", url)
            raise
        except httpx.HTTPError as e:
            logger.error("HTTP error while requesting {} {}: {}", method, url, e)
            raise

        except Exception as e:
            logger.error("Unexpected error while requesting {} {}: {}", method, url, e)
            raise

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
