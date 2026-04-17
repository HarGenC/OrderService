from aiokafka import AIOKafkaConsumer
import json
from loguru import logger
from typing import Callable

from app.infrastructure.exceptions import DuplicateEventError


class KafkaConsumer:
    def __init__(self, bootstrap_servers: str, kafka_group_id: str, topic: str):
        self._consumer: AIOKafkaConsumer | None = None
        self._bootstrap_servers = bootstrap_servers
        self._kafka_group_id = kafka_group_id
        self._topic = topic

    async def start(self):
        """Запуск consumer"""
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._kafka_group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
            enable_auto_commit=False,
        )
        await self._consumer.start()

    async def run(self, process: Callable):
        await self.start()

        try:
            async for message in self._consumer:
                if message.value is None:
                    continue

                event = message.value

                try:
                    is_processed = await process(event)
                    if is_processed:
                        print(
                            f"Order with id {event.get('order_id')} processed successfully"
                        )
                        await self._consumer.commit()

                except DuplicateEventError:
                    print(f"Order with id {event.get('order_id')} is a duplicate")
                    await self._consumer.commit()
                    continue
                except Exception as e:
                    logger.error("Error processing message: {}", e)
                    continue

        finally:
            await self._consumer.stop()
