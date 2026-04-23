from typing import Callable, Protocol


class IKafkaConsumer(Protocol):
    async def start(self): ...

    async def run(self, process: Callable): ...
