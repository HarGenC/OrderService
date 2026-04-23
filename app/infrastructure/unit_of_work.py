from typing import Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Self

from app.application.interfaces.repos.inbox_repo import IInboxRepository
from app.application.interfaces.repos.notification_repo import INotificationRepository
from app.application.interfaces.repos.order_repo import IOrderRepository
from app.application.interfaces.repos.outbox_repo import IOutboxRepository
from app.application.interfaces.repos.payment_repo import IPaymentRepository

OrderRepoFactory = Callable[[AsyncSession], IOrderRepository]
PaymentRepoFactory = Callable[[AsyncSession], IPaymentRepository]
OutboxRepoFactory = Callable[[AsyncSession], IOutboxRepository]
InboxRepoFactory = Callable[[AsyncSession], IInboxRepository]
NotificationRepoFactory = Callable[[AsyncSession], INotificationRepository]


class UnitOfWork:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        order_repo_factory: OrderRepoFactory,
        payment_repo_factory: PaymentRepoFactory,
        outbox_repo_factory: OutboxRepoFactory,
        inbox_repo_factory: InboxRepoFactory,
        notification_repo_factory: NotificationRepoFactory,
    ) -> None:
        self._session_factory = session_factory
        self._order_repo_factory = order_repo_factory
        self._payment_repo_factory = payment_repo_factory
        self._outbox_repo_factory = outbox_repo_factory
        self._inbox_repo_factory = inbox_repo_factory
        self._notification_repo_factory = notification_repo_factory

        self._session: Optional[AsyncSession] = None

        self._order_repo = None
        self._payment_repo = None
        self._outbox_repo = None
        self._inbox_repo = None
        self._notification_repo = None

    def _ensure_session(self):
        if self._session is None:
            raise RuntimeError("UnitOfWork is not initialized. Use 'async with'.")

    @property
    def orders(self) -> IOrderRepository:
        self._ensure_session()
        if self._order_repo is None:
            self._order_repo = self._order_repo_factory(self._session)
        return self._order_repo

    @property
    def payments(self) -> IPaymentRepository:
        self._ensure_session()
        if self._payment_repo is None:
            self._payment_repo = self._payment_repo_factory(self._session)
        return self._payment_repo

    @property
    def outbox(self) -> IOutboxRepository:
        self._ensure_session()
        if self._outbox_repo is None:
            self._outbox_repo = self._outbox_repo_factory(self._session)
        return self._outbox_repo

    @property
    def inbox(self) -> IInboxRepository:
        self._ensure_session()
        if self._inbox_repo is None:
            self._inbox_repo = self._inbox_repo_factory(self._session)
        return self._inbox_repo

    @property
    def notification(self) -> INotificationRepository:
        self._ensure_session()
        if self._notification_repo is None:
            self._notification_repo = self._notification_repo_factory(self._session)
        return self._notification_repo

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()

        self._order_repo = None
        self._payment_repo = None
        self._outbox_repo = None
        self._inbox_repo = None
        self._notification_repo = None

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._session:
            return

        await self._session.rollback()
        await self._session.close()
        self._session = None

        if exc_type:
            raise exc_val

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
