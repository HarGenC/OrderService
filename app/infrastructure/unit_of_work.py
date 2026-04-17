from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.repositories import (
    InboxRepository,
    OrderRepository,
    OutboxRepository,
    PaymentRepository,
)


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def __call__(self):
        async with self._session_factory() as session:
            try:
                yield _UnitOfWorkImplementation(session)
                await session.rollback()
            except:
                await session.rollback()
                raise


class _UnitOfWorkImplementation:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._order_repo = None
        self._payment_repo = None
        self._outbox_repo = None
        self._inbox_repo = None

    @property
    def orders(self):
        if self._order_repo is None:
            self._order_repo = OrderRepository(self._session)
        return self._order_repo

    @property
    def payments(self):
        if self._payment_repo is None:
            self._payment_repo = PaymentRepository(self._session)
        return self._payment_repo

    @property
    def outbox(self):
        if self._outbox_repo is None:
            self._outbox_repo = OutboxRepository(self._session)
        return self._outbox_repo

    @property
    def inbox(self):
        if self._inbox_repo is None:
            self._inbox_repo = InboxRepository(self._session)
        return self._inbox_repo

    async def commit(self):
        await self._session.commit()
