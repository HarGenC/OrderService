from typing import Protocol
from types import TracebackType
from typing import Type
from typing import Self

from app.application.interfaces.repos.inbox_repo import IInboxRepository
from app.application.interfaces.repos.notification_repo import INotificationRepository
from app.application.interfaces.repos.order_repo import IOrderRepository
from app.application.interfaces.repos.outbox_repo import IOutboxRepository
from app.application.interfaces.repos.payment_repo import IPaymentRepository


class IUnitOfWork(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self): ...
    async def rollback(self): ...

    @property
    def orders(self) -> IOrderRepository: ...

    @property
    def payments(self) -> IPaymentRepository: ...

    @property
    def outbox(self) -> IOutboxRepository: ...

    @property
    def inbox(self) -> IInboxRepository: ...

    @property
    def notification(self) -> INotificationRepository: ...
