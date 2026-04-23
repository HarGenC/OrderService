from typing import Any, Protocol, Self


class IKafkaProducer(Protocol):
    async def start(self): ...

    async def stop(self): ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def send_message(
        self,
        message: dict[str, Any],
        key: str | None = None,
        topic: str | None = None,
    ) -> None: ...
