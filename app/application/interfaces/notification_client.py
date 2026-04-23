from typing import Protocol


from app.application.dto.notification_client import CreateRequestDTO
from app.core.models import ResponseNotificationDTO


class INotificationClient(Protocol):
    async def send_notification(
        self, json: CreateRequestDTO
    ) -> ResponseNotificationDTO: ...
