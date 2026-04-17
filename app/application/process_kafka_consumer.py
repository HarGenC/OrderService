from app.infrastructure.kafka_consumer import KafkaConsumer
from app.infrastructure.unit_of_work import UnitOfWork
from app.core.models import EventTypeEnum


class ProcessKafkaConsumerUseCase:
    def __init__(self, unit_of_work: UnitOfWork, kafka_consumer: KafkaConsumer):
        self.uow = unit_of_work
        self._kafka_consumer = kafka_consumer

    async def __call__(self):
        await self._kafka_consumer.run(self.process)

    async def process(self, event: dict) -> bool:
        print(f"Received event: {event}")
        print(event.get("event_type"))
        if event.get("event_type") not in (
            EventTypeEnum.ORDER_SHIPPED,
            EventTypeEnum.ORDER_CANCELLED,
        ):
            print(f"Skipping event with type {event.get('event_type')}")
            return False
        async with self.uow() as uow:
            payload = {}
            for _key, _value in event.items():
                print(f"Ключ:{_key}, значение: {_value} ")
                if _key in ("order_id", "event_type"):
                    print("Скипаем")
                    continue
                payload[_key] = _value

            print(f"Processing order with id {event.get('order_id')}")
            await uow.inbox.create(
                uow.inbox.CreateDTO(
                    order_id=event.get("order_id"),
                    event_type=event["event_type"],
                    payload=payload,
                )
            )
            print(f"Order with id {event.get('order_id')} saved to inbox")
            await uow.commit()
            print(f"Order with id {event.get('order_id')} committed")
            return True
