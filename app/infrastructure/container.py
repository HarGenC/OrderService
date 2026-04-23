from typing import Callable

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.infrastructure.kafka_consumer import KafkaConsumer
from app.infrastructure.repos.repositories import (
    InboxRepository,
    NotificationRepository,
    OrderRepository,
    OutboxRepository,
    PaymentRepository,
)
from app.infrastructure.unit_of_work import UnitOfWork
from app.infrastructure.kafka_producer import KafkaProducer


class InfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    async_engine = providers.Singleton[AsyncEngine](
        create_async_engine,
        config.db.dsn,
        pool_size=config.db.pool_size,
        pool_recycle=config.db.pool_recycle,
        future=True,
    )

    session_factory: Callable[..., AsyncEngine] = providers.Factory(
        async_sessionmaker, async_engine, expire_on_commit=False, class_=AsyncSession
    )

    order_repo_factory = providers.Factory(OrderRepository)
    payment_repo_factory = providers.Factory(PaymentRepository)
    outbox_repo_factory = providers.Factory(OutboxRepository)
    inbox_repo_factory = providers.Factory(InboxRepository)
    notification_repo_factory = providers.Factory(NotificationRepository)

    unit_of_work = providers.Factory[UnitOfWork](
        UnitOfWork,
        session_factory=session_factory,
        order_repo_factory=order_repo_factory.provider,
        payment_repo_factory=payment_repo_factory.provider,
        outbox_repo_factory=outbox_repo_factory.provider,
        inbox_repo_factory=inbox_repo_factory.provider,
        notification_repo_factory=notification_repo_factory.provider,
    )

    kafka_producer = providers.Singleton[KafkaProducer](
        KafkaProducer,
        bootstrap_servers=config.kafka.producer.bootstrap_servers,
        topic=config.kafka.producer.topic,
    )

    kafka_consumer = providers.Singleton[KafkaConsumer](
        KafkaConsumer,
        bootstrap_servers=config.kafka.consumer.bootstrap_servers,
        kafka_group_id=config.kafka.consumer.group_id,
        topic=config.kafka.consumer.topic,
    )
