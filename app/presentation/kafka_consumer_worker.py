import asyncio

from app.application.process_kafka_consumer import ProcessKafkaConsumerUseCase


class KafkaConsumerWorker:
    def __init__(self, use_case: ProcessKafkaConsumerUseCase):
        self._use_case = use_case

    async def run(self):
        while True:
            await self._use_case()
            await asyncio.sleep(0.5)
