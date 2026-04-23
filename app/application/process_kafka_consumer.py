from app.application.dto.inbox import CreateInboxDTO
from app.application.interfaces.kafka_consumer import IKafkaConsumer
from app.application.interfaces.uow import IUnitOfWork
from app.core.models import EventTypeEnum
from loguru import logger


class ProcessKafkaConsumerUseCase:
    def __init__(self, unit_of_work: IUnitOfWork, kafka_consumer: IKafkaConsumer):
        self.uow = unit_of_work
        self._kafka_consumer = kafka_consumer

    async def __call__(self):
        await self._kafka_consumer.run(self.process)

    async def process(self, event: dict) -> bool:
        if event.get("event_type") not in (
            EventTypeEnum.ORDER_SHIPPED,
            EventTypeEnum.ORDER_CANCELLED,
        ):
            return False
        async with self.uow as uow:
            payload = {}
            for _key, _value in event.items():
                if _key in ("order_id", "event_type"):
                    continue
                payload[_key] = _value

            if not event.get("order_id"):
                logger.warning("Received event with missing order_id, skipping")
                return False

            await uow.inbox.create(
                CreateInboxDTO(
                    order_id=event.get("order_id"),
                    event_type=event["event_type"],
                    payload=payload,
                )
            )
            await uow.commit()
            logger.info("Order with id {} committed", event.get("order_id"))
            return True
