from pydantic import BaseModel
from typing import List
from datetime import datetime

class Message(BaseModel):
    message_id: str
    chatroom_id: str
    sender_uid: str
    content: str
    timestamp: str
    message_type: str = "text"

class Chatroom(BaseModel):
    chatroom_id: str
    participants: List[str]
    ad_id: str
    created_at: str
    last_message: str = ""
    last_message_time: str = ""
