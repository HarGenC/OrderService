import asyncio
import http
from typing import Set

import httpx


class AsyncRetry:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        backoff: float = 2.0,
        retryable_statuses: Set[http.HTTPStatus] | None = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff = backoff
        if retryable_statuses is None:
            self.retryable_statuses = {
                http.HTTPStatus.REQUEST_TIMEOUT,  # 408
                http.HTTPStatus.TOO_MANY_REQUESTS,  # 429
                http.HTTPStatus.INTERNAL_SERVER_ERROR,  # 500
                http.HTTPStatus.BAD_GATEWAY,  # 502
                http.HTTPStatus.SERVICE_UNAVAILABLE,  # 503
                http.HTTPStatus.GATEWAY_TIMEOUT,  # 504
            }
        else:
            self.retryable_statuses = retryable_statuses

    async def execute(self, func, *args, **kwargs):
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code not in self.retryable_statuses:
                    error_msg = (
                        f"HTTP error {exc.response.status_code}: {exc.response.text}"
                    )
                    raise ValueError(
                        f"External service returned error: {error_msg}"
                    ) from exc
                last_error = exc

            delay = self.base_delay * (self.backoff**attempt)
            await asyncio.sleep(delay)

        raise ValueError(
            f"Operation failed after {self.max_retries} attempts"
        ) from last_error
