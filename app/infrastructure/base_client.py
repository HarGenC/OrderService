import httpx
from loguru import logger

from app.infrastructure.async_retry import AsyncRetry


class BaseServiceClient:
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
