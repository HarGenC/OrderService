from app.application.dto.notification_client import CreateRequestDTO
from app.core.models import ResponseNotificationDTO
from app.infrastructure.base_client import BaseServiceClient


class NotificationClient(BaseServiceClient):
    async def send_notification(
        self, json: CreateRequestDTO
    ) -> ResponseNotificationDTO:
        response = await self.request_url(
            method="POST",
            url=f"{self.base_url}/api/notifications",
            json_data=json.model_dump(),
        )

        return ResponseNotificationDTO(
            id=response["id"],
            user_id=response["user_id"],
            message=response["message"],
            reference_id=response["reference_id"],
            created_at=response["created_at"],
        )
