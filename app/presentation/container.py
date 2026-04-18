from dependency_injector import containers, providers

from app.application.container import ApplicationContainer
from app.presentation.inbox_worker import InboxWorker
from app.presentation.kafka_consumer_worker import KafkaConsumerWorker
from app.presentation.notification_worker import NotificationWorker
from app.presentation.outbox_worker import OutboxWorker


class PresentationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    application = providers.Container[ApplicationContainer](
        ApplicationContainer,
        config=config,
    )
    outbox_worker = providers.Singleton[OutboxWorker](
        OutboxWorker, use_case=application.process_outbox_events_use_case
    )

    kafka_consumer_worker = providers.Singleton[KafkaConsumerWorker](
        KafkaConsumerWorker, use_case=application.process_kafka_consumer
    )

    inbox_worker = providers.Singleton[InboxWorker](
        InboxWorker, use_case=application.process_inbox_events_use_case
    )

    notification_worker = providers.Singleton[NotificationWorker](
        NotificationWorker, use_case=application.process_notification_use_case
    )
