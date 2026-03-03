from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SendNotification(BaseModel):
    channel: str  # email, whatsapp, web
    recipient: str
    message_body: str
    ticket_number: Optional[str] = None
    customer_name: Optional[str] = None


class NotificationLogEntry(BaseModel):
    id: str
    channel: str
    recipient: str
    message_body: str
    ticket_number: Optional[str] = None
    status: str
    timestamp: str
