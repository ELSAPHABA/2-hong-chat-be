from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    sender_id: str
    message_text: str

class MessageResponse(BaseModel):
    id: str
    room_id: str
    sender_id: str
    message_text: str
    timestamp: datetime

    class Config:
        from_attributes = True
