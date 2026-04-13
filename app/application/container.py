from dependency_injector import containers, providers

from app.application.create_order import CreateOrderUseCase
from app.application.get_order import GetOrderUseCase
from app.infrastructure.catalog_service_client import CatalogServiceClient
from app.infrastructure.container import InfrastructureContainer


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

    create_order_use_case = providers.Singleton[CreateOrderUseCase](
        CreateOrderUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        catalog_service_client=catalog_service_client,
    )

    get_order_use_case = providers.Singleton[GetOrderUseCase](
        GetOrderUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
    )
