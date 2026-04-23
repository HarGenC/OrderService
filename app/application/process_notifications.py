from datetime import datetime, timedelta, timezone

from loguru import logger

from app.application.dto.notification_client import CreateRequestDTO
from app.application.interfaces.notification_client import INotificationClient
from app.application.interfaces.uow import IUnitOfWork


class ProcessNotificationUseCase:
    def __init__(
        self,
        unit_of_work: IUnitOfWork,
        notification_client: INotificationClient,
        batch_size: int = 10,
        backoff: int = 2,
    ):
        self._unit_of_work = unit_of_work
        self._batch_size = batch_size
        self._notification_client = notification_client
        self._backoff = backoff

    async def __call__(self):
        async with self._unit_of_work as uow:
            notifications = await uow.notification.claim_notifications(self._batch_size)
            if not notifications:
                return

            for notification in notifications:
                try:
                    await self._notification_client.send_notification(
                        CreateRequestDTO(
                            message=notification.message,
                            reference_id=str(notification.reference_id),
                            idempotency_key=str(notification.idempotency_key),
                        )
                    )
                    logger.info(
                        "Notification {} with order id: {}. Sent successfully with message: {}",
                        notification.id,
                        notification.reference_id,
                        notification.message,
                    )
                    await uow.notification.mark_as_sent(notification.id)
                    await uow.commit()
                except Exception as e:
                    await uow.notification.update_retry_count(
                        id=notification.id,
                        retry_count=notification.retry_count + 1,
                        next_retry_at=datetime.now(timezone.utc)
                        + timedelta(minutes=self._backoff**notification.retry_count),
                    )
                    await uow.commit()
                    logger.info(
                        "Error sending notification {}: {}",
                        notification.reference_id,
                        e,
                    )
