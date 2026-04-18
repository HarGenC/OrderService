from dependency_injector import containers, providers

from app.application.process_inbox_events import ProcessInboxEventsUseCase
from app.application.process_kafka_consumer import ProcessKafkaConsumerUseCase
from app.application.create_order import CreateOrderUseCase
from app.application.get_order import GetOrderUseCase
from app.application.process_callback import CallbackProcessingUseCase
from app.application.process_notifications import ProcessNotificationUseCase
from app.application.process_outbox_events import ProcessOutboxEventsUseCase
from app.infrastructure.catalog_service_client import CatalogServiceClient
from app.infrastructure.container import InfrastructureContainer
from app.infrastructure.notification_client import NotificationClient
from app.infrastructure.payments_service_client import PaymentsServiceClient


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    infrastructure_container = providers.Container[InfrastructureContainer](
        InfrastructureContainer,
        config=config.infrastructure,
    )

    catalog_service_client = providers.Singleton[CatalogServiceClient](
        CatalogServiceClient,
        api_key=config.infrastructure.clients.catalog_service.api_key,
        base_url=config.infrastructure.clients.catalog_service.base_url,
    )

    payments_service_client = providers.Singleton[PaymentsServiceClient](
        PaymentsServiceClient,
        api_key=config.infrastructure.clients.payments_service.api_key,
        base_url=config.infrastructure.clients.payments_service.base_url,
    )

    notification_client = providers.Singleton[NotificationClient](
        NotificationClient,
        api_key=config.infrastructure.clients.payments_service.api_key,
        base_url=config.infrastructure.clients.payments_service.base_url,
    )

    create_order_use_case = providers.Singleton[CreateOrderUseCase](
        CreateOrderUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        catalog_service_client=catalog_service_client,
        payments_service_client=payments_service_client,
        service_name=config.infrastructure.hostname.service_name,
        namespace=config.infrastructure.hostname.namespace,
    )

    callback_processing_use_case = providers.Singleton[CallbackProcessingUseCase](
        CallbackProcessingUseCase, unit_of_work=infrastructure_container.unit_of_work
    )

    get_order_use_case = providers.Singleton[GetOrderUseCase](
        GetOrderUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
    )

    process_outbox_events_use_case = providers.Singleton[ProcessOutboxEventsUseCase](
        ProcessOutboxEventsUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        kafka_producer=infrastructure_container.kafka_producer,
    )

    process_kafka_consumer = providers.Singleton[ProcessKafkaConsumerUseCase](
        ProcessKafkaConsumerUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        kafka_consumer=infrastructure_container.kafka_consumer,
    )

    process_inbox_events_use_case = providers.Singleton[ProcessInboxEventsUseCase](
        ProcessInboxEventsUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
    )

    process_notification_use_case = providers.Singleton[ProcessNotificationUseCase](
        ProcessNotificationUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        notification_client=notification_client,
    )
