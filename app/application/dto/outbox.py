from pydantic import BaseModel

from app.core.models import EventTypeEnum


class CreateOutboxDTO(BaseModel):
    event_type: EventTypeEnum
    payload: dict
