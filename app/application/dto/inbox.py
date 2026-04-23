from pydantic import BaseModel


class CreateInboxDTO(BaseModel):
    order_id: str
    event_type: str
    payload: dict
