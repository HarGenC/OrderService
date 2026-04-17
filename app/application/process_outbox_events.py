from datetime import datetime, timedelta, timezone
from loguru import logger

from app.infrastructure.kafka_producer import KafkaProducer
from app.infrastructure.unit_of_work import UnitOfWork


class ProcessOutboxEventsUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        kafka_producer: KafkaProducer,
        batch_size: int = 100,
        backoff: int = 2,
    ):
        self._unit_of_work = unit_of_work
        self._kafka_producer = kafka_producer
        self._batch_size = batch_size
        self._backoff = backoff

    async def __call__(self):
        async with self._unit_of_work() as uow:
            events = await uow.outbox.claim_events(self._batch_size)
            if not events:
                return

        async with self._kafka_producer as kp:
            for event in events:
                async with self._unit_of_work() as uow:
                    try:
                        await kp.send_message(
                            message={
                                "event_type": event.event_type,
                                **event.payload,
                                "idempotency_key": str(event.idempotency_key),
                            },
                            key=str(event.id),
                            topic="student_system-order.events",
                        )
                    except Exception as e:
                        logger.info(f"Error sending event {event.id} to Kafka: {e}")
                        await uow.outbox.update_retry_count(
                            id=event.id,
                            retry_count=event.retry_count + 1,
                            next_retry_at=datetime.now(timezone.utc)
                            + timedelta(minutes=self._backoff**event.retry_count),
                        )
                        await uow.commit()
                        continue

                    await uow.outbox.mark_as_sent(event.id)

                    await uow.commit()
                    logger.info(f"Event {event.id} sent to Kafka successfully")
